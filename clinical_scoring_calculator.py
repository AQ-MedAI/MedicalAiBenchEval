import pandas as pd
import yaml
import json
from typing import Dict, List, Any, Tuple, Optional
import os
import re
import random
import string
from datetime import datetime


def load_config(config_path: str = "config.yaml") -> Dict:
    """
    Load configuration file

    Args:
        config_path: Configuration file path, default is "config.yaml"

    Returns:
        Dict: Configuration dictionary containing scores corresponding to grading levels

    Note:
        - If configuration file does not exist, default configuration will be created automatically
        - Default configuration includes positive scores for A1~A3 and negative scores for S1~S4
        - Configuration file uses YAML format for easy modification
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        # If configuration file does not exist, use default configuration
        default_config = {
            'point': {
                'A1': 3,
                'A2': 2,
                'A3': 1,
                'S1': -1,
                'S2': -2,
                'S3': -3,
                'S4': -4
            }
        }
        # Create default configuration file
        try:
            with open(config_path, 'w', encoding='utf-8') as file:
                yaml.dump(default_config, file, default_flow_style=False, allow_unicode=True)
            print(f"Default configuration file created: {config_path}")
        except Exception as e:
            print(f"Failed to create configuration file: {e}")
        return default_config


def safe_convert_to_number(value, default=0):
    """
    Safely convert value to number

    Args:
        value: Value to convert, can be string, number or other types
        default: Default value when conversion fails, default is 0

    Returns:
        int/float: Converted numeric value

    Note:
        - Supports cleaning non-numeric characters like commas, spaces in strings
        - Automatically recognizes integers and floats
        - Returns default value and outputs warning when conversion fails
    """
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        try:
            # Remove non-numeric characters like commas, spaces from string (keep negative sign and decimal point)
            cleaned_value = re.sub(r'[^\d.-]', '', value.strip())

            if not cleaned_value:
                return default

            # Try to convert to integer
            if '.' not in cleaned_value:
                return int(cleaned_value)
            else:
                # Try to convert to float
                return float(cleaned_value)

        except (ValueError, AttributeError):
            print(f"Warning: Unable to convert '{value}' to number, using default value {default}")
            return default

    print(f"Warning: Unknown type {type(value)} value '{value}', using default value {default}")
    return default


def parse_irrelevant_content(irrelevant_content_str: str) -> Optional[Dict]:
    """
    Parse irrelevant content field

    Args:
        irrelevant_content_str: JSON string of irrelevant content

    Returns:
        Optional[Dict]: Parsed irrelevant content data, returns None if parsing fails

    Note:
        - Handles irrelevant content JSON data in Excel
        - Supports fault tolerance for empty values and invalid JSON
        - Outputs detailed error information when parsing fails
    """
    try:
        if pd.isna(irrelevant_content_str) or irrelevant_content_str == '':
            return None

        # Parse JSON string
        irrelevant_data = json.loads(irrelevant_content_str)
        return irrelevant_data

    except json.JSONDecodeError as e:
        print(f"Warning: Irrelevant content JSON parsing failed: {e}")
        print(f"Content preview: {str(irrelevant_content_str)[:200]}...")
        return None
    except Exception as e:
        print(f"Warning: Error occurred while parsing irrelevant content: {e}")
        return None


def calculate_irrelevant_penalty(irrelevant_data: Optional[Dict], points_config: Dict) -> Tuple[int, Dict]:
    """
    Calculate irrelevant content penalty

    Args:
        irrelevant_data: Irrelevant content data dictionary
        points_config: Points configuration dictionary

    Returns:
        Tuple[int, Dict]: (total penalty, detailed statistics dictionary)

    Note:
        - Calculate penalty based on levels in final_grades
        - Count quantity and corresponding penalty for each level
        - Return detailed statistics for subsequent analysis
    """
    if not irrelevant_data:
        return 0, {}

    # Initialize statistics
    level_counts = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}
    level_penalties = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}
    total_penalty = 0

    # Get scores from final_grades
    final_grades = irrelevant_data.get('final_grades', [])

    for grade in final_grades:
        level = grade.get('level', 'S1')
        if level in level_counts:
            level_counts[level] += 1
            # Calculate penalty for this level
            raw_level_point = points_config.get(level, -1)
            level_point = abs(safe_convert_to_number(raw_level_point, -1))
            level_penalties[level] += level_point
            total_penalty += level_point

    # Build detailed statistics
    irrelevant_details = {
        "irrelevant_total_penalty": total_penalty,
        "irrelevant_S1_count": level_counts["S1"],
        "irrelevant_S2_count": level_counts["S2"],
        "irrelevant_S3_count": level_counts["S3"],
        "irrelevant_S4_count": level_counts["S4"],
        "irrelevant_S1_penalty": level_penalties["S1"],
        "irrelevant_S2_penalty": level_penalties["S2"],
        "irrelevant_S3_penalty": level_penalties["S3"],
        "irrelevant_S4_penalty": level_penalties["S4"],
        "irrelevant_total_count": sum(level_counts.values())
    }

    return total_penalty, irrelevant_details


def calculate_scores(merged_json_data: List[Dict], irrelevant_content_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Core method for calculating various scores

    Args:
        merged_json_data: JSON list containing scoring data
        irrelevant_content_str: Optional irrelevant content JSON string

    Returns:
        Dict[str, Any]: Dictionary containing various scores and statistical information

    Note:
        - Calculate core indicators like theoretical maximum score, actual score, normalized score
        - Count quantity and scoring for each level
        - Handle irrelevant content penalty
        - Support conditional scoring calculation for Met status
        - Include detailed error handling and logging

    Return field descriptions:
        - max_possible: Theoretical maximum score (sum of all positive score items)
        - final_total_score: Final score (actual score - irrelevant content penalty)
        - normalized: Normalized score (between 0-1)
        - positive_all_score_with_met: Total positive score under Met status
        - rubric_all_score_with_met: Total negative penalty under Met status
    """
    try:
        # Load configuration
        config = load_config()
        points_config = config['point']

        # Initialize variables
        max_possible = 0  # Theoretical maximum score (only accumulate positive scores)
        total_score = 0   # Actual score
        penalty = 0       # Total penalty (absolute value of negative scores)

        # Count specific content for positive and negative scores
        positive_counts = {"A1": 0, "A2": 0, "A3": 0}  # Positive score level statistics
        positive_scores = {"A1": 0, "A2": 0, "A3": 0}  # Positive score statistics
        negative_counts = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}  # Negative score level statistics
        negative_scores = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}  # Negative score statistics

        # Total score statistics after Met
        positive_all_score_with_met = 0  # Total positive score after Met
        rubric_all_score_with_met = 0    # Total negative penalty after Met

        # Safety check input data
        if not merged_json_data:
            print("  Warning: merged_json_data is empty")
            return get_default_scores()

        if not isinstance(merged_json_data, list):
            print(f"  Error: merged_json_data is not list type, but {type(merged_json_data)}")
            raise ValueError(f"merged_json_data should be a list, but got {type(merged_json_data)}")

        # Iterate through each scoring item
        for i, item in enumerate(merged_json_data):
            try:
                # Safety check each item
                if not isinstance(item, dict):
                    print(f"  Warning: Item {i+1} is not dict type, but {type(item)}: {item}")
                    continue

                level = str(item.get('level', '')).strip()  # Ensure level is string

                # Get final_results from judge_results
                judge_results = item.get('judge_results', {})

                # Safety check judge_results
                if not isinstance(judge_results, dict):
                    print(f"  Warning: judge_results of item {i+1} is not dict type: {type(judge_results)}")
                    judge_results = {}

                final_status = str(judge_results.get('final_results', 'Not Met')).strip()

                # Get score corresponding to this level and ensure it's a number
                raw_point_value = points_config.get(level, 0)
                point_value = safe_convert_to_number(raw_point_value, 0)

                print(f"  Item {i+1}: level={level}, final_status={final_status}, point_value={point_value}")

                # Determine if point > 0, accumulate max_possible or penalty
                if point_value > 0:
                    max_possible += point_value
                elif point_value < 0:
                    penalty += abs(point_value)  # Absolute value of negative score

                # Determine if final == Met, if so accumulate total_score and count specific content
                if final_status == "Met":
                    total_score += point_value

                    # Count specific positive and negative score content
                    if point_value > 0 and level in positive_counts:
                        positive_counts[level] += 1
                        positive_scores[level] += point_value
                        # Accumulate total positive score after Met
                        positive_all_score_with_met += point_value
                    elif point_value < 0 and level in negative_counts:
                        negative_counts[level] += 1
                        negative_scores[level] += abs(point_value)
                        # Accumulate total negative penalty after Met (take absolute value)
                        rubric_all_score_with_met += abs(point_value)

            except Exception as e:
                print(f"  Error processing item {i+1}: {e}")
                print(f"  Item content: {item}")
                continue

        # Handle irrelevant content score (if provided and valid)
        irrelevant_penalty = 0
        irrelevant_details = {
            "irrelevant_total_penalty": 0,
            "irrelevant_S1_count": 0, "irrelevant_S2_count": 0, "irrelevant_S3_count": 0, "irrelevant_S4_count": 0,
            "irrelevant_S1_penalty": 0, "irrelevant_S2_penalty": 0, "irrelevant_S3_penalty": 0, "irrelevant_S4_penalty": 0,
            "irrelevant_total_count": 0
        }

        # Only process when valid irrelevant content data is provided
        if irrelevant_content_str and not pd.isna(irrelevant_content_str) and str(irrelevant_content_str).strip():
            print(f"  Processing irrelevant content score...")
            try:
                # Parse irrelevant content JSON
                irrelevant_scores = json.loads(irrelevant_content_str)
                if isinstance(irrelevant_scores, dict):
                    # Count irrelevant content for each level
                    level_counts = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}
                    level_penalties = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}

                    final_grades = irrelevant_scores.get('final_grades', [])
                    if isinstance(final_grades, list):
                        for grade in final_grades:
                            if isinstance(grade, dict):
                                level = grade.get('final_level', 'S1')  # Note this might be final_level
                                if level in level_counts:
                                    level_counts[level] += 1
                                    # Calculate penalty for this level
                                    raw_level_point = points_config.get(level, -1)
                                    level_point = abs(safe_convert_to_number(raw_level_point, -1))
                                    level_penalties[level] += level_point
                                    irrelevant_penalty += level_point

                        irrelevant_details = {
                            "irrelevant_total_penalty": irrelevant_penalty,
                            "irrelevant_S1_count": level_counts["S1"],
                            "irrelevant_S2_count": level_counts["S2"],
                            "irrelevant_S3_count": level_counts["S3"],
                            "irrelevant_S4_count": level_counts["S4"],
                            "irrelevant_S1_penalty": level_penalties["S1"],
                            "irrelevant_S2_penalty": level_penalties["S2"],
                            "irrelevant_S3_penalty": level_penalties["S3"],
                            "irrelevant_S4_penalty": level_penalties["S4"],
                            "irrelevant_total_count": sum(level_counts.values())
                        }
                        print(f"  Irrelevant content penalty: {irrelevant_penalty}, total count: {sum(level_counts.values())}")
                    else:
                        print(f"  Warning: final_grades is not list type, skipping irrelevant content scoring")
                else:
                    print(f"  Warning: Irrelevant content data format incorrect, skipping irrelevant content scoring")
            except json.JSONDecodeError as e:
                print(f"  Warning: Irrelevant content JSON parsing failed, skipping irrelevant content scoring: {e}")
            except Exception as e:
                print(f"  Warning: Error processing irrelevant content score, skipping irrelevant content scoring: {e}")
        else:
            print(f"  Irrelevant content data is empty or invalid, skipping irrelevant content scoring")

        # Calculate final score (including irrelevant content penalty)
        final_total_score = total_score - irrelevant_penalty
        final_penalty = penalty + irrelevant_penalty

        # Calculate normalized score
        normalized = max(final_total_score, 0) / max_possible if max_possible > 0 else 0

        print(f"  Calculation complete: theoretical maximum={max_possible}, actual score={final_total_score}, normalized={normalized:.4f}")
        print(f"  Total positive score after Met={positive_all_score_with_met}, total negative penalty after Met={rubric_all_score_with_met}")

        # Return all scores
        scores = {
            "max_possible": max_possible,
            "final_total_score": final_total_score,
            "normalized": round(normalized, 4),
            "final_penalty": final_penalty,
            "positive_score_raw": total_score,
            "penalty": penalty,
            "A1_count": positive_counts["A1"],
            "A2_count": positive_counts["A2"],
            "A3_count": positive_counts["A3"],
            "A1_score": positive_scores["A1"],
            "A2_score": positive_scores["A2"],
            "A3_score": positive_scores["A3"],
            "positive_total_count": sum(positive_counts.values()),
            "rubric_S1_count": negative_counts["S1"],
            "rubric_S2_count": negative_counts["S2"],
            "rubric_S3_count": negative_counts["S3"],
            "rubric_S4_count": negative_counts["S4"],
            "rubric_S1_penalty": negative_scores["S1"],
            "rubric_S2_penalty": negative_scores["S2"],
            "rubric_S3_penalty": negative_scores["S3"],
            "rubric_S4_penalty": negative_scores["S4"],
            "rubric_total_count": sum(negative_counts.values()),
            # New fields
            "positive_all_score_with_met": positive_all_score_with_met,
            "rubric_all_score_with_met": rubric_all_score_with_met
        }

        # Merge irrelevant content detailed scores
        scores.update(irrelevant_details)
        return scores

    except Exception as e:
        print(f"  Error occurred while calculating scores: {e}")
        # Return default values containing all fields to avoid KeyError
        return get_default_scores(str(e))


