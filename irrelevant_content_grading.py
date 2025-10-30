#!/usr/bin/env python3
"""
Irrelevant Content Grading Assessment Script: Specifically assess the severity level of extracted irrelevant content

Main Functions:
1. Perform S1-S4 level assessment on extracted irrelevant content
2. Support multi-model voting mechanism to ensure assessment accuracy
3. Provide multiple voting strategies (conservative, majority, average)
4. Generate detailed assessment reports and statistical information

Usage Workflow:
1. First use extract_irrelevant_content.py to extract irrelevant content
2. Use this script to perform grading assessment on extracted content
3. Output detailed reports containing levels and reasons
"""

import json
import logging
import re
import asyncio
import pandas as pd
from pathlib import Path
from typing import List, Dict
from judge_engine import MODEL_CFG, get_client
from langchain_core.messages import HumanMessage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ContentGrader:
    """
    Irrelevant Content Grading Assessor

    Main Functions:
    1. Build professional medical content assessment prompts
    2. Call AI models for content level assessment
    3. Parse model returned assessment results
    4. Support batch assessment of multiple irrelevant contents

    Level Standards:
    - S1: Content irrelevant but no factual errors (correct but redundant)
    - S2: Content irrelevant with minor factual errors (numerical range deviation)
    - S3: Content irrelevant with obvious factual errors (specific information errors)
    - S4: Content irrelevant with serious factual errors (involving risks such as wrong dosage, contraindications, etc.)
    """

    def __init__(self):
        """
        Initialize content grading assessor

        Note:
            - Load available AI model configurations
            - Prepare model list for assessment
        """
        self.models = MODEL_CFG

    def _build_grading_prompt(self, question: str, answer: str, irrelevant_content: str, rubrics: List[Dict]) -> str:
        """
        Build level assessment prompt

        Args:
            question: Original clinical question
            answer: Complete model answer
            irrelevant_content: Irrelevant content to be assessed
            rubrics: Assessment criteria list

        Returns:
            str: Built assessment prompt

        Note:
            - Provide clear S1-S4 level judgment standards
            - Combine specific clinical questions and answer content
            - Require model to return structured JSON format results
            - Focus on accuracy and safety of medical content
        """
        rubric_text = "\n".join([f"- {r.get('desc', '')}" for r in rubrics])

        return f"""作为医学内容审核专家，请基于S1-S4等级标准评估以下无关内容的严重程度。
                
                【临床问题】
                {question}
                
                【完整回答】
                {answer}
                
                【待评估的无关内容】
                {irrelevant_content}
                
                【评测要点】
                {rubric_text}
                
                【S等级判定标准】
                - **S1**：内容无关但无事实错误（正确但冗余）
                - **S2**：内容无关且有轻微事实错误（数字范围偏差）
                - **S3**：内容无关且有明显事实错误（具体信息错误）  
                - **S4**：内容无关且有严重事实错误（涉及风险，如错误剂量、禁忌症等）
                
                【输出要求】
                仅返回JSON格式：{{"level":"S等级","reasoning":"简要说明"}}
                示例：{{"level":"S3","reasoning":"对药物剂量存在明显错误"}}
                """

    def _parse_grading_response(self, content: str) -> Dict:
        """
        Parse AI model returned level assessment results

        Args:
            content: Original text content returned by model

        Returns:
            Dict: Parsed results containing level and reasoning

        Note:
            - Prioritize parsing standard JSON format
            - Support extracting JSON code blocks from text
            - Provide multi-level backup parsing strategies
            - Ensure always return valid S1-S4 levels
            - Handle various format exceptions
        """
        try:
            content = content.strip()

            # Try to parse as JSON directly
            try:
                parsed = json.loads(content)
                if "level" in parsed and parsed["level"] in ["S1", "S2", "S3", "S4"]:
                    return {
                        "level": parsed["level"],
                        "reasoning": parsed.get("reasoning", "No specific explanation")
                    }
            except:
                pass

            # Try to extract JSON code block
            json_match = re.search(r'\{[^}]*"level"[^}]*\}', content)
            if json_match:
                parsed = json.loads(json_match.group(0))
                if "level" in parsed and parsed["level"] in ["S1", "S2", "S3", "S4"]:
                    return {
                        "level": parsed["level"],
                        "reasoning": parsed.get("reasoning", "No specific explanation")
                    }

            # Backup: extract level only
            level_match = re.search(r'"level"\s*:\s*"(S[1-4])"', content)
            if level_match:
                return {
                    "level": level_match.group(1),
                    "reasoning": "System automatic assessment"
                }

            # Final backup: find S1-S4 pattern
            level_match = re.search(r'\b(S[1-4])\b', content)
            if level_match:
                return {
                    "level": level_match.group(1),
                    "reasoning": "Basic assessment"
                }

            return {"level": "S1", "reasoning": "Default level"}

        except Exception as e:
            logger.error(f"Parsing failed: {e}, content: {content[:100]}...")
            return {"level": "S1", "reasoning": "Parsing failed"}

    async def grade_single_content(self, model_id: str, question: str, answer: str, irrelevant_content: str, rubrics: List[Dict]) -> Dict:
        """
        Perform level assessment on single irrelevant content

        Args:
            model_id: AI model ID to use
            question: Original question
            answer: Complete answer
            irrelevant_content: Irrelevant content to be assessed
            rubrics: Assessment standards

        Returns:
            Dict: Assessment results including content, level, reasoning, etc.

        Note:
            - Call specified AI model for assessment
            - Handle API call exceptions
            - Return structured assessment results
            - Record detailed debugging information
        """
        try:
            client = get_client(model_id)
            prompt = self._build_grading_prompt(question, answer, irrelevant_content, rubrics)

            logger.debug(f"Using model {model_id} to assess: {irrelevant_content[:50]}...")
            response = await client.ainvoke([HumanMessage(content=prompt)])

            grade_info = self._parse_grading_response(response.content)
            return {
                "content": irrelevant_content,
                **grade_info,
                "model_id": model_id
            }

        except Exception as e:
            logger.error(f"Assessment failed: {e}")
            return {
                "content": irrelevant_content,
                "level": "S1",
                "reasoning": f"Assessment failed: {str(e)}",
                "model_id": model_id
            }

    async def grade_multiple_content(self, model_id: str, question: str, answer: str, irrelevant_contents: List[str], rubrics: List[Dict]) -> List[Dict]:
        """
        Batch assess multiple irrelevant contents

        Args:
            model_id: AI model ID
            question: Original question
            answer: Complete answer
            irrelevant_contents: List of irrelevant contents
            rubrics: Assessment standards

        Returns:
            List[Dict]: Assessment results list for all contents

        Note:
            - Assess each irrelevant content in the list one by one
            - Maintain consistency of assessment result order
            - Handle empty list cases
        """
        if not irrelevant_contents:
            return []

        results = []
        for content in irrelevant_contents:
            result = await self.grade_single_content(model_id, question, answer, content, rubrics)
            results.append(result)

        return results


