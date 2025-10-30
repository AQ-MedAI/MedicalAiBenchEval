#!/usr/bin/env python3
"""
Content Extraction Script: Specifically designed to extract content unrelated to scoring criteria from medical answers
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

class ContentExtractor:
    def __init__(self):
        self.models = MODEL_CFG

    def _build_extract_prompt(self, question: str, answer: str, rubrics: List[Dict]) -> str:
        """Build prompt for irrelevant content extraction"""
        rubric_text = "\n".join([f"- {r.get('desc', '')}" for r in rubrics])

        return f"""作为医学内容审核专家，请严格依据【评测要点】判断【模型回答】中是否存在**与评分标准无关、偏离临床问题核心的信息内容**。你的任务是识别并提取那些**未服务于任何得分要点、且对解答临床问题无实质贡献的完整信息单元**。

                ⚠️ 核心原则：  
                一个内容是否“无关”，**不取决于它是否专业或详细，而取决于它是否支持、解释、回应【评测要点】中的任何一个条目**。若某内容无法映射到任一得分点，则视为无关。
                
                【临床问题】
                {question}
                
                【模型回答】
                {answer}
                
                【评测要点】
                {rubric_text}
                
                【提取标准】
                仅提取满足以下全部条件的内容：
                - 是一段**语义完整的句子或句群**（不得拆分为短语或术语）
                - 包含医学知识、背景介绍、机制说明或其他专业扩展
                - **与【评测要点】中的任何一项均无直接关联**
                - 其删除不会影响回答在各评分项上的得分能力
                
                常见类型包括但不限于：
                - 疾病历史沿革、药物研发过程
                - 尚未纳入指南的前沿研究或假设性机制
                - 超出问题范围的流行病学数据（如发病率、地域分布）
                - 对非关键术语的过度解释
                - 与其他疾病/治疗的比较性描述（无必要对比时）
                
                【明确排除】（即使冗长也不提取）：
                - 礼貌用语（如“请参考医生建议”）
                - 合理过渡句或结构衔接词
                - 必要术语定义（尤其是缩写首次出现时）
                - 安全警示、个体差异提醒、用药监测建议等风险管理内容（除非明显泛化或离题）
                
                【输出要求】
                返回 JSON 数组，每个对象包含：
                - "content"：原文中被认定为无关的**完整文本段落**
                - "reasoning"：结合【评测要点】逐条分析该内容为何无法支撑任何得分项，在语义上如何偏离主题
                
                【输出格式示例】
                ```json
                [
                    {{
                        "content": "近年来，CAR-T细胞疗法在血液系统恶性肿瘤治疗中取得了突破性进展，已有多个靶向CD19的产品获批上市。",
                        "reasoning": "该句描述CAR-T疗法在血液肿瘤中的应用进展，属于前沿治疗技术介绍。然而，本题临床问题是‘慢性淋巴细胞白血病的一线化疗方案’，评测要点聚焦于苯丁酸氮芥、阿卡替尼等传统与靶向药物的选择依据。CAR-T目前并非CLL一线或常规推荐治疗，且未在评分要点中提及，因此该信息与得分要点无关，属于离题的知识扩展。"
                    }},
                    {{
                        "content": "维生素D受体广泛分布于全身多种组织，包括甲状旁腺、免疫细胞和心血管系统。",
                        "reasoning": "该句提供维生素D受体的解剖分布信息，虽具生物学意义，但本题为‘骨质疏松症的初始治疗策略’，评测要点包括钙剂补充、双膦酸盐使用、生活方式干预等。受体分布细节无助于解释治疗选择或机制核心，亦未出现在评分标准中，故判定为无关背景信息。"
                    }}
                ]
                ```
            """

    def _parse_extract_response_json(self, content: str) -> List[Dict]:
        """Parse JSON format irrelevant content extraction results"""
        try:
            # Try to extract JSON code block
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```down-', content)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                # Try to parse entire content as JSON directly
                json_str = content.strip()

            # Parse JSON
            parsed_items = json.loads(json_str)

            # Validate format
            if isinstance(parsed_items, list):
                validated_items = []
                for item in parsed_items:
                    if isinstance(item, dict) and "content" in item:
                        content_value = item.get("content")
                        if content_value is None:
                            continue
                        
                        validated_item = {
                            "content": str(content_value).strip(),
                            "reasoning": str(item.get("reasoning", "No reason provided")).strip()
                        }
                        # Ensure content is not empty
                        if validated_item["content"]:
                            validated_items.append(validated_item)
                return validated_items
            else:
                return []

        except json.JSONDecodeError:
            logger.warning(f"JSON parsing failed, returning empty list: {content[:100]}...")
            return []
        except Exception as e:
            logger.error(f"Parsing exception: {e}")
            return []

    async def extract_irrelevant_content(self, model_id: str, question: str, answer: str, rubrics: List[Dict]) -> List[Dict]:
        """Extract irrelevant content from a single answer"""
        try:
            client = get_client(model_id)
            prompt = self._build_extract_prompt(question, answer, rubrics)
            logger.debug(f"Extracting content using model {model_id}...")
            response = await client.ainvoke([HumanMessage(content=prompt)])
            irrelevant_contents = self._parse_extract_response_json(response.content)
            logger.info(f"Model {model_id} extraction completed, found {len(irrelevant_contents)} irrelevant contents")
            return irrelevant_contents
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return []

class ExcelHandler:
    @staticmethod
    def load_data(file_path: str, question_col: str, answer_col: str, rubric_col: str) -> pd.DataFrame:
        """Load data and validate columns"""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")

        df = pd.read_excel(file_path)

        required_cols = [question_col, answer_col, rubric_col]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing column: {col}")

        return df

    @staticmethod
    def save_extraction_results(results: List[Dict], output_file: str):
        """Save extraction results"""
        summary = []
        details = []

        for r in results:
            if "error" in r:
                summary.append({
                    "Row Number": r["row"]+1,
                    "Error": r["error"],
                    "Extracted Content Count": 0
                })
                continue

            # Summary information
            summary.append({
                "Row Number": r["row"]+1,
                "Extracted Content Count": len(r.get("extracted_contents", [])),
                "Extraction Model": r.get("extract_model", "")
            })

            # Detailed information
            for item in r.get("extracted_contents", []):
                details.append({
                    "Row Number": r["row"]+1,
                    "Irrelevant Content": item["content"],
                    "Judgment Reasoning": item["reasoning"],
                    "Extraction Model": r.get("extract_model", "")
                })

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            pd.DataFrame(summary).to_excel(writer, sheet_name='Extraction Summary', index=False)
            pd.DataFrame(details).to_excel(writer, sheet_name='Detailed Content', index=False)

        # Save JSON format
        json_output = str(Path(output_file).with_suffix('.json'))
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

async def extract_content_process(config: Dict = None) -> str:
    """Main processing workflow"""
    if config is None:
        config = {
            "input_file": "data/input/random-with-answer.xlsx",
            "question_column": "question",
            "answer_column": "gemini_2_5_pro_answer",
            "rubric_column": "rubrics",
            "extract_model": "m4",  # Extraction model
            "output_dir": "data/output"
        }

    extractor = ContentExtractor()
    handler = ExcelHandler()

    logger.info("Starting content extraction (extracting only irrelevant content)...")

    # Validate configuration
    required_keys = ["input_file", "question_column", "answer_column", "rubric_column"]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing configuration item: {key}")

    df = handler.load_data(
        config["input_file"],
        config["question_column"],
        config["answer_column"],
        config["rubric_column"]
    )

    logger.info(f"Data loaded successfully, {len(df)} rows of data")
    logger.info(f"Data columns: {list(df.columns)}")

    results = []
    extract_model = config.get("extract_model", "m1")

    for idx, row in df.iterrows():
        logger.info(f"Progress: {idx+1}/{len(df)} ({(idx+1)/len(df)*100:.1f}%)")

        try:
            question = str(row[config["question_column"]]).strip()
            answer = str(row[config["answer_column"]]).strip()
            rubric_str = str(row[config["rubric_column"]]).strip()

            if not all([question, answer, rubric_str]):
                results.append({
                    "row": idx,
                    "error": "Missing data"
                })
                continue

            # Parse evaluation criteria
            try:
                rubrics = [{"desc": rubric_str}] if not rubric_str.startswith('[') else [
                    {"desc": r.get("desc", "")} for r in json.loads(rubric_str)
                ]
            except:
                rubrics = [{"desc": rubric_str}]

            # Extract irrelevant content
            extracted_contents = await extractor.extract_irrelevant_content(
                extract_model, question, answer, rubrics
            )

            result = {
                "row": idx,
                "question": question,
                "answer": answer,
                "extracted_contents": extracted_contents,
                "extract_count": len(extracted_contents),
                "extract_model": extract_model
            }

            if extracted_contents:
                logger.info(f" Row {idx+1} extraction successful, found {len(extracted_contents)} irrelevant contents")
            else:
                logger.info(f" Row {idx+1} no irrelevant content")

            results.append(result)

        except Exception as e:
            logger.error(f"Row {idx+1} processing failed: {e}")
            results.append({
                "row": idx,
                "error": str(e)
            })

    # Save results
    output_file = Path(config["input_file"]).parent / f"extracted_content_{extract_model}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    handler.save_extraction_results(results, str(output_file))

    logger.info("=" * 50)
    total_extracted = sum(len(r.get("extracted_contents", [])) for r in results if "error" not in r)
    logger.info(f"Extraction completed!")
    logger.info(f"Total extracted irrelevant content: {total_extracted} items")
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 50)

    return str(output_file)

def main():
    print(" Content Extraction System - Specifically for extracting irrelevant content")
    asyncio.run(extract_content_process())

if __name__ == "__main__":
    main()