def generate_random_suffix(length=6):
    """
    Generate random suffix

    Args:
        length: Random string length, default is 6

    Returns:
        str: Suffix composed of timestamp + random string

    Note:
        - Used to generate unique suffix for output files
        - Format: YYYYMMDD_HHMMSS_random_string
        - Avoid filename conflicts
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{timestamp}_{random_chars}"


def add_random_suffix_to_filename(filename: str) -> str:
    """
    Add random suffix to filename

    Args:
        filename: Original filename

    Returns:
        str: Filename with suffix added

    Note:
        - Insert random suffix between filename and extension
        - Keep original file extension unchanged
    """
    name, ext = os.path.splitext(filename)
    suffix = generate_random_suffix()
    new_filename = f"{name}_{suffix}{ext}"
    return new_filename


def get_irrelevant_column_for_model(model_column: str) -> str:
    """
    Get corresponding irrelevant content column name based on model column name

    Args:
        model_column: Model column name

    Returns:
        str: Corresponding irrelevant content column name

    Note:
        - Defines mapping relationship between model review result columns and irrelevant content columns
        - Used for automatic matching of related data columns
        - Returns empty string if no corresponding relationship found
    """
    # Define mapping relationship between model columns and irrelevant content columns
    model_to_irrelevant = {
        'gpt_5_answer_judged_json': 'gpt_5_answer_irrelevant_content',
        'gemini_2_5_pro_answer_judged_json': 'gemini_2_5_pro_answer_irrelevant_content',
        'claude_opus_4_answer_judged_json': 'claude_opus_4_answer_irrelevant_content'
    }

    return model_to_irrelevant.get(model_column, '')


def fix_truncated_json(json_str: str) -> str:
    """
    Attempt to fix truncated JSON string

    Args:
        json_str: Possibly truncated JSON string

    Returns:
        str: Fixed JSON string, returns empty array '[]' if fix fails

    Note:
        - Excel cells have 32767 character limit, overly long JSON may be truncated
        - Find last complete JSON object by analyzing bracket matching
        - Automatically complete missing end symbols
        - Return empty array when fix fails to avoid program crash
    """
    try:
        # Try direct parsing first
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError as e:
        print(f"    JSON parsing failed, attempting fix: {e}")

        # JSON is truncated, attempt to fix
        json_str = json_str.strip()

        # If not ending with ], it means truncated
        if not json_str.endswith(']'):
            # Find last complete object end position
            last_complete_obj = -1
            brace_count = 0
            in_string = False
            escape_next = False

            for i, char in enumerate(json_str):
                if escape_next:
                    escape_next = False
                    continue

                if char == '\\':
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found end of a complete object
                            last_complete_obj = i

            if last_complete_obj > 0:
                # Truncate to last complete object, then add ]
                fixed_json = json_str[:last_complete_obj + 1] + ']'
                try:
                    json.loads(fixed_json)
                    print(f"    JSON fix successful, truncated to position {last_complete_obj}")
                    return fixed_json
                except:
                    print(f"    JSON fix failed")

        # If fix fails, return empty array
        print(f"    Cannot fix JSON, returning empty array")
        return '[]'


def load_and_process_data(input_file: str,
                          model_columns: List[str] = None) -> Tuple[pd.DataFrame, Dict[str, List[Dict]]]:
    """
    Load Excel data and process scores for all models

    Args:
        input_file: Input Excel file path
        model_columns: List of model column names to process, uses default columns if None

    Returns:
        Tuple[pd.DataFrame, Dict[str, List[Dict]]]: (original DataFrame, score data for each model)

    Note:
        - Read Excel file and validate data integrity
        - Automatically detect and match irrelevant content columns
        - Handle JSON truncation issues
        - Calculate detailed score statistics for each model
        - Support fault tolerance, single row failure won't affect overall processing

    Usage example:
        df, scores = load_and_process_data('input.xlsx', ['gpt_5_answer_judged_json'])
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file does not exist: {input_file}")

        # Read Excel file
        print(f"Reading Excel file: {input_file}")
        df = pd.read_excel(input_file)
        print(f"Read {len(df)} rows of data")
        print(f"Column names: {list(df.columns)}")

        # Default model columns
        if model_columns is None:
            model_columns = [
                'gpt_5_answer_judged_json',
                'gemini_2_5_pro_answer_judged_json',
                'claude_opus_4_answer_judged_json'
            ]

        # Check if model columns exist
        existing_columns = []
        for col in model_columns:
            if col in df.columns:
                existing_columns.append(col)
            else:
                print(f"Warning: Column '{col}' does not exist, will skip")

        if not existing_columns:
            raise ValueError("No specified model columns found")

        print(f"Will process the following model columns: {existing_columns}")

        # Check if irrelevant content columns exist
        irrelevant_columns_info = {}
        for model_col in existing_columns:
            irrelevant_col = get_irrelevant_column_for_model(model_col)
            if irrelevant_col and irrelevant_col in df.columns:
                irrelevant_columns_info[model_col] = irrelevant_col
                print(f"Model {model_col} corresponding irrelevant content column: {irrelevant_col}")
            else:
                irrelevant_columns_info[model_col] = None
                print(f"Warning: Model {model_col} corresponding irrelevant content column {irrelevant_col} not found")

        # Store score data for all models
        all_model_scores = {}

        # Calculate scores for each model column
        for model_col in existing_columns:
            print(f"\nStarting to process model column: {model_col}")
            model_scores = []
            irrelevant_col = irrelevant_columns_info[model_col]

            for index, row in df.iterrows():
                print(f"Processing row {index+1}, model: {model_col}")
                try:
                    # Parse model's JSON field
                    merged_json_str = row[model_col]

                    if pd.isna(merged_json_str) or merged_json_str == '':
                        print("  JSON is empty, using default scores")
                        scores = get_default_scores()
                    else:
                        # Check JSON length, if close to 32767 it might be truncated
                        json_str = str(merged_json_str)
                        print(f"  JSON content length: {len(json_str)}")
                        if len(json_str) >= 32760:  # Close to 32767 truncation point
                            print(f"  Detected possibly truncated JSON, attempting fix...")
                            json_str = fix_truncated_json(json_str)

                        # Parse JSON data
                        merged_json_data = json.loads(json_str)
                        print(f"  Parsing successful, contains {len(merged_json_data)} items")

                        # Get irrelevant content data for this row
                        irrelevant_content_str = None
                        if irrelevant_col and irrelevant_col in df.columns:
                            irrelevant_content_str = row[irrelevant_col]
                            if pd.isna(irrelevant_content_str) or irrelevant_content_str == '':
                                irrelevant_content_str = None
                                print("  Irrelevant content data is empty")
                            else:
                                print(f"  Found irrelevant content data, length: {len(str(irrelevant_content_str))}")
                        else:
                            print(f"  Irrelevant content column {irrelevant_col} not found, skipping irrelevant content scoring")

                        # Calculate scores
                        scores = calculate_scores(merged_json_data, irrelevant_content_str)

                    model_scores.append(scores)
                    print(f"  Row {index+1} processing complete")

                except json.JSONDecodeError as e:
                    print(f"Row {index+1} JSON parsing error: {e}")
                    print(f"JSON content preview: {str(merged_json_str)[:200]}...")
                    model_scores.append(get_default_scores("JSON parsing failed"))

                except Exception as e:
                    print(f"Row {index+1} processing error: {e}")
                    model_scores.append(get_default_scores(str(e)))

            # Store score data for this model
            all_model_scores[model_col] = model_scores
            print(f"Model {model_col} processing complete, {len(model_scores)} records total")

        print(f"\nData loading and processing complete!")
        print(f"Processed {len(df)} rows of data, {len(existing_columns)} models")
        return df, all_model_scores

    except Exception as e:
        print(f"Error occurred while loading and processing data: {e}")
        import traceback
        traceback.print_exc()
        raise