class VoteProcessor:
    """
    Multi-Model Voting Processor

    Main Functions:
    1. Implement multiple voting strategies (conservative, majority, average)
    2. Handle voting tie situations
    3. Ensure consistency and reliability of assessment results

    Voting Strategy Explanation:
    - Conservative strategy: S4 priority, then handle ties by severity
    - Majority strategy: Majority vote, choose median severity on ties
    - Average strategy: Numerical average then rounding
    """

    def _get_conservative_level(self, levels: List[str]) -> str:
        """
        Conservative strategy: S4 priority, then majority vote (including tie handling)

        Args:
            levels: List of levels given by each model

        Returns:
            str: Finally determined level

        Note:
            - If any model gives S4, directly return S4 (most conservative)
            - Otherwise follow majority voting principle
            - Choose higher severity level on ties
            - Suitable for medical content scenarios with high safety requirements
        """
        if "S4" in levels:
            return "S4"

        level_counts = {}
        for level in levels:
            level_counts[level] = level_counts.get(level, 0) + 1

        max_count = max(level_counts.values())
        tied_levels = [level for level, count in level_counts.items() if count == max_count]

        if len(tied_levels) > 1:
            severity_order = {"S1": 1, "S2": 2, "S3": 3, "S4": 4}
            return max(tied_levels, key=lambda x: severity_order[x])

        return max(level_counts.items(), key=lambda x: x[1])[0]

    def _get_majority_level(self, levels: List[str]) -> str:
        """
        Majority voting strategy (including tie handling)

        Args:
            levels: List of levels given by each model

        Returns:
            str: Finally determined level

        Note:
            - Choose the level with most votes
            - Calculate median severity on ties
            - More balanced compared to conservative strategy
            - Suitable for scenarios requiring balance between accuracy and strictness
        """
        level_counts = {}
        for level in levels:
            level_counts[level] = level_counts.get(level, 0) + 1

        max_count = max(level_counts.values())
        tied_levels = [level for level, count in level_counts.items() if count == max_count]

        if len(tied_levels) > 1:
            severity_order = {"S1": 1, "S2": 2, "S3": 3, "S4": 4}
            tied_severities = [severity_order[level] for level in tied_levels]
            tied_severities.sort()
            median_index = len(tied_severities) // 2
            return ["S1", "S2", "S3", "S4"][tied_severities[median_index] - 1]

        return max(level_counts.items(), key=lambda x: x[1])[0]

    def _get_average_level(self, levels: List[str]) -> str:
        """
        Numerical average strategy

        Args:
            levels: List of levels given by each model

        Returns:
            str: Finally determined level

        Note:
            - Convert S1-S4 to numerical values 1-4
            - Calculate average and round
            - Convert back to corresponding S level
            - Suitable for scenarios requiring numerical processing
        """
        level_map = {"S1": 1, "S2": 2, "S3": 3, "S4": 4}
        numeric_levels = [level_map[level] for level in levels if level in level_map]

        if not numeric_levels:
            return "S1"

        avg_level = round(sum(numeric_levels) / len(numeric_levels))
        reverse_map = {1: "S1", 2: "S2", 3: "S3", 4: "S4"}
        return reverse_map[min(max(avg_level, 1), 4)]


