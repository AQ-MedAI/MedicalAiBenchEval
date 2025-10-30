"""
Medical Content Evaluation Serial Processor

Main Functions:
1. Complete medical content evaluation pipeline with parallel processing support
2. Step 1: NoMet and Met Review (Optional)
3. Step 2: Irrelevant Content Extraction and Review (Optional)
4. Step 3: Score Calculation (Optional inclusion of irrelevant content)
5. Step 4: Data Analysis and Visualization (Optional)

Processing Flow:
Input Excel -> Parallel execution of Steps 1&2 -> Merge results -> Score calculation -> Data analysis -> Output Excel

Features:
- Support flexible enable/disable of steps
- Steps 1 and 2 can execute in parallel for improved efficiency
- Support configuration files and command line parameters
- Complete error handling and logging
"""

import asyncio
import argparse
import logging
import os
import tempfile
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clinical_answer_judge import MultiModelMergedJsonJudge
from clinical_scoring_calculator import process_excel_data
from enhanced_analyzer import EnhancedMedicalAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MedicalEvaluationPipeline:
    """
    Medical Content Evaluation Pipeline Processor

    Main Functions:
    1. Coordinate execution of multiple evaluation steps
    2. Support parallel processing for improved efficiency
    3. Manage temporary files and data flow
    4. Provide flexible configuration options

    Processing Steps:
    - Step 1: NoMet and Met Review (Judge whether model answers meet evaluation criteria)
    - Step 2: Irrelevant Content Extraction and Review (Identify and grade irrelevant content)
    - Step 3: Score Calculation (Calculate final scores based on review results)
    - Step 4: Data Analysis and Visualization (Generate statistical reports and charts)

    Parallel Processing Strategy:
    - Steps 1 and 2 can execute in parallel (both based on original data)
    - Step 3 needs to wait for the first two steps to complete and merge results
    - Step 4 performs analysis based on Step 3 output
    """

    def __init__(self,
                 enable_met_nomet_review: bool = True,
                 enable_irrelevant_extraction: bool = True,
                 include_irrelevant_in_scoring: bool = True,
                 enable_data_analysis: bool = True,
                 analysis_config_file: str = 'config_visualization.yaml',
                 judge_models: list = None,
                 extract_model: str = "m3",
                 grade_models: list = None,
                 voting_strategy: str = "conservative",
                 question_col: str = "question",
                 rubric_col: str = "rubrics",
                 answer_columns: list = None):
        """
        Initialize Medical Content Evaluation Pipeline

        Args:
            enable_met_nomet_review: Whether to enable NoMet and Met review
            enable_irrelevant_extraction: Whether to enable irrelevant content extraction and review
            include_irrelevant_in_scoring: Whether to include irrelevant content scoring in evaluation
            enable_data_analysis: Whether to enable data analysis and visualization
            analysis_config_file: Data analysis configuration file path
            judge_models: Model list for NoMet and Met review
            extract_model: Model for irrelevant content extraction
            grade_models: Model list for irrelevant content grading
            voting_strategy: Voting strategy (conservative/majority/average)
            question_col: Question column name
            rubric_col: JSON criteria column name
            answer_columns: Model answer column name list

        Note:
            - All steps can be controlled to enable/disable through parameters
            - Support flexible model configuration and column name mapping
            - Create temporary directory to manage intermediate files
        """
        # Process control parameters
        self.enable_met_nomet_review = enable_met_nomet_review
        self.enable_irrelevant_extraction = enable_irrelevant_extraction
        self.include_irrelevant_in_scoring = include_irrelevant_in_scoring
        self.enable_data_analysis = enable_data_analysis
        self.analysis_config_file = analysis_config_file

        # Model configuration parameters
        self.judge_models = judge_models if judge_models else ['m1', 'm2']
        self.extract_model = extract_model
        self.grade_models = grade_models if grade_models else ['m1', 'm2', 'm3']
        self.voting_strategy = voting_strategy

        # Data column name configuration
        self.question_col = question_col
        self.rubric_col = rubric_col
        self.answer_columns = answer_columns or [
            'gpt_5_answer',
            'gemini_2_5_pro_answer',
            'claude_opus_4_answer'
        ]

        # Create temporary directory for intermediate files
        self.temp_dir = Path(tempfile.mkdtemp(prefix="medical_eval_"))
        logger.info(f"Temporary directory: {self.temp_dir}")

    def cleanup(self):
        """
        Clean up temporary files

        Note:
            - Delete temporary directory and files created during processing
            - Called after pipeline completion to free disk space
            - Include exception handling to ensure cleanup failure doesn't affect main process
        """
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info("Temporary file cleanup completed")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {e}")

    async def step1_met_nomet_review(self, input_file: str, max_rows: int = None) -> str:
        """
        Step 1: NoMet and Met Review (Optional)

        Args:
            input_file: Input Excel file path
            max_rows: Maximum rows to process limit

        Returns:
            str: Processed file path

        Note:
            - Perform Met/Not Met judgment for each evaluation criterion of each model answer
            - Use multiple AI models for review, determine final results through voting
            - Generate new Excel file containing detailed review results
            - If this step is disabled, directly return original file path
        """
        if not self.enable_met_nomet_review:
            logger.info("Step 1: Skip NoMet and Met review (disabled)")
            return input_file

        logger.info("="*60)
        logger.info("Step 1: Starting NoMet and Met review")
        logger.info("="*60)

        # Set output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.temp_dir / f"step1_judged_{timestamp}.xlsx"

        # Create reviewer
        judge = MultiModelMergedJsonJudge(
            batch_size=2,
            request_delay=2.0,
            judge_models=self.judge_models,
            question_col=self.question_col,
            rubric_col=self.rubric_col,
            answer_columns=self.answer_columns
        )

        # Execute review
        result_file = await judge.process_excel_file(
            input_file=input_file,
            output_file=str(output_file),
            max_rows=max_rows
        )
        logger.info(f"Step 1 completed, output file: {result_file}")
        return result_file

    async def step2_irrelevant_content_processing(self, input_file: str, max_rows: int = None) -> str:
        """
        Step 2: Irrelevant Content Extraction and Review (Optional)

        Args:
            input_file: Input Excel file path
            max_rows: Maximum rows to process limit

        Returns:
            str: Processed file path

        Note:
            - Extract content unrelated to the question from model answers
            - Perform S1-S4 level assessment on irrelevant content
            - Use multi-model voting to determine final level
            - Generate new Excel file containing irrelevant content analysis results
            - If this step is disabled, directly return original file path
        """
        if not self.enable_irrelevant_extraction:
            logger.info("Step 2: Skip irrelevant content extraction and review (disabled)")
            return input_file

        logger.info("="*60)
        logger.info("Step 2: Starting irrelevant content extraction and review")
        logger.info("="*60)

        # Read DataFrame
        df = pd.read_excel(input_file)

        # Use DataFrame interface for irrelevant content processing
        from general_negative_points import process_dataframe_negative_content

        result_df = await process_dataframe_negative_content(
            df=df,
            question_col=self.question_col,
            target_models=self.answer_columns,
            rubric_col=self.rubric_col,
            extract_model=self.extract_model,
            level_models=self.grade_models,
            voting_strategy=self.voting_strategy,
            max_rows=max_rows
        )

        # Set output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.temp_dir / f"step2_irrelevant_{timestamp}.xlsx"

        # Save results
        result_df.to_excel(output_file, index=False)
        logger.info(f"Step 2 completed, output file: {output_file}")
        return str(output_file)

    def extract_irrelevant_data_from_excel(self, input_file: str) -> str:
        """
        Extract irrelevant content data from Excel file and convert to JSON format

        Args:
            input_file: Excel file containing irrelevant content assessment results

        Returns:
            str: Converted JSON file path, returns None if failed

        Note:
            - Extract scoring data from irrelevant content columns in Excel
            - Convert to JSON format required by scoring system
            - Process irrelevant content data for multiple models
            - Filter invalid and error data records
            - Generate temporary JSON file for scoring system use
        """
        try:
            logger.info("Extracting irrelevant content data from Excel...")

            # Read Excel file
            df = pd.read_excel(input_file)

            # Use user-specified model answer columns
            answer_columns = self.answer_columns

            # Extract irrelevant content data
            irrelevant_data = []

            for idx, row in df.iterrows():
                for answer_col in answer_columns:
                    irrelevant_col = f"{answer_col}_irrelevant_content"

                    if irrelevant_col in df.columns:
                        irrelevant_content = row.get(irrelevant_col, '')

                        if irrelevant_content and not pd.isna(irrelevant_content):
                            try:
                                # Parse JSON data
                                if isinstance(irrelevant_content, str):
                                    content_data = json.loads(irrelevant_content)
                                else:
                                    content_data = irrelevant_content

                                # Check for error information
                                if isinstance(content_data, dict) and 'error' in content_data:
                                    logger.warning(f"Row {idx+1} {answer_col} contains error: {content_data['error']}")
                                    continue

                                # Build data format required by scoring system
                                final_grades = content_data.get("final_grades", [])

                                # Only add when there is actual scoring data
                                if final_grades and len(final_grades) > 0:
                                    irrelevant_item = {
                                        "row": idx,
                                        "model": answer_col,
                                        "final_grades": final_grades
                                    }
                                    irrelevant_data.append(irrelevant_item)
                                    logger.debug(f"Row {idx+1} {answer_col} added {len(final_grades)} irrelevant content scores")

                            except (json.JSONDecodeError, Exception) as e:
                                logger.warning(f"Row {idx+1} {answer_col} irrelevant content data parsing failed: {e}")
                                continue

            if not irrelevant_data:
                logger.info("No valid irrelevant content data found")
                return None

            # Save as temporary JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = self.temp_dir / f"irrelevant_data_{timestamp}.json"

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(irrelevant_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Irrelevant content data extracted, total {len(irrelevant_data)} records, saved to: {json_file}")
            return str(json_file)

        except Exception as e:
            logger.error(f"Failed to extract irrelevant content data: {e}")
            return None

    def step3_scoring(self, input_file: str, output_file: str) -> str:
        """
        Step 3: Score Calculation

        Args:
            input_file: Input Excel file path (containing results from first two steps)
            output_file: Final output file path

        Returns:
            str: Final output file path

        Note:
            - Calculate scores based on Met/Not Met review results
            - Optionally include irrelevant content deductions
            - Support multiple scoring indicators (A-class positive scores, S-class negative scores, etc.)
            - Generate detailed scoring statistics and analysis
            - Output final Excel file containing all scoring data
        """
        logger.info("="*60)
        logger.info("Step 3: Starting score calculation")
        logger.info("="*60)

        # Generate corresponding judgment JSON column names based on user-specified model answer columns
        model_columns = [f"{col}_judged_json" for col in self.answer_columns]

        # Read DataFrame
        logger.info(f"Reading Excel file: {input_file}")
        df = pd.read_excel(input_file)
        logger.info(f"Read {len(df)} rows of data")

        # Determine whether to use irrelevant content scoring
        irrelevant_file = None
        if self.include_irrelevant_in_scoring and self.enable_irrelevant_extraction:
            logger.info("Extracting irrelevant content scoring data...")
            irrelevant_file = self.extract_irrelevant_data_from_excel(input_file)
            if irrelevant_file:
                logger.info(f"Will include irrelevant content scoring in evaluation, data file: {irrelevant_file}")
            else:
                logger.warning("Irrelevant content data extraction failed, scoring will not include irrelevant content")
        else:
            logger.info("Scoring does not include irrelevant content scoring")

        # Execute scoring
        result_file = process_excel_data(
            input_df=df,  # Pass DataFrame instead of file path
            output_file=output_file,
            model_columns=model_columns,
            irrelevant_file=irrelevant_file
        )

        logger.info(f"Step 3 completed, final output file: {result_file}")
        return result_file

    def step4_data_analysis(self, input_file: str) -> str:
        """
        Step 4: Data Analysis and Visualization (Optional)

        Args:
            input_file: Excel file path containing scoring results

        Returns:
            str: Input file path (this step does not modify data file)

        Note:
            - Perform statistical analysis on scoring results
            - Generate various visualization charts (bar charts, box plots, heatmaps, etc.)
            - Create detailed analysis reports
            - Output CSV format summary data
            - All analysis results saved to permanent directory
            - If this step is disabled or analysis fails, does not affect main process
        """
        if not hasattr(self, 'enable_data_analysis') or not self.enable_data_analysis:
            logger.info("Step 4: Skip data analysis (disabled)")
            return input_file

        logger.info("="*60)
        logger.info("Step 4: Starting data analysis and visualization")
        logger.info("="*60)

        try:
            # Create analyzer
            analysis_config_file = getattr(self, 'analysis_config_file', 'config_visualization.yaml')
            analyzer = EnhancedMedicalAnalyzer(config_file=analysis_config_file)

            # Configure analyzer to use scored file
            analyzer.config['input_file'] = input_file

            # Dynamically adjust model column name mapping (based on current pipeline's answer_columns)
            model_mapping = {}
            model_names = ['GPT-5', 'Gemini-2.5-Pro', 'Claude-Opus-4']
            for i, col in enumerate(self.answer_columns):
                if i < len(model_names):
                    model_mapping[model_names[i]] = f'{col}_judged_json_scores'
            analyzer.config['columns']['model_scores'] = model_mapping

            # Set output path to permanent directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_output_dir = Path("data/output/analysis")
            analysis_output_dir.mkdir(parents=True, exist_ok=True)

            analyzer.config['output'] = {
                'visualization': str(analysis_output_dir / f'medical_evaluation_report_{timestamp}.png'),
                'detailed_report': str(analysis_output_dir / f'medical_analysis_report_{timestamp}.txt'),
                'csv_summary': str(analysis_output_dir / f'model_performance_summary_{timestamp}.csv')
            }

            logger.info(f" Analysis target file: {input_file}")
            logger.info(f" Model score column mapping: {model_mapping}")
            logger.info(f" Analysis results will be saved to: {analysis_output_dir}")

            # Run analysis
            analyzer.run_analysis()
            logger.info("Step 4 completed: Data analysis and visualization")
            logger.info(f" Analysis results saved to: {analysis_output_dir}")

            # Display list of generated files
            generated_files = list(analysis_output_dir.glob(f"*{timestamp}*"))
            if generated_files:
                logger.info(" Generated analysis files:")
                for file in generated_files:
                    logger.info(f"  - {file}")

            return input_file

        except Exception as e:
            logger.error(f"Data analysis failed: {e}")
            logger.info("Continue process, skip data analysis step")
            return input_file

    async def run_pipeline(self, input_file: str, output_file: str, max_rows: int = None) -> str:
        """
        Run complete evaluation pipeline

        Args:
            input_file: Input Excel file path
            output_file: Final output Excel file path
            max_rows: Maximum rows to process limit

        Returns:
            str: Final output file path

        Note:
            - Coordinate execution of all processing steps
            - Execute Steps 1 and 2 in parallel for improved efficiency
            - Intelligently merge results from parallel processing
            - Handle various enable/disable combination scenarios
            - Manage data flow and temporary files
            - Provide detailed progress tracking and error handling

        Execution Strategy:
            1. If both Steps 1 and 2 are enabled: Execute in parallel then merge results
            2. If only one is enabled: Execute serially
            3. If both are disabled: Use original data directly
            4. Step 3 performs scoring based on merged results from previous steps
            5. Step 4 performs analysis based on scoring results
        """
        try:
            logger.info(" Starting medical content evaluation pipeline (true parallel execution)")
            logger.info(f"Input file: {input_file}")
            logger.info(f"Output file: {output_file}")
            logger.info(f"NoMet and Met review: {'Enabled' if self.enable_met_nomet_review else 'Disabled'}")
            logger.info(f"Irrelevant content extraction: {'Enabled' if self.enable_irrelevant_extraction else 'Disabled'}")
            logger.info(f"Irrelevant content scoring: {'Included' if self.include_irrelevant_in_scoring else 'Not included'}")
            logger.info(f"Data analysis: {'Enabled' if self.enable_data_analysis else 'Disabled'}")
            logger.info(f"Question column name: {self.question_col}")
            logger.info(f"JSON criteria column name: {self.rubric_col}")
            logger.info(f"Model answer column names: {self.answer_columns}")

            if self.enable_met_nomet_review:
                logger.info(f"Review models: {self.judge_models}")
            if self.enable_irrelevant_extraction:
                logger.info(f"Extraction model: {self.extract_model}")
                logger.info(f"Grading models: {self.grade_models}")
            logger.info(f"Voting strategy: {self.voting_strategy}")

            # Parallel execution strategy
            if self.enable_met_nomet_review and self.enable_irrelevant_extraction:
                # Both steps enabled, execute in parallel
                logger.info(" Steps 1 and 2 starting parallel execution...")

                # Start both steps simultaneously
                tasks = [
                    self.step1_met_nomet_review(input_file, max_rows),
                    self.step2_irrelevant_content_processing(input_file, max_rows)
                ]

                # Wait for both tasks to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check execution results
                for i, result in enumerate(results, 1):
                    if isinstance(result, Exception):
                        logger.error(f"Step {i} execution failed: {result}")
                        raise result

                step1_file, step2_file = results

                # Merge results from both steps
                logger.info(" Merging parallel processing results from both steps...")

                # Load base data
                df_base = pd.read_excel(input_file)
                if max_rows:
                    df_base = df_base.head(max_rows)

                # Step 1 results
                df_step1 = pd.read_excel(step1_file)

                # Step 2 results
                df_step2 = pd.read_excel(step2_file)

                # Intelligent merge: merge different columns from both steps by row index
                # 1. First merge Step 1 results (rubric-related columns)
                step1_cols = [col for col in df_step1.columns if col not in df_base.columns]
                for col in step1_cols:
                    if col in df_step1.columns:
                        df_base[col] = df_step1[col]

                # 2. Then merge Step 2 results (model answer-related columns)
                step2_cols = [col for col in df_step2.columns if col not in df_base.columns]
                for col in step2_cols:
                    if col in df_step2.columns:
                        df_base[col] = df_step2[col]

                logger.info(" Parallel result merge completed")

            elif self.enable_met_nomet_review:
                # Only Step 1 enabled, execute serially
                logger.info(" Executing Step 1: NoMet and Met review...")
                step1_file = await self.step1_met_nomet_review(input_file, max_rows)
                df_base = pd.read_excel(step1_file)

            elif self.enable_irrelevant_extraction:
                # Only Step 2 enabled, execute serially
                logger.info(" Executing Step 2: Irrelevant content extraction and review...")
                step2_file = await self.step2_irrelevant_content_processing(input_file, max_rows)
                df_base = pd.read_excel(step2_file)

            else:
                # Both steps disabled
                logger.info("️ Both Steps 1 and 2 disabled, using original data directly...")
                df_base = pd.read_excel(input_file)
                if max_rows:
                    df_base = df_base.head(max_rows)

            # Create merged file for Step 3 use
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            merged_file = self.temp_dir / f"merged_parallel_{timestamp}.xlsx"

            # Check long text content, set more tolerant format
            max_content_length = 0
            for col in df_base.columns:
                if df_base[col].dtype == 'object':
                    max_len = df_base[col].astype(str).str.len().max()
                    max_content_length = max(max_content_length, max_len)
                    if max_len > 30000:
                        logger.warning(f"Column '{col}' maximum content length: {max_len} characters, may exceed Excel limit")

            # Use xlsxwriter engine to support large text
            with pd.ExcelWriter(merged_file, engine='xlsxwriter') as writer:
                df_base.to_excel(writer, sheet_name='Sheet1', index=False)

                # Configure worksheet to handle large text
                workbook = writer.book
                worksheet = writer.sheets['Sheet1']

                # Set text format and column width
                text_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})

                for i, col in enumerate(df_base.columns):
                    max_len = max(
                        df_base[col].astype(str).str.len().max(),
                        len(str(col))
                    )
                    # Set column width, maximum limit to Excel allowed range
                    col_width = min(max_len + 2, 255)
                    worksheet.set_column(i, i, col_width, text_format)

            logger.info(f"Merged file created, maximum content length: {max_content_length} characters")
            logger.info(" All prerequisite steps completed, starting Step 3 scoring...")

            # Step 3: Use merged complete data for scoring
            final_output = self.step3_scoring(str(merged_file), output_file)

            # Step 4: Data analysis and visualization
            self.step4_data_analysis(final_output)

            logger.info("="*60)
            logger.info(" Pipeline parallel execution completed!")
            logger.info(f"Final output file: {final_output}")

            if self.enable_data_analysis:
                analysis_dir = Path("data/output/analysis")
                if analysis_dir.exists() and list(analysis_dir.glob("*")):
                    logger.info(f" Data analysis reports generated to: {analysis_dir}")
                    # List latest analysis files
                    latest_files = sorted(analysis_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                    for file in latest_files:
                        logger.info(f" {file.name}")
                else:
                    logger.warning("   Data analysis files not found")
            logger.info("="*60)

            return final_output

        except Exception as e:
            logger.error(f"Pipeline parallel execution failed: {e}")
            raise
        finally:
            # Clean up temporary files (optional, may need to keep for debugging)
            pass


async def main():
    """
    Main function - Entry point for medical content evaluation serial processor

    Note:
        - Parse configuration files and command line arguments
        - Create and configure evaluation pipeline
        - Execute complete processing workflow
        - Provide detailed progress feedback and error handling

    Configuration Priority:
        1. Command line arguments (highest priority)
        2. config.yaml configuration file
        3. Program default values (lowest priority)

    Supported Parameters:
        - Basic parameters: input file, output file, maximum rows, etc.
        - Process control: enable/disable various processing steps
        - Model configuration: specify AI models to use and voting strategy
        - Column configuration: customize data column mappings

    Usage Examples:
        python script.py input.xlsx -o output.xlsx
        python script.py input.xlsx --disable-met-nomet --max_rows 100
        python script.py input.xlsx --judge-models m1 m2 --voting-strategy majority
    """
    import yaml

    # Check if config.yaml configuration file exists
    config_path = Path("config.yaml")
    config = {}
    if config_path.exists():
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            logger.info(" Loading configuration file config.yaml")
        except Exception as e:
            logger.warning(f" Configuration file reading failed, using default configuration: {e}")

    parser = argparse.ArgumentParser(description='Medical Content Evaluation Serial Processor')

    # Read default paths from configuration file
    default_input = config.get('files', {}).get('input_file', 'data/medical_evaluation_result_test_1.xlsx')
    default_output = config.get('files', {}).get('output_file', 'data/output/processed_result_final.xlsx')

    # Basic parameters
    parser.add_argument('input_file', nargs='?',
                        default=default_input,
                        help=f'Input Excel file path (default: {default_input})')
    parser.add_argument('-o', '--output',
                        default=default_output,
                        help=f'Output Excel file path (default: {default_output})')
    parser.add_argument('-m', '--max_rows',
                        type=int,
                        default=None,
                        help='Maximum rows to process (default: all)')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        default=False,
                        help='Verbose logging (default: off)')

    # Read process control parameters from configuration file
    default_disable_met = config.get('pipeline', {}).get('disable_met_nomet', False)
    default_disable_irrelevant = config.get('pipeline', {}).get('disable_irrelevant_extraction', False)
    default_exclude_scoring = config.get('pipeline', {}).get('exclude_irrelevant_scoring', False)
    default_disable_analysis = config.get('pipeline', {}).get('disable_data_analysis', False)
    default_analysis_config = config.get('pipeline', {}).get('analysis_config_file', 'config_visualization.yaml')

    # Process control parameters
    parser.add_argument('--disable-met-nomet',
                        action='store_true',
                        default=default_disable_met,
                        help='Disable NoMet and Met review (default: disabled)' if default_disable_met else 'Disable NoMet and Met review (default: enabled)')
    parser.add_argument('--disable-irrelevant',
                        action='store_true',
                        default=default_disable_irrelevant,
                        help='Disable irrelevant content extraction and review (default: disabled)' if default_disable_irrelevant else 'Disable irrelevant content extraction and review (default: enabled)')
    parser.add_argument('--exclude-irrelevant-scoring',
                        action='store_true',
                        default=default_exclude_scoring,
                        help='Do not include irrelevant content scoring in evaluation (default: not included)' if default_exclude_scoring else 'Do not include irrelevant content scoring in evaluation (default: included)')
    parser.add_argument('--disable-data-analysis',
                        action='store_true',
                        default=default_disable_analysis,
                        help='Disable data analysis and visualization (default: disabled)' if default_disable_analysis else 'Disable data analysis and visualization (default: enabled)')
    parser.add_argument('--analysis-config',
                        default=default_analysis_config,
                        help=f'Data analysis configuration file path (default: {default_analysis_config})')

    # Read model parameters from configuration file
    default_judge_models = config.get('models', {}).get('judge_models', ['m1', 'm2', 'm3'])
    default_extract_model = config.get('models', {}).get('extract_model', 'm5')
    default_grade_models = config.get('models', {}).get('grade_models', ['m1', 'm2', 'm3'])
    default_voting_strategy = config.get('models', {}).get('voting_strategy', 'conservative')

    # Model parameters
    parser.add_argument('--judge-models',
                        nargs='+',
                        default=default_judge_models,
                        choices=['m1', 'm2', 'm3', 'm4','m5'],
                        help=f'NoMet and Met review models (default: {" ".join(default_judge_models)})')
    parser.add_argument('--extract-model',
                        default=default_extract_model,
                        choices=['m1', 'm2', 'm3', 'm4','m5'],
                        help=f'Irrelevant content extraction model (default: {default_extract_model})')
    parser.add_argument('--grade-models',
                        nargs='+',
                        default=default_grade_models,
                        choices=['m1', 'm2', 'm3', 'm4','m5'],
                        help=f'Irrelevant content grading models (default: {" ".join(default_grade_models)})')
    parser.add_argument('--voting-strategy',
                        default=default_voting_strategy,
                        choices=['conservative', 'majority', 'average'],
                        help=f'Voting strategy (default: {default_voting_strategy})')

    # Read column name configuration from configuration file
    default_question_col = config.get('columns', {}).get('question_col', 'question')
    default_rubric_col = config.get('columns', {}).get('rubric_col', 'final_merged_json')
    default_answer_columns = config.get('columns', {}).get('answer_columns',
                                                           ['gpt_5_answer', 'gemini_2_5_pro_answer', 'claude_opus_4_answer'])

    # Column name configuration parameters
    parser.add_argument('--question-col',
                        default=default_question_col,
                        help=f'Question column name (default: {default_question_col})')
    parser.add_argument('--rubric-col',
                        default=default_rubric_col,
                        help=f'JSON criteria column name (default: {default_rubric_col})')
    parser.add_argument('--answer-columns',
                        nargs='+',
                        default=default_answer_columns,
                        help=f'Model answer column names (e.g.: {", ".join(default_answer_columns)})')

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check input file
    if not os.path.exists(args.input_file):
        logger.error(f"Input file does not exist: {args.input_file}")
        return

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logger.info(" Starting medical content evaluation pipeline")
    logger.info(f"Input file: {args.input_file}")
    logger.info(f"Output file: {args.output}")
    if config_path.exists():
        logger.info("Configuration source: config.yaml")
    else:
        logger.info("Configuration source: command line arguments/default configuration")

    # Create pipeline
    pipeline = MedicalEvaluationPipeline(
        enable_met_nomet_review=not args.disable_met_nomet,
        enable_irrelevant_extraction=not args.disable_irrelevant,
        include_irrelevant_in_scoring=not args.exclude_irrelevant_scoring,
        enable_data_analysis=not args.disable_data_analysis,
        analysis_config_file=args.analysis_config,
        judge_models=args.judge_models,
        extract_model=args.extract_model,
        grade_models=args.grade_models,
        voting_strategy=args.voting_strategy,
        question_col=args.question_col,
        rubric_col=args.rubric_col,
        answer_columns=args.answer_columns
    )

    try:
        # Run pipeline
        final_output = await pipeline.run_pipeline(
            input_file=args.input_file,
            output_file=args.output,
            max_rows=args.max_rows
        )

        print(f"\n Processing completed!")
        print(f" Final output file: {final_output}")

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        print(f" Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())