def save_results_to_excel(df: pd.DataFrame,
                          all_model_scores: Dict[str, List[Dict]],
                          output_file: str) -> str:
    """
    Save processing results to Excel file

    Args:
        df: Original DataFrame
        all_model_scores: Score data dictionary for each model
        output_file: Output file path

    Returns:
        str: Actual output file path (with random suffix)

    Note:
        - Automatically add timestamp and random suffix to output file to avoid overwriting
        - Convert score dictionary to JSON string for storage
        - Create output directory (if not exists)
        - Output detailed statistical information
        - Display score situation for each row and each model
    """
    try:
        # Add random suffix to output file
        output_file_with_suffix = add_random_suffix_to_filename(output_file)
        print(f"Output file will be saved as: {output_file_with_suffix}")

        # Create copy of output DataFrame
        output_df = df.copy()

        # Add score columns for each model
        for model_col, scores_list in all_model_scores.items():
            score_column_name = f"{model_col}_scores"

            # Convert score dictionary to JSON string
            scores_json_list = []
            for scores in scores_list:
                scores_json_list.append(json.dumps(scores, ensure_ascii=False))

            output_df[score_column_name] = scores_json_list
            print(f"Added score column: {score_column_name}")

        # Ensure output directory exists
        output_dir = os.path.dirname(output_file_with_suffix)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Export to Excel
        output_df.to_excel(output_file_with_suffix, index=False)
        print(f"\nResults saved to: {output_file_with_suffix}")

        # Print statistics
        print(f"\n{'='*80}")
        print("Save Statistics:")
        print(f"Total rows: {len(output_df)}")
        print(f"Total columns: {len(output_df.columns)}")
        print(f"Number of models processed: {len(all_model_scores)}")

        # Display score statistics for each model
        print(f"\nScore Statistics by Model:")
        for model_col, scores_list in all_model_scores.items():
            print(f"\nModel: {model_col}")
            print("-" * 60)

            for i, scores in enumerate(scores_list):
                # Use English field names to get data, but display Chinese labels
                base_info = (f"Row {i+1}: theoretical maximum={scores.get('max_possible', 0)}, "
                             f"actual score={scores.get('final_total_score', 0)}, "
                             f"normalized={scores.get('normalized', 0)}, "
                             f"total penalty={scores.get('final_penalty', 0)}")

                # If includes irrelevant content score, display detailed information
                if 'irrelevant_total_penalty' in scores:
                    irrelevant_info = (f" [irrelevant content: count={scores.get('irrelevant_total_count', 0)}, "
                                       f"penalty={scores.get('irrelevant_total_penalty', 0)}]")
                    base_info += irrelevant_info

                print(base_info)

                if 'error' in scores:
                    print(f"      Error: {scores['error']}")

        return output_file_with_suffix

    except Exception as e:
        print(f"Error occurred while saving results: {e}")
        import traceback
        traceback.print_exc()
        raise


