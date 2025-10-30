import asyncio
import json
import pandas as pd
from typing import Dict, List, Optional
import os
from datetime import datetime
from extract_irrelevant_content import extract_content_process, ContentExtractor, ExcelHandler as ExtractHandler
from irrelevant_content_grading import process_grading, ContentGrader, VoteProcessor, DataHandler as GradeHandler
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
"""
Coordination Script: Use extract_irrelevant_content.py and irrelevant_content_grading.py for two-step processing
Supports both DataFrame and file path input methods
"""
async def two_step_process(config: Dict = None) -> str:
    """
    Two-step complete workflow:
    1. Use extract_irrelevant_content.py to extract irrelevant content
    2. Use irrelevant_content_grading.py for level assessment
    """

    if config is None:
        config = {
            "input_file": "data/input/random-with-answer.xlsx",
            "question_column": "question",
            "answer_column": "gemini_2_5_pro_answer",
            "rubric_column": "rubrics",
            "extract_model": "m1",
            "level_models": ["m1", "m2", "m3"],
            "voting_strategy": "conservative"
        }

    print(" Starting two-step processing workflow...")
    print("=" * 60)

    # Step 1: Extract irrelevant content
    print("Step 1: Extracting irrelevant content...")
    extract_config = {
        "input_file": config["input_file"],
        "question_column": config["question_column"],
        "answer_column": config["answer_column"],
        "rubric_column": config["rubric_column"],
        "extract_model": config["extract_model"]
    }

    extracted_file = await extract_content_process(extract_config)
    print(f" Extraction completed: {extracted_file}")

    print("-" * 60)

    # Step 2: Level assessment
    print("Step 2: Level assessment...")
    grading_config = {
        "input_file": extracted_file.replace('.xlsx', '.json'),
        "level_models": config["level_models"],
        "voting_strategy": config["voting_strategy"]
    }

    graded_file = await process_grading(grading_config)
    print(f" Grading completed: {graded_file}")

    print("=" * 60)
    print(" Two-step processing fully completed!")
    print(f"Extraction results: {extracted_file}")
    print(f"Grading results: {graded_file}")

    return graded_file
async def process_dataframe_negative_content(
        df: pd.DataFrame,
        question_col: str = "question",
        target_models: List[str] = None,
        rubric_col: str = "rubric",
        extract_model: str = "m5",
        level_models: List[str] = None,
        voting_strategy: str = "conservative",
        max_rows: int = None
) -> pd.DataFrame:
    """
    Process negative content extraction and scoring in DataFrame
    """
    if level_models is None:
        level_models = ["m1", "m2", "m3"]
    if target_models is None:
        target_models = [
            'gpt_5_answer',
            'gemini_2_5_pro_answer',
            'claude_opus_4_answer'
        ]
    logger.info(f"Starting DataFrame negative content processing, target models: {target_models}")
    logger.info(f"Extraction model: {extract_model}, scoring models: {level_models}")
    # Create DataFrame copy
    result_df = df.copy()
    # Limit rows
    if max_rows is not None:
        result_df = result_df.head(max_rows)
        logger.info(f"Limited to processing first {max_rows} rows")
    # Check required columns
    if question_col not in result_df.columns:
        raise ValueError(f"Question column not found: {question_col}")
    if rubric_col not in result_df.columns:
        raise ValueError(f"Rubric column not found: {rubric_col}")
    # Check target model columns
    available_models = [col for col in target_models if col in result_df.columns]
    if not available_models:
        raise ValueError(f"No target model columns found: {target_models}")
    logger.info(f"Found available model columns: {available_models}")
    # Process each row of data
    for idx, row in result_df.iterrows():
        question = row.get(question_col, '')
        rubric = row.get(rubric_col, '')
        if not question or not rubric:
            logger.warning(f"Row {idx+1} missing question or rubric, skipping")
            continue
        logger.info(f"Processing row {idx+1}...")
        # Process each model's answer
        for model_col in available_models:
            if model_col in result_df.columns:
                answer = row.get(model_col, '')
                if answer and not pd.isna(answer):
                    try:
                        # Use single data processing function
                        result = await process_row_direct(
                            question=question,
                            answer=str(answer),
                            rubric=rubric,
                            extract_model=extract_model,
                            level_models=level_models,
                            voting_strategy=voting_strategy
                        )
                        # Modified here: generate correct column name format
                        irrelevant_col = f"{model_col}_irrelevant_content"
                        result_df.at[idx, irrelevant_col] = json.dumps(result, ensure_ascii=False, indent=2)
                        logger.info(f"Row {idx+1} {model_col} processing completed, extracted {len(result.get('final_grades', []))} negative contents")
                        # Add small delay to avoid API rate limiting
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.error(f"Row {idx+1} {model_col} processing failed: {e}")
                        # Save error information
                        irrelevant_col = f"{model_col}_irrelevant_content"
                        result_df.at[idx, irrelevant_col] = json.dumps({"error": str(e)}, ensure_ascii=False)
                else:
                    logger.warning(f"Row {idx+1} {model_col} answer is empty, skipping")
        # Inter-row delay
        if idx < len(result_df) - 1:
            await asyncio.sleep(1.0)
    logger.info("DataFrame negative content processing completed")
    return result_df