class DataHandler:
    """
    Data Processing and File IO Processor

    Main Functions:
    1. Load input data in different formats (JSON, Excel)
    2. Save assessment results to multiple formats
    3. Generate detailed summary reports
    4. Handle data format conversion
    """

    @staticmethod
    def load_extracted_data(file_path: str) -> List[Dict]:
        """
        Load extracted irrelevant content data

        Args:
            file_path: Input file path, supporting JSON and Excel formats

        Returns:
            List[Dict]: Standardized data record list

        Note:
            - Automatically recognize file format (JSON or Excel)
            - Convert data in different formats to unified structure
            - Handle missing fields and data type conversion
            - Ensure data format consistency
        """
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
            results = []
            for _, row in df.iterrows():
                result = {
                    "row": int(row.get("Row Number", 0)) - 1,
                    "question": str(row.get("Question", "")),
                    "answer": str(row.get("Answer", "")),
                    "extracted_contents": [
                        {
                            "content": str(row.get("Irrelevant Content", "")),
                            "reasoning": str(row.get("Judgment Reasoning", ""))
                        }
                    ],
                    "rubric": str(row.get("Assessment Criteria", ""))
                }
                results.append(result)
            return results

    @staticmethod
    def save_grading_results(results: List[Dict], output_file: str):
        """
        Save grading assessment results

        Args:
            results: Assessment results list
            output_file: Output file path

        Note:
            - Generate detailed Excel format report (including summary and details sheets)
            - Also save JSON format raw data
            - Summary sheet includes final levels and reasons
            - Details sheet includes voting situation of each model
            - Handle display of error records
        """
        summary = []
        details = []

        for r in results:
            if "error" in r:
                summary.append({
                    "Row Number": r["row"]+1,
                    "Error": r["error"],
                    "Final Level": "",
                    "Judgment Reason": "",
                    "Voting Strategy": ""
                })
                continue

            for item in r.get("final_grades", []):
                summary.append({
                    "Row Number": r["row"]+1,
                    "Irrelevant Content": item["content"],
                    "Level": item["level"],
                    "Reason": item["reasoning"],
                    "Voting Strategy": item.get("voting_strategy", "conservative")
                })

                # Model detailed results
                for level, count in item.get("model_votes", {}).items():
                    details.append({
                        "Row Number": r["row"]+1,
                        "Irrelevant Content": item["content"],
                        "Level": level,
                        "Vote Count": count,
                        "Voting Strategy": item.get("voting_strategy", "conservative")
                    })

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            pd.DataFrame(summary).to_excel(writer, sheet_name='Grading Summary', index=False)
            if details:
                pd.DataFrame(details).to_excel(writer, sheet_name='Model Details', index=False)

        # Save JSON format
        json_output = str(Path(output_file).with_suffix('.json'))
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)