def process_excel_data(input_file: str = None,
                       input_df: pd.DataFrame = None,
                       output_file: str = None,
                       model_columns: List[str] = None,
                       irrelevant_file: str = None) -> str:
    """
    Complete processing workflow: load data -> calculate scores -> save results

    Args:
        input_file: Input Excel file path (choose one with input_df)
        input_df: Input DataFrame (choose one with input_file)
        output_file: Output Excel file path
        model_columns: List of model column names to process
        irrelevant_file: Irrelevant content JSON file path (optional, currently unused)

    Returns:
        str: Actual output file path

    Note:
        - Supports two input methods: file path or direct DataFrame input
        - Automatically handles irrelevant content scoring data in Excel
        - Complete workflow includes data validation, score calculation, result saving
        - Outputs detailed processing progress and statistical information

    Usage examples:
        # Using file path
        result_file = process_excel_data(input_file='input.xlsx', output_file='output.xlsx')

        # Using DataFrame
        result_file = process_excel_data(input_df=df, output_file='output.xlsx')
    """
    print("=" * 80)
    print("Starting Multi-Model Scoring Processing (including irrelevant content scoring from Excel)")
    print("=" * 80)

    # Step 1: Load and process data
    print("\n Step 1: Load and process data")

    if input_df is not None:
        # Use passed DataFrame directly
        print("Using passed DataFrame")
        df = input_df.copy()
        print(f"DataFrame contains {len(df)} rows of data")
        print(f"Column names: {list(df.columns)}")

        # Process irrelevant content data (if irrelevant_file is provided)
        irrelevant_data_map = {}
        if irrelevant_file and os.path.exists(irrelevant_file):
            print(f"Loading irrelevant content data: {irrelevant_file}")
            try:
                with open(irrelevant_file, 'r', encoding='utf-8') as f:
                    irrelevant_data = json.load(f)

                # Build mapping from row-model to irrelevant content
                for item in irrelevant_data:
                    row_idx = item.get('row', 0)
                    model = item.get('model', '')
                    final_grades = item.get('final_grades', [])

                    if final_grades:  # Only add when there is scoring data
                        irrelevant_data_map[(row_idx, model)] = {
                            'final_grades': final_grades
                        }

                print(f"Loaded {len(irrelevant_data_map)} irrelevant content records")
            except Exception as e:
                print(f"Failed to load irrelevant content data: {e}")

        # Process score data
        all_model_scores = process_dataframe_scores(df, model_columns, irrelevant_data_map)

    elif input_file is not None:
        # Use original file processing logic
        df, all_model_scores = load_and_process_data(input_file, model_columns)
    else:
        raise ValueError("Must provide input_file or input_df parameter")

    # Step 2: Save results
    print("\n Step 2: Save results to Excel")
    result_file = save_results_to_excel(df, all_model_scores, output_file)

    print("\n" + "=" * 80)
    print(" Processing Complete!")
    print(f" Output file: {result_file}")
    print("=" * 80)

    return result_file


