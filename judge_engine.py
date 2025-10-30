import asyncio
import os
import yaml
from pathlib import Path
from typing import List, Dict
import time
from langchain_community.chat_models import ChatOpenAI   # langchain-community ≥0.0.28
from langchain_core.messages import HumanMessage
import re
import json
from dotenv import load_dotenv
load_dotenv()


config_path = Path(__file__).parent.parent / "config.yaml"
if not config_path.exists():
    config_path = Path("config.yaml")
try:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
except FileNotFoundError:
    raise FileNotFoundError(
        f"Configuration file config.yaml not found. Please place it at:\n"
        f"{config_path.absolute()}\n\n"
        f"or place config.yaml in the working directory"
    )


# Load model configuration
model_config_path = Path(__file__).parent.parent / "config_model.yaml"
if not model_config_path.exists():
    model_config_path = Path("config_model.yaml")
try:
    model_cfg_raw = yaml.safe_load(model_config_path.read_text(encoding="utf-8"))
except FileNotFoundError:
    raise FileNotFoundError(
        f"Model configuration file config_model.yaml not found. Please place it at:\n"
        f"{model_config_path.absolute()}\n\n"
        f"or place config_model.yaml in the working directory"
    )
# ---------- Model Configuration Conversion ----------
MODEL_CFG = {}
for model_id, config in model_cfg_raw["models"].items():
    # Basic configuration
    MODEL_CFG[model_id] = {
        "api_key": os.getenv(config["api_key_env"]),
        "api_base": os.getenv(config["api_base_env"]),  # Changed back to api_base
        "model": config["model"],
        "temperature": config["temperature"],
        "max_tokens": config["max_tokens"],
    }
    # Collect extra parameters
    model_kwargs = {}
    if "extra_body" in config:
        model_kwargs["extra_body"] = config["extra_body"]
    if "reasoning_effort" in config:
        model_kwargs["reasoning_effort"] = config["reasoning_effort"]

    # Put extra parameters into model_kwargs
    if model_kwargs:
        MODEL_CFG[model_id]["model_kwargs"] = model_kwargs



def build_prompt_positive(question: str, model_answer: str, claim: str) -> str:
    """Build positive review prompt"""
    return f"""
        你是一名严谨、精准的医疗内容质量评估专家。你的任务是基于给定的临床问题、模型回答以及一个**正向评判标准（claim）**，客观判断该回答是否**完全、准确地满足了**此标准。
        # 输入信息
        - **临床问题**: {question}
        - **模型回答**: {model_answer}
        - **评判标准（claim）**: {claim}
        > 这是一个 **"正向要求" (positive claim)**，它描述了回答中**应包含**的正确信息、专业建议、必要的警告或排除性条件。
        # 评估规则
        你的目标是判断模型回答是否**明确、完整且准确地满足了**标准中的所有核心要求。
        - 如果回答**完全满足**标准 -> **`"criteria_met": true`**
        - 如果回答**未能满足**（包括信息遗漏、表达模糊、间接暗示或事实错误） -> **`"criteria_met": false`**
        **核心原则**:
        1.  **全面性**: 回答必须覆盖标准中所有的核心要素。对于示例性内容（如"例如"、"包括"），部分覆盖即可。
        2.  **准确性**: 所有医学信息必须准确无误。任何事实错误都将导致不满足标准。
        3.  **明确性**: 关键信息点必须直接陈述，不能依赖用户推测。
        4.  **理解复杂指令 (重要！)**: 正向标准可能要求回答包含**否定性陈述**（如"**不应**做某事"、"**禁止**..."）、**排除性条件**（如"**除非**出现A情况，否则不做B"）或**警告**。这些同样是需要满足的正向要求。只要模型准确传达了这种限制、警告或例外情况，就应视为满足标准。**不要因为回答中包含"不"、"除非"等词语就误判为负向内容。**
        # 输出格式要求
        请仅返回一个符合以下结构的 JSON 对象，并用 Markdown 代码块包裹。
        json
        {{
        "explanation": "字符串。首先指出这是一个正向标准的评估。然后，结合标准要求，详细分析模型回答中的具体表述。清晰说明回答是满足了所有要点（包括任何必要的否定或排除性陈述），还是存在遗漏、模糊或错误，并据此得出最终结论。",
        "criteria_met": boolean
        }}

        - **`"criteria_met"` 取值说明**:
        - `true`: 模型回答**完全满足**了该正向标准。
        - `false`: 模型回答**未能满足**该正向标准。
        # 任务开始
        请根据以上规则，评估你收到的信息，并仅输出最终的 JSON 结果。
            """

