#!/usr/bin/env python3
"""
Excel Merged JSON Review Processor - Multi-Model Version
Used to perform AI review on each point in the final_merged_json column of Excel files
Supports separate reviews for multiple model answers, generating multi-column results
Supports optional review models
"""
import os
import pandas as pd
import json
import asyncio
import time
import argparse
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import yaml
from judge_engine import judge_one, vote
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
def load_config():
    """
    Load configuration file
    Returns:
        dict: Configuration dictionary containing processing parameters, request control and retry settings
    Note:
        - If config.yaml file does not exist, default configuration will be used
        - Configuration includes batch size, concurrency count, delay time, retry count and other parameters
    """
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Default configuration - using new simplified configuration structure
        return {
            'processing': {
                'batch_size': 2,
                'concurrent_models': 3,
                'concurrent_items': 1
            },
            'request_control': {
                'base_delay': 0.1,
                'batch_delay': 1,
                'item_delay': 0
            },
            'retry': {
                'max_retries': 4,
                'retry_multiplier': 2,
                'rate_limit_wait': 15.0
            }
        }
CONFIG = load_config()
class MultiModelMergedJsonJudge:
    """
    Multi-Model JSON Review Processor
    Main Functions:
    1. Read questions, scoring criteria and multiple model answers from Excel files
    2. Use specified review models to judge each scoring point
    3. Support concurrent processing to improve efficiency
    4. Generate new Excel files containing review results
    Usage:
    judge = MultiModelMergedJsonJudge(
        judge_models=['m1', 'm2'],  # Specify review models
        answer_columns=['gpt_answer', 'claude_answer']  # Specify model answer columns to review
    )
    await judge.process_excel_file('input.xlsx', 'output.xlsx')
    """
    def __init__(self, batch_size: int = None, request_delay: float = 2.0, judge_models: List[str] = None,
                 answer_columns: List[str] = None, question_col: str = 'question', rubric_col: str = 'rubrics'):
        """
        Initialize reviewer
        Args:
            batch_size: Batch processing size, controls the number of rows processed simultaneously
            request_delay: Request delay time (seconds)
            judge_models: List of models used for review, e.g. ['m1', 'm2']
            answer_columns: List of model answer column names to review
            question_col: Column name containing questions in Excel
            rubric_col: Column name containing scoring criteria JSON in Excel
        """
        # Use values from config file if parameters are not provided
        self.batch_size = batch_size if batch_size is not None else CONFIG['processing']['batch_size']
        self.request_delay = request_delay
        self.last_request_time = 0
        self.question_col = question_col
        self.rubric_col = rubric_col
        # Read concurrency control parameters from config file
        self.concurrent_models = CONFIG['processing']['concurrent_models']
        self.concurrent_items = CONFIG['processing']['concurrent_items']
        self.base_delay = CONFIG['request_control']['base_delay']
        self.batch_delay = CONFIG['request_control']['batch_delay']
        self.item_delay = CONFIG['request_control']['item_delay']
        # Retry configuration
        self.max_retries = CONFIG['retry']['max_retries']
        self.retry_multiplier = CONFIG['retry']['retry_multiplier']
        self.rate_limit_wait = CONFIG['retry']['rate_limit_wait']
        # Specify review models (now always has value)
        self.judge_models = judge_models if judge_models else ['m1', 'm2']
        logger.info(f"Using review models: {self.judge_models}")
        # Supported model answer columns (specified by user)
        self.answer_columns = answer_columns or [
            'gpt_5_answer',
            'gemini_2_5_pro_answer',
            'claude_opus_4_answer'
        ]
    async def _judge_one_with_selected_models(self, question: str, model_answer: str, claim: str, claim_type: str = "positive") -> List[Dict]:
        """
        Internal method for review using specified models
        Args:
            question: Question text
            model_answer: Model answer
            claim: Specific point to review
            claim_type: Point type, "positive" or "negative"
        Returns:
            List[Dict]: List of judgment results from various review models
        Note:
            - Only calls review models specified in judge_models
            - If specified models are not available, automatically falls back to available models
        """
        # Import internal functions from judge_engine
        from judge_engine import call_model, MODEL_CFG
        # Verify if specified models exist
        available_models = list(MODEL_CFG.keys())
        valid_models = [m for m in self.judge_models if m in available_models]
        if not valid_models:
            logger.warning(f"Specified review models {self.judge_models} are all unavailable, using all available models {available_models}")
            valid_models = available_models
        elif len(valid_models) < len(self.judge_models):
            invalid_models = [m for m in self.judge_models if m not in available_models]
            logger.warning(f"The following specified review models are unavailable: {invalid_models}, will use: {valid_models}")
        # Only call specified models, pass type parameter
        tasks = [call_model(question, model_answer, claim, mid, claim_type) for mid in valid_models]
        return await asyncio.gather(*tasks)
    async def judge_single_item_with_retry(self, item: Dict, question: str, model_answer: str,
                                           model_name: str, max_retries: int = None) -> Dict:
        """
        Review single point with retry mechanism
        Args:
            item: Point data to review
            question: Question text
            model_answer: Model answer
            model_name: Model name (for result identification)
            max_retries: Maximum retry count
        Returns:
            Dict: Point data containing review results
        Note:
            - Supports automatic retry mechanism, handles network errors and API limits
            - Special handling for 429 errors (rate limiting)
            - Returns error information instead of throwing exceptions on failure
        """
        if max_retries is None:
            max_retries = self.max_retries
        # Get type information from item
        claim_type = item.get('type', 'positive')  # Default to positive
        for attempt in range(max_retries):
            try:
                # Use configured base delay control
                current_time = time.time()
                elapsed = current_time - self.last_request_time
                min_delay = self.base_delay
                if elapsed < min_delay:
                    wait_time = min_delay - elapsed
                    logger.debug(f"Waiting {wait_time:.2f} seconds to avoid rate limiting...")
                    await asyncio.sleep(wait_time)
                self.last_request_time = time.time()
                # Call judgment engine, pass claim_type parameter
                judgments = await self._judge_one_with_selected_models(
                    question, model_answer, item.get('claim', ''), claim_type
                )
                final_result = vote(judgments)
                # Build result
                judge_results = {
                    "final_results": final_result,
                    "origin_results": judgments
                }
                # Return complete item, add judge_results for corresponding model
                result_item = item.copy()
                if 'judge_results' not in result_item:
                    result_item['judge_results'] = {}
                result_item['judge_results'][model_name] = judge_results
                logger.debug(f"Point {item.get('id')} ({claim_type}) review completed for model {model_name}: {final_result}")
                return result_item
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Point {item.get('id')} model {model_name} attempt {attempt+1} failed: {error_msg}")
                # Check if it's a 429 error
                if "429" in error_msg or "RateLimitError" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = self.rate_limit_wait
                        logger.info(f"Encountered rate limit, waiting {wait_time:.2f} seconds before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                # Other errors or last retry
                if attempt == max_retries - 1:
                    logger.error(f"Point {item.get('id')} model {model_name} all retries failed: {error_msg}")
                    # Return error result
                    result_item = item.copy()
                    if 'judge_results' not in result_item:
                        result_item['judge_results'] = {}
                    result_item['judge_results'][model_name] = {
                        "final_results": "Error",
                        "origin_results": [{
                            "model_id": "error",
                            "judgment": "Error",
                            "confidence": 0.0,
                            "latency": 0.0,
                            "error": error_msg
                        }]
                    }
                    return result_item
                # Non-429 errors, use exponential backoff retry
                retry_delay = self.base_delay * (self.retry_multiplier ** attempt)
                await asyncio.sleep(retry_delay)
        # Should not reach here, but as insurance
        result_item = item.copy()
        if 'judge_results' not in result_item:
            result_item['judge_results'] = {}
        result_item['judge_results'][model_name] = {
            "final_results": "Error",
            "origin_results": [{
                "model_id": "error",
                "judgment": "Error",
                "confidence": 0.0,
                "latency": 0.0,
                "error": "Unknown error"
            }]
        }
        return result_item
    async def process_row_items(self, row_data: Dict) -> Dict:
        """
        Process all points for all model answers in a single row (concurrent processing between models)
        Args:
            row_data: Dictionary containing row index, JSON data, questions and answers
        Returns:
            Dict: Processing result, including status, reviewed point list, etc.
        Note:
            - Concurrent review of all model answers for each point
            - Use semaphore to control concurrency count
            - Handle exceptions to ensure single point failure won't interrupt entire process
        """
        row_index = row_data['row_index']
        final_merged_json = row_data['final_merged_json']
        question = row_data['question']
        answers = row_data['answers']
        try:
            # Parse final_merged_json
            if isinstance(final_merged_json, str):
                items = json.loads(final_merged_json)
            else:
                items = final_merged_json
            if not isinstance(items, list):
                raise ValueError("final_merged_json should be a list")
            logger.info(f"Processing row {row_index + 1}, {len(items)} points, {len(answers)} model answers")
            # Process all model answers for each point
            judged_items = []
            # Use configured item concurrency count
            semaphore_items = asyncio.Semaphore(self.concurrent_items)
            async def process_single_item(i, item):
                """
                Process all model answers for a single point
                Args:
                    i: Point index
                    item: Point data
                Returns:
                    Dict: Processed point data containing review results for all models
                """
                async with semaphore_items:
                    logger.debug(f"Processing row {row_index + 1} point {i + 1}")
                    # Initialize judge_results for the point
                    current_item = item.copy()
                    current_item['judge_results'] = {}
                    valid_answers = {k: v for k, v in answers.items() if v and not pd.isna(v)}
                    if valid_answers:
                        # Use configured model concurrency count
                        semaphore_models = asyncio.Semaphore(self.concurrent_models)
                        async def process_model_with_semaphore(model_name, model_answer):
                            """
                            Model review processing with semaphore control
                            Args:
                                model_name: Model name
                                model_answer: Model answer
                            Returns:
                                Dict: Review result
                            """
                            async with semaphore_models:
                                return await self.judge_single_item_with_retry(
                                    current_item, question, str(model_answer), model_name
                                )
                        # Process all models concurrently
                        tasks = [
                            process_model_with_semaphore(model_name, model_answer)
                            for model_name, model_answer in valid_answers.items()
                        ]
                        try:
                            results = await asyncio.gather(*tasks, return_exceptions=True)
                            # Process results
                            for (model_name, _), result in zip(valid_answers.items(), results):
                                if isinstance(result, Exception):
                                    logger.error(f"Row {row_index + 1} point {i} model {model_name} processing exception: {result}")
                                    current_item['judge_results'][model_name] = {
                                        "final_results": "Error",
                                        "origin_results": [{
                                            "model_id": "error",
                                            "judgment": "Error",
                                            "confidence": 0.0,
                                            "latency": 0.0,
                                            "error": str(result)
                                        }]
                                    }
                                else:
                                    current_item['judge_results'][model_name] = result['judge_results'][model_name]
                        except Exception as e:
                            logger.error(f"Row {row_index + 1} point {i} concurrent processing failed: {e}")
                            # Set error results for all models
                            for model_name in valid_answers.keys():
                                current_item['judge_results'][model_name] = {
                                    "final_results": "Error",
                                    "origin_results": [{
                                        "model_id": "error",
                                        "judgment": "Error",
                                        "confidence": 0.0,
                                        "latency": 0.0,
                                        "error": str(e)
                                    }]
                                }
                    return current_item
            # Process all points
            if self.concurrent_items > 1:
                # Process points concurrently
                tasks = [process_single_item(i, item) for i, item in enumerate(items)]
                judged_items = await asyncio.gather(*tasks)
            else:
                # Process points serially
                for i, item in enumerate(items):
                    processed_item = await process_single_item(i, item)
                    judged_items.append(processed_item)
                    # Delay between items
                    if i < len(items) - 1 and self.item_delay > 0:
                        await asyncio.sleep(self.item_delay)
            return {
                "row_index": row_index,
                "status": "success",
                "judged_items": judged_items,
                "total_items": len(items),
                "error": None
            }
        except Exception as e:
            logger.error(f"Processing row {row_index + 1} failed: {str(e)}")
            return {
                "row_index": row_index,
                "status": "error",
                "judged_items": [],
                "total_items": 0,
                "error": str(e)
            }
    async def process_batch(self, batch_data: List[Dict]) -> List[Dict]:
        """
        Process a batch of data (serial processing to control request frequency)
        Args:
            batch_data: Batch data list, each element contains processing data for one row
        Returns:
            List[Dict]: Batch processing result list
        Note:
            - Rows within batch are processed sequentially to avoid too frequent API requests
            - Appropriate delay after each row processing
            - Single row failure won't affect other rows in the batch
        """
        logger.info(f"Starting batch processing, containing {len(batch_data)} rows")
        final_results = []
        for i, row_data in enumerate(batch_data):
            try:
                logger.info(f"Processing row {i + 1}/{len(batch_data)} in batch")
                result = await self.process_row_items(row_data)
                final_results.append(result)
                # Inter-row delay (within batch)
                if i < len(batch_data) - 1 and len(batch_data) > 1:
                    delay = 1.0  # Inter-row delay within batch
                    logger.debug(f"Inter-row waiting {delay} seconds...")
                    await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Row {row_data['row_index']} processing exception in batch: {e}")
                final_results.append({
                    "row_index": row_data['row_index'],
                    "status": "error",
                    "judged_items": [],
                    "total_items": 0,
                    "error": str(e)
                })
        return final_results
    def prepare_batch_data(self, df: pd.DataFrame) -> List[List[Dict]]:
        """
        Prepare batch data
        Args:
            df: Input DataFrame
        Returns:
            List[List[Dict]]: Batched data list
        Note:
            - Validate data integrity for each row
            - Collect all valid model answers
            - Group data by batch size
            - Skip invalid or incomplete rows
        """
        all_data = []
        for idx, row in df.iterrows():
            final_merged_json = row.get(self.rubric_col, '')
            question = row.get(self.question_col, '')
            if not final_merged_json or not question:
                logger.warning(f"Row {idx + 1} data incomplete, skipping")
                continue
            # Collect all model answers
            answers = {}
            has_valid_answer = False
            for col in self.answer_columns:
                if col in df.columns:
                    answer = row.get(col, '')
                    if answer and not pd.isna(answer) and str(answer).strip():
                        answers[col] = str(answer).strip()
                        has_valid_answer = True
                    else:
                        answers[col] = ""
            if not has_valid_answer:
                logger.warning(f"Row {idx + 1} has no valid model answers, skipping")
                continue
            all_data.append({
                "row_index": idx,
                "final_merged_json": final_merged_json,
                "question": question,
                "answers": answers
            })
        # Batch
        batches = []
        for i in range(0, len(all_data), self.batch_size):
            batch = all_data[i:i + self.batch_size]
            batches.append(batch)
        return batches
    async def process_excel_file(self, input_file: str, output_file: str = None, max_rows: int = None):
        """
        Main method for processing Excel files
        Args:
            input_file: Input Excel file path
            output_file: Output Excel file path (optional, auto-generated by default)
            max_rows: Maximum processing rows (optional, for testing)
        Returns:
            str: Output file path
        Note:
            - Read Excel file and validate required columns
            - Process data in batches to control memory usage and API request frequency
            - Update DataFrame and save results
            - Generate processing statistics
        """
        # Check input file
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file does not exist: {input_file}")
        # Set output file
        if output_file is None:
            output_dir = "data/output"
            os.makedirs(output_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Include review model information in filename
            model_suffix = f"_{'_'.join(self.judge_models)}"
            output_file = os.path.join(output_dir, f"{base_name}_multi_judged{model_suffix}_{timestamp}.xlsx")
        # Read Excel file
        logger.info(f"Reading file: {input_file}")
        df = pd.read_excel(input_file)
        # Check required columns
        if self.question_col not in df.columns:
            raise ValueError(f"Excel file must contain '{self.question_col}' column")
        if self.rubric_col not in df.columns:
            raise ValueError(f"Excel file must contain '{self.rubric_col}' column")
        # Check model answer columns
        available_answer_cols = [col for col in self.answer_columns if col in df.columns]
        if not available_answer_cols:
            raise ValueError(f"Excel file must contain at least one model answer column: {self.answer_columns}")
        logger.info(f"Found model answer columns: {available_answer_cols}")
        # Limit rows
        if max_rows is not None:
            df = df.head(max_rows)
            logger.info(f"Limited to processing first {max_rows} rows")
        logger.info(f"Total {len(df)} rows of data read")
        # Prepare batch data
        batches = self.prepare_batch_data(df)
        logger.info(f"Divided into {len(batches)} batches, {self.batch_size} rows per batch")
        logger.info(f"Concurrency configuration: model concurrency={self.concurrent_models}, item concurrency={self.concurrent_items}")
        # Process all batches
        all_results = []
        total_batches = len(batches)
        for batch_idx, batch_data in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{total_batches}")
            try:
                batch_results = await self.process_batch(batch_data)
                all_results.extend(batch_results)
                # Show progress
                processed_rows = (batch_idx + 1) * self.batch_size
                total_rows = len(df)
                progress = min(processed_rows / total_rows * 100, 100)
                logger.info(f"Total progress: {progress:.1f}% ({min(processed_rows, total_rows)}/{total_rows})")
                # Inter-batch delay
                if batch_idx < total_batches - 1:
                    if total_batches == 1:
                        # Only one batch, no delay needed
                        pass
                    else:
                        # Use configured inter-batch delay
                        logger.info(f"Inter-batch waiting {self.batch_delay} seconds...")
                        await asyncio.sleep(self.batch_delay)
            except Exception as e:
                logger.error(f"Batch {batch_idx + 1} processing failed: {str(e)}")
                # Create error results for this batch
                for row_data in batch_data:
                    all_results.append({
                        "row_index": row_data['row_index'],
                        "status": "error",
                        "judged_items": [],
                        "total_items": 0,
                        "error": f"Batch processing failed: {str(e)}"
                    })
        # Update DataFrame
        self.update_dataframe_with_results(df, all_results, available_answer_cols)
        # Save results
        df.to_excel(output_file, index=False)
        logger.info(f"Results saved to: {output_file}")
        # Print statistics
        self.print_statistics(all_results, available_answer_cols)
        return output_file
    def split_items_by_type(self, model_judged_items: List[Dict]) -> tuple:
        """
        Split points into positive and negative categories based on type field

        Args:
            model_judged_items: Model review result list

        Returns:
            tuple: (positive_items, negative_items)
        """
        positive_items = []
        negative_items = []

        for item in model_judged_items:
            item_type = item.get('type', 'positive')
            if item_type == 'negative':
                negative_items.append(item)
            else:
                positive_items.append(item)

        return positive_items, negative_items
    def update_dataframe_with_results(self, df: pd.DataFrame, results: List[Dict], answer_columns: List[str]):
        """
        Update DataFrame with review results
        Args:
            df: DataFrame to update
            results: Review result list
            answer_columns: Model answer column name list
        Note:
            - Create four new columns for each model: complete JSON, positive points, negative points, statistical summary
            - Handle success and failure cases
            - Generate easy-to-understand statistical summary
        """
        # Add review result columns for each model
        for col in answer_columns:
            judged_col = f"{col}_judged_json"
            positive_col = f"{col}_positive_items"
            negative_col = f"{col}_negative_items"
            summary_col = f"{col}_judge_summary"  # New summary column
            if judged_col not in df.columns:
                df[judged_col] = ""
            if positive_col not in df.columns:
                df[positive_col] = ""
            if negative_col not in df.columns:
                df[negative_col] = ""
            if summary_col not in df.columns:  # New summary column
                df[summary_col] = ""
        # Create result mapping
        result_map = {r['row_index']: r for r in results}
        for idx in range(len(df)):
            if idx in result_map:
                result = result_map[idx]
                if result['status'] == 'success':
                    # Generate separate review results for each model
                    for col in answer_columns:
                        # Extract review results for this model
                        model_judged_items = []
                        met_count = 0
                        not_met_count = 0
                        error_count = 0

                        for item in result['judged_items']:
                            if 'judge_results' in item and col in item['judge_results']:
                                model_item = item.copy()
                                model_item['judge_results'] = {
                                    "final_results": item['judge_results'][col]['final_results'],
                                    "origin_results": item['judge_results'][col]['origin_results']
                                }
                                model_judged_items.append(model_item)

                                # Count review results
                                final_result = item['judge_results'][col].get('final_results', 'Error')
                                if final_result == 'Met':
                                    met_count += 1
                                elif final_result == 'Not Met':
                                    not_met_count += 1
                                else:
                                    error_count += 1
                        # Save complete review results for this model
                        judged_col = f"{col}_judged_json"
                        positive_col = f"{col}_positive_items"
                        negative_col = f"{col}_negative_items"
                        summary_col = f"{col}_judge_summary"

                        # Complete JSON
                        df.at[idx, judged_col] = json.dumps(
                            model_judged_items,
                            ensure_ascii=False,
                            indent=2
                        )
                        # Separate points by type
                        positive_items, negative_items = self.split_items_by_type(model_judged_items)
                        # Save positive and negative separate columns
                        df.at[idx, positive_col] = json.dumps(
                            positive_items,
                            ensure_ascii=False,
                            indent=2
                        )
                        df.at[idx, negative_col] = json.dumps(
                            negative_items,
                            ensure_ascii=False,
                            indent=2
                        )

                        # Generate statistical summary
                        total_count = met_count + not_met_count + error_count
                        summary = f"Total: {total_count}, Met: {met_count}, Not Met: {not_met_count}, Error: {error_count}"
                        df.at[idx, summary_col] = summary

                else:
                    # Handle failure cases
                    for col in answer_columns:
                        judged_col = f"{col}_judged_json"
                        positive_col = f"{col}_positive_items"
                        negative_col = f"{col}_negative_items"
                        summary_col = f"{col}_judge_summary"
                        error_msg = f"Processing failed: {result.get('error', 'Unknown error')}"
                        df.at[idx, judged_col] = error_msg
                        df.at[idx, positive_col] = "[]"
                        df.at[idx, negative_col] = "[]"
                        df.at[idx, summary_col] = "Total: 0, Met: 0, Not Met: 0, Error: 0"
    def print_statistics(self, results: List[Dict], answer_columns: List[str]):
        """
        Print statistics
        Args:
            results: Processing result list
            answer_columns: Model answer column name list
        Note:
            - Display overall processing statistics
            - Display review result distribution for each model
            - Calculate key metrics like Met rate
        """
        total_rows = len(results)
        success_rows = sum(1 for r in results if r['status'] == 'success')
        error_rows = total_rows - success_rows
        total_items = sum(r['total_items'] for r in results if r['status'] == 'success')
        print("\n" + "="*60)
        print("Multi-Model Review Statistics Summary")
        print("="*60)
        print(f"Processed rows: {total_rows}")
        print(f"Successfully processed: {success_rows}")
        print(f"Processing failed: {error_rows}")
        print(f"Total points: {total_items}")
        print(f"Review model count: {len(answer_columns)} models")
        print(f"Using review models: {self.judge_models}")
        # Statistics for each model's review results
        for col in answer_columns:
            met_count = 0
            not_met_count = 0
            error_count = 0
            positive_count = 0
            negative_count = 0
            for result in results:
                if result['status'] == 'success':
                    for item in result['judged_items']:
                        if 'judge_results' in item and col in item['judge_results']:
                            final_result = item['judge_results'][col].get('final_results', 'Error')
                            item_type = item.get('type', 'positive')

                            if final_result == 'Met':
                                met_count += 1
                            elif final_result == 'Not Met':
                                not_met_count += 1
                            else:
                                error_count += 1

                            if item_type == 'positive':
                                positive_count += 1
                            else:
                                negative_count += 1
            print(f"\n{col}:")
            print(f"  Met: {met_count}")
            print(f"  Not Met: {not_met_count}")
            print(f"  Error: {error_count}")
            print(f"  Positive points: {positive_count}")
            print(f"  Negative points: {negative_count}")
            if total_items > 0:
                met_rate = (met_count / total_items) * 100
                print(f"  Met rate: {met_rate:.1f}%")
async def main():
    """
    Main function - handle command line arguments and execute review process
    Note:
        - Parse command line arguments
        - Create reviewer instance
        - Execute file processing
        - Display result statistics
    Usage examples:
        python script.py input.xlsx -o output.xlsx --judge_models m1 m2
        python script.py input.xlsx --max_rows 10 --verbose
    """
    parser = argparse.ArgumentParser(description='Excel Merged JSON Multi-Model Review Processor')
    parser.add_argument('input_file', nargs='?',
                        default='data/medical_evaluation_result_test_1.xlsx',
                        help='Input Excel file path')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-b', '--batch_size', type=int,
                        help=f'Batch size (default: {CONFIG["processing"]["batch_size"]})')
    parser.add_argument('-d', '--delay', type=float, default=1.0,
                        help='Request delay seconds (default: 1.0)')
    parser.add_argument('-m', '--max_rows', type=int,
                        help='Maximum processing rows (default: all)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose logging')
    parser.add_argument('--question-col', default='query',
                        help='Specify column name containing questions (default: question)')
    parser.add_argument('--rubric-col',
                        default='final_merged_json',
                        help='JSON points column name (default: rubrics)')
    parser.add_argument('--judge_models', nargs='+', default=['m1', 'm2', 'm3'],
                        choices=['m1', 'm2', 'm3', 'm4'],
                        help='Specify models for review, e.g.: --judge_models m1 m2 (default: m1 m2 m3)')
    parser.add_argument('--answer-columns', nargs='+',
                        default=['gpt_5_answer', 'gemini_2_5_pro_answer', 'claude_opus_4_answer'],
                        help='Specify model answer column names to review')
    args = parser.parse_args()
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    # Create reviewer
    judge = MultiModelMergedJsonJudge(
        batch_size=args.batch_size,
        request_delay=args.delay,
        judge_models=args.judge_models,
        answer_columns=args.answer_columns,
        question_col=args.question_col,
        rubric_col=args.rubric_col,
    )
    try:
        print("Starting Excel Merged JSON multi-model review...")
        print(f"Input file: {args.input_file}")
        print(f"Batch size: {judge.batch_size}")
        print(f"Request delay: {args.delay} seconds")
        print(f"Question column: {args.question_col}")
        print(f"JSON points column: {args.rubric_col}")
        print(f"Model answer columns: {args.answer_columns}")
        print(f"Review models: {args.judge_models}")
        print(f"Concurrency configuration: models={judge.concurrent_models}, items={judge.concurrent_items}")
        # Process file
        output_file = await judge.process_excel_file(
            args.input_file,
            args.output,
            args.max_rows
        )
        print(f"\nProcessing completed!")
        print(f"Output file: {output_file}")
        print(f"\nNew features:")
        print(f"- Each model has corresponding positive and negative separate columns for easy viewing")
        print(f"- Original complete JSON columns retained for subsequent script processing")
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        print(f"Error: {str(e)}")
if __name__ == "__main__":
    asyncio.run(main())