def process_dataframe_scores(df: pd.DataFrame,
                             model_columns: List[str] = None,
                             irrelevant_data_map: Dict = None) -> Dict[str, List[Dict]]:
    """
    Process score data in DataFrame

    Args:
        df: Input DataFrame
        model_columns: List of model column names to process
        irrelevant_data_map: Irrelevant content data mapping (currently unused, interface reserved)

    Returns:
        Dict[str, List[Dict]]: Score data for each model

    Note:
        - Extract model review results and irrelevant content data from DataFrame
        - Automatically match corresponding irrelevant content columns
        - Handle JSON truncation and parsing errors
        - Generate complete score statistics for each model
    """
    # Default model columns
    if model_columns is None:
        model_columns = [
            'gpt_5_answer_judged_json',
            'gemini_2_5_pro_answer_judged_json',
            'claude_opus_4_answer_judged_json'
        ]

    # Check if model columns exist
    existing_columns = []
    for col in model_columns:
        if col in df.columns:
            existing_columns.append(col)
        else:
            print(f"Warning: Column '{col}' does not exist, will skip")

    if not existing_columns:
        raise ValueError("No specified model columns found")

    print(f"Will process the following model columns: {existing_columns}")

    # Store score data for all models
    all_model_scores = {}

    # Mapping between model columns and irrelevant content columns
    model_to_irrelevant = {
        'gpt_5_answer_judged_json': 'gpt_5_answer_irrelevant_content',
        'gemini_2_5_pro_answer_judged_json': 'gemini_2_5_pro_answer_irrelevant_content',
        'claude_opus_4_answer_judged_json': 'claude_opus_4_answer_irrelevant_content'
    }

    # Calculate scores for each model column
    for model_col in existing_columns:
        print(f"\nStarting to process model column: {model_col}")
        model_scores = []

        # Get corresponding irrelevant content column name
        irrelevant_col = model_to_irrelevant.get(model_col, '')

        for index, row in df.iterrows():
            print(f"Processing row {index+1}, model: {model_col}")
            try:
                # Parse model's JSON field
                merged_json_str = row[model_col]

                if pd.isna(merged_json_str) or merged_json_str == '':
                    print("  JSON is empty, using default scores")
                    scores = get_default_scores()
                else:
                    # Check JSON length, if close to 32767 it might be truncated
                    json_str = str(merged_json_str)
                    print(f"  JSON content length: {len(json_str)}")
                    if len(json_str) >= 32760:  # Close to 32767 truncation point
                        print(f"  Detected possibly truncated JSON, attempting fix...")
                        json_str = fix_truncated_json(json_str)

                    # Parse JSON data
                    merged_json_data = json.loads(json_str)
                    print(f"  Parsing successful, contains {len(merged_json_data)} items")

                    # Get irrelevant content data for this row - read directly from DataFrame
                    irrelevant_content_str = None
                    if irrelevant_col and irrelevant_col in df.columns:
                        irrelevant_content_str = row[irrelevant_col]
                        if pd.isna(irrelevant_content_str) or irrelevant_content_str == '':
                            irrelevant_content_str = None
                            print("  Irrelevant content data is empty")
                        else:
                            print(f"  Found irrelevant content data, length: {len(str(irrelevant_content_str))}")
                    else:
                        print(f"  Irrelevant content column {irrelevant_col} not found, skipping irrelevant content scoring")

                    # Calculate scores
                    scores = calculate_scores(merged_json_data, irrelevant_content_str)

                model_scores.append(scores)
                print(f"  Row {index+1} processing complete")

            except json.JSONDecodeError as e:
                print(f"Row {index+1} JSON parsing error: {e}")
                print(f"JSON content preview: {str(merged_json_str)[:200]}...")
                model_scores.append(get_default_scores("JSON parsing failed"))

            except Exception as e:
                print(f"Row {index+1} processing error: {e}")
                model_scores.append(get_default_scores(str(e)))

        # Store score data for this model
        all_model_scores[model_col] = model_scores
        print(f"Model {model_col} processing complete, {len(model_scores)} records total")

    print(f"\nData processing complete!")
    print(f"Processed {len(df)} rows of data, {len(existing_columns)} models")
    return all_model_scores