async def process_excel_file_negative_content(
        input_file: str,
        output_file: str = None,
        question_col: str = "question",
        target_models: List[str] = None,
        rubric_col: str = "rubric",
        extract_model: str = "m5",
        level_models: List[str] = None,
        voting_strategy: str = "conservative",
        max_rows: int = None
) -> str:
    """
    Process negative content extraction and scoring for Excel file

    Args:
        input_file: Input Excel file path
        output_file: Output Excel file path
        question_col: Question column name
        target_models: Target model list
        rubric_col: Rubric column name
        extract_model: Extraction model
        level_models: Scoring model list
        voting_strategy: Voting strategy
        max_rows: Maximum rows to process

    Returns:
        Output file path
    """
    logger.info(f"Starting Excel file processing: {input_file}")

    # Read Excel file
    df = pd.read_excel(input_file)
    logger.info(f"Read {len(df)} rows of data")

    # Process DataFrame
    result_df = await process_dataframe_negative_content(
        df=df,
        question_col=question_col,
        target_models=target_models,
        rubric_col=rubric_col,
        extract_model=extract_model,
        level_models=level_models,
        voting_strategy=voting_strategy,
        max_rows=max_rows
    )

    # Set output file
    if output_file is None:
        output_dir = "data/output"
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_suffix = f"_{extract_model}_{'_'.join(level_models)}"
        output_file = os.path.join(output_dir, f"{base_name}_negative_content{model_suffix}_{timestamp}.xlsx")

    # Save results
    result_df.to_excel(output_file, index=False)
    logger.info(f"Results saved to: {output_file}")

    # Print statistics
    print_negative_content_statistics(result_df, target_models)

    return output_file
def print_negative_content_statistics(df: pd.DataFrame, target_models: List[str]):
    """Print negative content statistics"""
    print("\n" + "="*60)
    print("Negative Content Processing Statistics")
    print("="*60)
    print(f"Processed rows: {len(df)}")

    for model in target_models:
        irrelevant_col = f"{model}_irrelevant_content"
        if irrelevant_col in df.columns:
            total_items = 0
            error_count = 0

            for idx, row in df.iterrows():
                content = row.get(irrelevant_col, '')
                if content and not pd.isna(content):
                    try:
                        data = json.loads(content)
                        if isinstance(data, dict) and 'final_grades' in data:
                            total_items += len(data['final_grades'])
                        elif 'error' in data:
                            error_count += 1
                    except:
                        error_count += 1

            print(f"\n{model}:")
            print(f"  Total extracted negative content: {total_items}")
            print(f"  Processing errors: {error_count}")

async def process_row_direct(question: str, answer: str, rubric: str, extract_model: str = "m1", level_models: list = None, voting_strategy: str = "conservative") -> Dict:
    """
    Single data quick processing: pass question, answer, rubric directly to get grading results
    """
    if level_models is None:
        level_models = ["m1", "m2", "m3"]
    extractor = ContentExtractor()
    grader = ContentGrader()
    vote_processor = VoteProcessor()
    # Extract irrelevant content
    rubrics = [{"desc": rubric}] if not rubric.startswith('[') else [{"desc": r.get("desc", "")} for r in json.loads(rubric)]
    extracted_contents = await extractor.extract_irrelevant_content(extract_model, question, answer, rubrics)
    if not extracted_contents:
        return {"extracted_contents": [], "final_grades": []}
    # Level assessment
    final_grades = []
    for content_item in extracted_contents:
        content = content_item["content"]
        original_reasoning = content_item.get("reasoning", "")
        # Collect results from each model
        model_results = []
        for model_id in level_models:
            try:
                model_result = await grader.grade_single_content(
                    model_id, question, answer, content, rubrics
                )
                model_results.append(model_result)
            except Exception as e:
                logger.error(f"Model {model_id} scoring failed: {e}")
                # Add default result
                model_results.append({
                    "level": "S1",
                    "severity": "Medium",  # Provide default value
                    "reasoning": f"Scoring failed: {str(e)}"
                })
        # Voting processing - add safety check
        levels = [r.get("level", "S1") for r in model_results]
        severities = [r.get("severity", "Medium") for r in model_results]  # Add default value
        reasonings = [r.get("reasoning", "No reasoning information") for r in model_results]  # Add default value
        if voting_strategy == "conservative":
            final_level = vote_processor._get_conservative_level(levels)
        elif voting_strategy == "average":
            final_level = vote_processor._get_average_level(levels)
        elif voting_strategy == "majority":
            final_level = vote_processor._get_majority_level(levels)
        else:
            final_level = vote_processor._get_conservative_level(levels)
        # Safely get the longest severity and reasoning
        final_severity = max(severities, key=len) if severities and all(severities) else "Medium"
        final_reasoning = max(reasonings, key=len) if reasonings and all(reasonings) else "Based on majority model judgment"
        final_grades.append({
            "content": content,
            "original_reasoning": original_reasoning,
            "final_level": final_level,
            "final_severity": final_severity,
            "reasoning": final_reasoning,
            "model_results": model_results,
            "voting_strategy": voting_strategy
        })
    return {
        "extracted_contents": extracted_contents,
        "final_grades": final_grades
    }
def main():
    print(" Two-Step Processing Coordinator")
    print(" Usage Examples:")
    print("  1. Two-step processing: python negative_content_pipeline.py")
    print("  2. Extract only: python extract_irrelevant_content.py")
    print("  3. Grade only: python irrelevant_content_grading.py")
    print()

    asyncio.run(two_step_process())
if __name__ == "__main__":
    main()