async def process_grading(config: Dict = None) -> str:
    """
    Main Processing Workflow - Grading Assessment

    Args:
        config: Configuration parameter dictionary including input file, model list, voting strategy, etc.

    Returns:
        str: Output file path

    Note:
        - Execute complete irrelevant content grading assessment workflow
        - Support multi-model parallel assessment and voting
        - Generate detailed statistical information and reports
        - Handle various exception situations
        - Provide progress tracking and logging

    Processing Workflow:
        1. Load extracted irrelevant content data
        2. Use multiple models to assess each irrelevant content
        3. Determine final level based on voting strategy
        4. Generate statistical reports and detailed results
        5. Save to Excel and JSON format files
    """
    if config is None:
        config = {
            "input_file": "data/input/extracted_content.json",
            "level_models": ["m1", "m2", "m4"],
            "voting_strategy": "conservative",
            "question_column": "question",
            "answer_column": "answer",
            "rubric_column": "rubric"
        }

    grader = ContentGrader()
    vote_processor = VoteProcessor()
    handler = DataHandler()

    logger.info("Starting irrelevant content grading assessment...")

    # Load extracted irrelevant content data
    data = handler.load_extracted_data(config["input_file"])
    logger.info(f"Data loaded successfully, total {len(data)} records")

    results = []
    total_records = len(data)

    for idx, record in enumerate(data):
        logger.info(f"Progress: {idx+1}/{total_records} ({(idx+1)/total_records*100:.1f}%)")

        try:
            row = record["row"]
            question = record["question"]
            answer = record["answer"]
            extracted_contents = record.get("extracted_contents", [])
            rubric = record.get("rubric", "")

            if not extracted_contents:
                results.append({
                    "row": row,
                    "question": question,
                    "answer": answer,
                    "rubric": rubric,
                    "extracted_contents": extracted_contents,
                    "final_grades": []
                })
                logger.info(f" Row {row+1} has no irrelevant content to grade")
                continue

            # Parse assessment criteria
            try:
                rubrics = [{"desc": rubric}] if not rubric.startswith('[') else [
                    {"desc": r.get("desc", "")} for r in json.loads(rubric)
                ]
            except:
                rubrics = [{"desc": rubric}]

            # Use multiple models to assess levels
            level_models = config.get("level_models", ["m1", "m2", "m3"])
            voting_strategy = config.get("voting_strategy", "conservative")

            logger.info(f"Using {len(level_models)} models to assess {len(extracted_contents)} irrelevant contents")

            final_grades = []

            # Perform voting assessment for each irrelevant content
            for content_item in extracted_contents:
                content = content_item["content"]

                # Collect assessment results from all models
                model_results = []
                for model_id in level_models:
                    model_result = await grader.grade_single_content(
                        model_id, question, answer, content, rubrics
                    )
                    model_results.append(model_result)

                # Voting processing
                levels = [r["level"] for r in model_results]
                reasonings = [r["reasoning"] for r in model_results]

                # Use voting strategy to determine final level
                if voting_strategy == "conservative":
                    final_level = vote_processor._get_conservative_level(levels)
                elif voting_strategy == "average":
                    final_level = vote_processor._get_average_level(levels)
                elif voting_strategy == "majority":
                    final_level = vote_processor._get_majority_level(levels)
                else:
                    final_level = vote_processor._get_conservative_level(levels)

                final_reasoning = max(reasonings, key=len) if reasonings else "Based on majority model judgment"

                # Calculate model consistency
                level_counts = {}
                for level in levels:
                    level_counts[level] = level_counts.get(level, 0) + 1

                final_grades.append({
                    "content": content,
                    "level": final_level,
                    "reasoning": final_reasoning,
                    "model_votes": level_counts,
                    "voting_strategy": voting_strategy
                })

            results.append({
                "row": row,
                "extracted_contents": extracted_contents,
                "final_grades": final_grades
            })

            logger.info(f" Row {row+1} processing completed, assessed {len(final_grades)} irrelevant contents")

        except Exception as e:
            logger.error(f"Row {record.get('row', idx)+1} processing failed: {e}")
            results.append({
                "row": record.get("row", idx),
                "error": str(e)
            })

    # Final summary statistics
    successful_results = [r for r in results if "error" not in r]
    failed_results = [r for r in results if "error" in r]
    total_graded = sum(len(r.get("final_grades", [])) for r in successful_results)

    logger.info("=" * 50)
    logger.info("Grading assessment completion statistics:")
    logger.info(f"Total processed records: {len(data)}")
    logger.info(f"Successfully assessed: {len(successful_results)}")
    logger.info(f"Failed records: {len(failed_results)}")
    logger.info(f"Total graded: {total_graded} items")

    # Statistics of level distribution
    level_counts = {}
    for r in successful_results:
        for item in r.get("final_grades", []):
            level = item["level"]
            level_counts[level] = level_counts.get(level, 0) + 1

    logger.info("Level distribution:")
    for level in ["S1", "S2", "S3", "S4"]:
        logger.info(f"  {level}: {level_counts.get(level, 0)} items")

    logger.info("=" * 50)

    # Save results
    output_file = Path(config["input_file"]).parent / f"graded_content_{voting_strategy}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    handler.save_grading_results(results, str(output_file))

    logger.info(f"Completed! Output: {output_file}")
    return str(output_file)


def main():
    """
    Main Function - Entry point for irrelevant content grading assessment system

    Note:
        - Provide system usage instructions and operation guide
        - Execute grading assessment workflow with default configuration
        - Display supported voting strategies and usage methods

    Usage Workflow:
        1. First use extract_irrelevant_content.py to extract irrelevant content
        2. Run this script for grading assessment
        3. View generated Excel and JSON report files

    Voting Strategy Selection:
        - conservative: Conservative strategy, prioritize more severe levels
        - majority: Majority vote, choose the level with most votes
        - average: Average strategy, calculate level based on numerical average
    """
    print("  Irrelevant Content Grading System - Specifically assess level severity")
    print(" Usage:")
    print("  1. First use extract_irrelevant_content.py to extract irrelevant content")
    print("  2. Then use this script for grading assessment")
    print("  3. Supported voting strategies: conservative|majority|average")
    print()

    asyncio.run(process_grading())


if __name__ == "__main__":
    main()