def get_default_scores(error_msg: str = None) -> Dict[str, Any]:
    """
    Get default score dictionary

    Args:
        error_msg: Error message (optional)

    Returns:
        Dict[str, Any]: Default score dictionary containing all required fields

    Note:
        - Used when data parsing fails or errors occur
        - Contains all possible score fields to avoid KeyError in subsequent processing
        - All numeric fields default to 0
        - If error message is provided, it will be added to return dictionary
    """
    default_scores = {
        "max_possible": 0,
        "final_total_score": 0,
        "normalized": 0,
        "final_penalty": 0,
        "positive_score_raw": 0,
        "penalty": 0,
        "A1_count": 0, "A2_count": 0, "A3_count": 0,
        "A1_score": 0, "A2_score": 0, "A3_score": 0,
        "positive_total_count": 0,
        "rubric_S1_count": 0, "rubric_S2_count": 0, "rubric_S3_count": 0, "rubric_S4_count": 0,
        "rubric_S1_penalty": 0, "rubric_S2_penalty": 0, "rubric_S3_penalty": 0, "rubric_S4_penalty": 0,
        "rubric_total_count": 0,
        "positive_all_score_with_met": 0,
        "rubric_all_score_with_met": 0,
        "irrelevant_total_penalty": 0,
        "irrelevant_S1_count": 0, "irrelevant_S2_count": 0, "irrelevant_S3_count": 0, "irrelevant_S4_count": 0,
        "irrelevant_S1_penalty": 0, "irrelevant_S2_penalty": 0, "irrelevant_S3_penalty": 0, "irrelevant_S4_penalty": 0,
        "irrelevant_total_count": 0
    }

    if error_msg:
        default_scores["error"] = error_msg

    return default_scores