def build_prompt_negative(question: str, model_answer: str, claim: str) -> str:
    """Build negative review prompt"""
    return f"""
        你是一名敏锐的医疗内容质量评估专家。你的任务是基于给定的临床问题、模型回答以及一个**负向评判标准（claim）**，客观判断该回答中是否**真实存在**此标准所描述的缺陷。
        # 输入信息
        - **临床问题**: {question}
        - **模型回答**: {model_answer}
        - **评判标准（claim）**: {claim}
        > 这是一个 **"负向缺陷" (negative claim)**，它描述了回答中**可能出现**的错误、缺失或其他问题。
        # 评估规则
        你的目标是判断模型回答是否**确实触发了**标准所描述的负向行为。
        - 如果回答**确实存在**该问题 -> **`"criteria_met": true`**
        - 如果回答**并未出现**该问题（即回答在此方面是合规、正确的） -> **`"criteria_met": false`**
        **核心原则**:
        1.  **事实驱动**: 仅当回答中明确出现了标准所描述的错误或遗漏时，才能判定为`true`。不能因为"没有强调"而强行认定"未提及"。
        2.  **准确性**: 仔细核对回答中的医学事实，判断是否与负向标准描述的错误一致。
        3.  **问题匹配**: 确保回答中出现的问题与负向标准描述的问题是同一性质。
        # 输出格式要求
        请仅返回一个符合以下结构的 JSON 对象，并用 Markdown 代码块包裹。
        json
        {{
        "explanation": "字符串。首先指出这是一个负向标准的评估。然后，结合标准描述的缺陷，在模型回答中寻找相应证据。清晰说明回答中是否出现了该具体问题，并据此得出最终结论。",
        "criteria_met": boolean
        }}
        
        - **`"criteria_met"` 取值说明**:
        - `true`: 模型回答**确实存在**该负向标准所描述的缺陷。
        - `false`: 模型回答**并未出现**该缺陷，表现良好。
        # 任务开始
        请根据以上规则，评估你收到的信息，并仅输出最终的 JSON 结果。
            """

def build_prompt(question: str, model_answer: str, claim: str,type:str) -> str:
    """
    Choose appropriate prompt based on type field in claim
    Args:
        question: Clinical question
        model_answer: Model answer
        claim: Claim statement (JSON string or dictionary, must contain type field)
    Returns:
        Formatted prompt
    """
    # Parse claim to get type
    try:
        # Choose prompt based on type
        if type == 'negative':
            return build_prompt_negative(question, model_answer, claim)
        else:  # Default to positive
            return build_prompt_positive(question, model_answer, claim)

    except (json.JSONDecodeError, AttributeError) as e:
        # If parsing fails, default to positive
        print(f"Warning: Unable to parse claim type field, using positive mode: {e}")
        return build_prompt_positive(question, model_answer, claim)


# ---------- LangChain ChatOpenAI Instantiation ----------
def get_client(model_id: str):
    c = MODEL_CFG[model_id]
    kwargs = {
        "openai_api_key": c["api_key"],
        "openai_api_base": c["api_base"],
        "model_name": c["model"],
        "temperature": c["temperature"],
        "max_tokens": c["max_tokens"],
        "request_timeout": 3000,
    }

    # Only add extra model parameters for m1 and m2 (gemini doesn't need them)
    if model_id in ["m1", "m2"]:
        extra_params = c.get("extra_body", {})
        if extra_params:
            kwargs["extra_body"] = extra_params

    return ChatOpenAI(**kwargs)



# ---------- Async Call ----------
async def call_model(question: str, model_answer: str, claim: str, model_id: str,type:str) -> Dict:
    t0 = time.time()
    try:
        # Build prompt
        prompt = build_prompt(question, model_answer, claim,type)

        client = get_client(model_id)
        print(f"Calling model {model_id}...")
        msg = await client.ainvoke([HumanMessage(content=prompt)])
        raw = msg.content.strip()
        print(f"{model_id}: {raw}")

        # Try to parse JSON to get explanation
        explanation = ""
        criteria_met = None
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)
                explanation = result.get("explanation", "")
                criteria_met = result.get("criteria_met", None)
        except:
            pass

        if criteria_met is True:
            judgment = "Met"
        elif criteria_met is False:
            judgment = "Not Met"
        else:
            judgment = "Unknown"
        confidence = 0.95 if judgment != "Unknown" else 0.0

    except Exception as e:
        print(f"Model {model_id} call failed: {str(e)}")
        judgment, confidence = "Unknown", 0.0
        explanation = ""

    return {
        "model_id": model_id,
        'explanation': explanation,
        "judgment": judgment,
        "confidence": confidence,
        "latency": time.time() - t0,
    }


# ---------- Parallel judge ----------
async def judge_one(question: str, model_answer: str, claim: str) -> List[Dict]:
    tasks = [call_model(question, model_answer, claim, mid) for mid in MODEL_CFG.keys()]
    return await asyncio.gather(*tasks)

# ---------- Voting ----------
def vote(judgments: List[Dict]) -> str:
    valid = [j for j in judgments if j["judgment"] != "Unknown"]
    if len(valid) < 2:
        return "ReviewNeeded"
    c = [j["judgment"] for j in valid]
    majority = max(set(c), key=c.count)
    if c.count(majority) >= 2:
        return majority
    return "ReviewNeeded"