def main():
    """
    Main function - Entry point for multi-model scoring processing system

    Note:
        - Configure input and output file paths
        - Specify model columns to process
        - Execute complete scoring processing workflow
        - Display processing results and statistical information

    Usage:
        1. Modify input_file to your input Excel file path
        2. Modify output_file to desired output file path
        3. Adjust model_columns list as needed
        4. Run script

    Notes:
        - Ensure input file exists and format is correct
        - Output directory will be created automatically
        - Output filename will automatically add timestamp to avoid overwriting
    """
    print("Multi-Model Scoring Processing System (reading irrelevant content scoring from Excel)")
    print("=" * 50)

    # Configuration parameters
    input_file = "data/input/new/multi_model_scores_4题_multi_judged_m1_m2_m3_20250930_170927.xlsx"
    output_file = "data/output/multi_model_scores.xlsx"

    # Specify model columns to process (can be customized)
    model_columns = [
        'gpt_5_answer_judged_json',
        'gemini_2_5_pro_answer_judged_json',
        'claude_opus_4_answer_judged_json'
    ]

    try:
        # Use complete processing workflow
        result_file = process_excel_data(
            input_file=input_file,
            output_file=output_file,
            model_columns=model_columns
        )
        print(f"\n Processing completed successfully!")
        print(f" Final output file: {result_file}")

    except Exception as e:
        print(f"\n Processing failed: {e}")


if __name__ == "__main__":
    main()