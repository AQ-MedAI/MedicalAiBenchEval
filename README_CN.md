# GAPS: 临床医学AI评估基准系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## 📋 目录

- [概述](#概述)
- [核心功能](#核心功能)
- [快速开始](#快速开始)
  - [安装](#安装)
  - [基本使用](#基本使用)
- [系统架构](#系统架构)
- [数据格式](#数据格式)
  - [输入格式](#输入格式)
  - [输出格式](#输出格式)
- [配置说明](#配置说明)
  - [基础配置](#基础配置)
  - [高级配置](#高级配置)
- [使用指南](#使用指南)
  - [命令行接口](#命令行接口)
  - [Python API](#python-api)
  - [使用示例](#使用示例)
- [评估框架](#评估框架)
  - [评分系统](#评分系统)
  - [评估指标](#评估指标)
- [数据集](#数据集)
  - [胸外科数据集](#胸外科数据集)
  - [数据质量](#数据质量)
- [高级功能](#高级功能)
  - [并行处理](#并行处理)
  - [投票策略](#投票策略)
  - [自定义模型](#自定义模型)
- [开发](#开发)
  - [技术文档](#技术文档)
  - [API参考](#api参考)
  - [故障排除](#故障排除)
- [社区](#社区)
  - [贡献指南](#贡献指南)
  - [引用](#引用)
- [许可证](#许可证)

## 概述

GAPS（Grounded, Automated, Personalized, Scalable）是一个专门为评估临床场景中AI模型而设计的综合评估框架。该系统通过多步骤评估流程为医疗AI系统提供自动化、临床基础的基准测试。

该框架解决了AI临床决策标准化评估的关键需求，提供：
- **临床基础评估**：基于真实医疗指南和专家知识的评估标准
- **自动化流程**：从原始回复到详细性能指标的流程化处理
- **多模型支持**：同时评估多个AI模型并进行比较分析
- **可扩展架构**：通过并行执行能力高效处理大型数据集

## 核心功能

- **🏥 医疗专用评估**：针对临床场景的专业评分标准，包含正负分评分
- **🔄 并行处理**：同时执行Met/Not Met审查和无关内容检测
- **📊 综合分析**：详细的统计分析和可视化报告
- **🎯 多模型评估**：支持同时评估多个AI模型
- **⚙️ 灵活配置**：可自定义模型、投票策略和评估参数
- **📈 丰富可视化**：自动生成性能图表和比较分析
- **🔧 模块化设计**：不同评估阶段的独立模块
- **📋 标准化输出**：一致的Excel报告和详细指标

## 快速开始

### 安装

```bash
# 克隆仓库
git clone <repository-url>
cd medical-ai-bench-eval

# 安装依赖
pip install -r requirements.txt
```

### 基本使用

```bash
# 运行完整评估流程
python medical_evaluation_pipeline.py input_data.xlsx

# 指定自定义输出文件
python medical_evaluation_pipeline.py input_data.xlsx -o results/evaluation_results.xlsx

# 启用详细日志
python medical_evaluation_pipeline.py input_data.xlsx -v
```

## 系统架构

该系统专为自动评估医疗问答AI模型回复而设计，通过多轮审查流程确保准确性和可靠性。系统支持包括GPT-5、Gemini-2.5-Pro、Claude-Opus-4等多种AI模型的专业医疗内容评估。

### 核心功能

- **多模型审查**：使用多个AI模型对每个评估点进行Met/Not Met判断
- **无关内容检测**：自动识别和评估回复中的无关医疗内容
- **智能评分系统**：基于A类正分点（A1-A3）和S类负分点（S1-S4）
- **并行处理**：支持步骤并行执行，显著提升处理效率
- **详细统计报告**：生成可视化分析报告和性能对比数据



### 系统流程图

```
📊 输入Excel文件
    ↓
┌─────────────────────────────────────────────────────────┐
│                    🔄 并行处理阶段                        │
├──────────────────────────┬──────────────────────────────┤
│    📋 步骤1：Met审查      │    🔍 步骤2：无关内容检测        │
│    • 多模型审查           │    • 内容提取                  │
│    • 投票决策             │    • 级别评估                  │
│    • 结果汇总             │    • 投票分类                  │
└──────────────────────────┴──────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│                    🔗 结果合并                           │
│    • 智能合并并行结果                                      │
│    • 数据完整性检查                                       │
│    • 冲突解决处理                                         │ 
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│                  🧮 步骤3：分数计算                       │
│    • 多维度分数统计                                       │
│    • 无关内容扣分                                         │
│    • 归一化处理                                           │
│    • 性能指标生成                                         │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│               📈 步骤4：数据分析与可视化                   │
│    • 统计分析报告                                         │
│    • 多样化图表生成                                       │
│    • CSV数据导出                                         │
│    • 性能对比分析                                         │
└─────────────────────────────────────────────────────────┘
    ↓
📋 输出Excel文件 + 📊 分析报告
```

### 🔧 架构特性

- **⚡ 并行处理**：步骤1和步骤2同时执行，显著提升处理效率
- **🎯 多模型支持**：同时使用多个AI模型进行交叉验证  
- **📊 智能评分**：基于A类正分点和S类负分点的综合评估
- **🔍 无关内容检测**：自动识别和扣分医疗回复中的无关内容
- **📈 可视化分析**：生成详细的性能图表和统计报告


## 快速开始

### 环境要求
- **Python**: 3.12+
- **操作系统**: Windows、macOS、Linux
- **核心依赖**: pandas、numpy、matplotlib、seaborn、asyncio、langchain、openpyxl、xlsxwriter

### 安装步骤

1. **克隆仓库**:
```bash
git clone <repository-url>
cd medical-ai-bench-eval
```

2. **安装依赖**:
```bash
pip install -r requirements.txt
```

3. **配置API密钥**（如果使用外部AI模型服务）：

   ### API配置指南

   #### 环境变量设置

   **Linux/Mac:**
   ```bash
   # OpenAI
   export OPENAI_API_KEY="sk-your-actual-key"
   export OPENAI_BASE_URL="https://api.openai.com/v1"

   # Claude (Anthropic)
   export ANTHROPIC_API_KEY="sk-ant-your-actual-key"
   export ANTHROPIC_BASE_URL="https://api.anthropic.com"

   # Google Gemini
   export GOOGLE_API_KEY="your-google-api-key"
   export GOOGLE_BASE_URL="https://generativelanguage.googleapis.com/v1beta"

   # Moonshot Kimi
   export MOONSHOT_API_KEY="sk-your-moonshot-key"
   export MOONSHOT_BASE_URL="https://api.moonshot.cn/v1"

   # 阿里巴巴通义千问
   export DASHSCOPE_API_KEY="your-dashscope-key"
   export DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/api/v1"

   # 百川
   export BAICHUAN_API_KEY="your-baichuan-key"
   export BAICHUAN_BASE_URL="https://api.baichuan-ai.com/v1"

   # DeepSeek
   export DEEPSEEK_API_KEY="sk-your-deepseek-key"
   export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"

   # 智谱ChatGLM
   export ZHIPU_API_KEY="your-zhipu-key"
   export ZHIPU_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
   ```

   **Windows PowerShell:**
   ```powershell
   $Env:OPENAI_API_KEY="sk-your-actual-key"
   $Env:OPENAI_BASE_URL="https://api.openai.com/v1"
   ```

   #### 模型配置

   **⚠️ 重要提示：仅支持OpenAI兼容API**
   
   本系统目前**仅支持OpenAI兼容的API接口**。所有模型都必须提供OpenAI兼容的端点，无论实际提供商是谁。

   **🌐 第三方多模型平台（推荐）**
   
   对于原生不支持OpenAI兼容API的模型（如Claude、Gemini），您可以使用提供统一OpenAI兼容访问的第三方平台：
   
   - **[OpenRouter](https://openrouter.ai/)** - 通过OpenAI兼容API访问Claude、Gemini、GPT等多种模型
   - **[Together AI](https://together.ai/)** - 各种开源和商业模型
   - **[Anyscale](https://anyscale.com/)** - 通过OpenAI兼容端点访问多个LLM

   编辑 `config_model.yaml` 配置您偏好的模型：

   ```yaml
   models:
     m1:  # OpenAI GPT-4 (原生)
       api_key_env: "OPENAI_API_KEY"
       api_base_env: "OPENAI_BASE_URL"
       model: "gpt-4-turbo-preview"
       temperature: 0.2
       max_tokens: 4000

     m2:  # Kimi (OpenAI兼容)
       api_key_env: "MOONSHOT_API_KEY"
       api_base_env: "MOONSHOT_BASE_URL"
       model: "kimi-latest"
       temperature: 0.2
       max_tokens: 4000

     m3:  # 通义千问 (OpenAI兼容)
       api_key_env: "DASHSCOPE_API_KEY"
       api_base_env: "DASHSCOPE_BASE_URL"
       model: "qwen-max"
       temperature: 0.1
       max_tokens: 4000

     m4:  # DeepSeek (OpenAI兼容)
       api_key_env: "DEEPSEEK_API_KEY"
       api_base_env: "DEEPSEEK_BASE_URL"
       model: "deepseek-chat"
       temperature: 0.2
       max_tokens: 4000

     m5:  # 本地模型 (通过OpenAI兼容服务器)
       api_key_env: "LOCAL_API_KEY"
       api_base_env: "LOCAL_BASE_URL"
       model: "llama3-medical"
       temperature: 0.2
       max_tokens: 4000

     # OpenRouter 示例 (取消注释以使用)
     # m6:  # 通过OpenRouter使用Claude
     #   api_key_env: "OPENROUTER_API_KEY"
     #   api_base_env: "OPENROUTER_BASE_URL"  # https://openrouter.ai/api/v1
     #   model: "anthropic/claude-3-5-sonnet-20241022"
     #   temperature: 0.2
     #   max_tokens: 4000

     # m7:  # 通过OpenRouter使用Gemini
     #   api_key_env: "OPENROUTER_API_KEY"
     #   api_base_env: "OPENROUTER_BASE_URL"  # https://openrouter.ai/api/v1
     #   model: "google/gemini-pro-1.5"
     #   temperature: 0.1
     #   max_tokens: 4000
   ```

   #### 支持与不支持的提供商

   | 提供商 | 状态 | API类型 | 备注 |
   |--------|------|---------|------|
   | **OpenAI** | ✅ 支持 | 原生OpenAI | 直接支持 |
   | **OpenRouter** | ✅ 支持 | 多模型平台 | 通过OpenAI兼容API访问Claude、Gemini、GPT等 |
   | **Together AI** | ✅ 支持 | 多模型平台 | 通过OpenAI兼容API访问各种模型 |
   | **Anyscale** | ✅ 支持 | 多模型平台 | 通过OpenAI兼容API访问多个LLM |
   | **Kimi/月之暗面** | ✅ 支持 | OpenAI兼容 | 通过兼容端点 |
   | **通义千问/DashScope** | ✅ 支持 | OpenAI兼容 | 通过兼容端点 |
   | **DeepSeek** | ✅ 支持 | OpenAI兼容 | 通过兼容端点 |
   | **百川智能** | ✅ 支持 | OpenAI兼容 | 通过兼容端点 |
   | **智谱AI** | ✅ 支持 | OpenAI兼容 | 通过兼容端点 |
   | **Claude/Anthropic** | ⚠️ 通过OpenRouter | 原生Anthropic API | 使用OpenRouter获得OpenAI兼容访问 |
   | **Gemini/Google** | ⚠️ 通过OpenRouter | 原生Google API | 使用OpenRouter获得OpenAI兼容访问 |

   #### 医疗模型推荐（仅OpenAI兼容）

   | 使用场景 | 推荐模型 | 温度参数 | 备注 |
   |----------|----------|----------|------|
   | **诊断任务** | gpt-4-turbo, deepseek-chat | 0.1-0.2 | 高准确性 |
   | **中文医疗** | qwen-max, baichuan-medical | 0.2-0.3 | 更好的CJK支持 |
   | **成本效益** | deepseek-chat, kimi | 0.2-0.3 | 良好平衡 |
   | **实时响应** | kimi, deepseek-chat | 0.1-0.2 | 快速响应 |
   | **隐私保护** | local-llama3-medical | 0.2-0.3 | 通过OpenAI兼容服务器本地部署 |

   #### 快速模型设置命令

   **GPT-4测试：**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   # 使用GPT-4运行
   python medical_evaluation_pipeline.py input.xlsx --judge-models m1
   ```

   **中文医疗模型：**
   ```bash
   export DASHSCOPE_API_KEY="your-key-here"
   # 使用通义千问
   python medical_evaluation_pipeline.py input.xlsx --judge-models m4
   ```

   **混合模型评估：**
   ```bash
   export OPENAI_API_KEY="your-key"
   export DASHSCOPE_API_KEY="your-key"
   # 使用GPT-4和通义千问进行评估
   python medical_evaluation_pipeline.py input.xlsx \
     --judge-models m1 m4 \
     --extract-model m5

### 基本用法

1. **准备输入数据**：
   - Excel文件格式
   - 包含问题、评分标准（JSON格式）、模型回复等列
   - 默认列名可在 `config.yaml` 中配置

2. **运行完整评估流程**：
```bash
python medical_evaluation_pipeline.py input.xlsx -o output.xlsx
```

3. **查看结果**：
   - 输出Excel文件包含详细的审查结果和分数
   - 数据分析报告保存在 `data/output/analysis/` 目录

## ⚙️ 系统配置

### 配置文件 (config.yaml)

```yaml
# 文件路径配置
files:
  input_file: "data/medical_evaluation_result.xlsx"
  output_file: "data/output/processed_result.xlsx"

# 流程控制
pipeline:
  disable_met_nomet: false          # 是否禁用Met审查
  disable_irrelevant_extraction: false  # 是否禁用无关内容检测
  exclude_irrelevant_scoring: false     # 是否从评分中排除无关内容
  disable_data_analysis: false          # 是否禁用数据分析
  analysis_config_file: "config_visualization.yaml"

# 模型配置
models:
  judge_models: ["m1", "m2", "m3"]      # Met审查模型
  extract_model: "m5"                   # 无关内容提取模型
  grade_models: ["m1", "m2", "m3"]      # 无关内容评分模型
  voting_strategy: "conservative"       # 投票策略

# 列名映射
columns:
  question_col: "question"
  rubric_col: "final_merged_json"
  answer_columns:
    - "gpt_5_answer"
    - "gemini_2_5_pro_answer"
    - "claude_opus_4_answer"

# 评分系统
point:
  A1: 5
  A2: 3
  A3: 1
  S1: -1
  S2: -2
  S3: -3
  S4: -4
```

### 命令行参数

```bash
# 流程控制
--disable-met-nomet          # 跳过Met审查步骤
--disable-irrelevant         # 跳过无关内容检测
--exclude-irrelevant-scoring # 从评分中排除无关内容扣分
--disable-data-analysis      # 跳过数据分析

# 模型配置
--judge-models m1 m2         # 指定Met审查模型
--extract-model m3           # 指定无关内容提取模型
--grade-models m1 m2 m4      # 指定无关内容评分模型
--voting-strategy majority   # 投票策略: conservative/majority/average

# 数据列配置
--question-col "问题"             # 问题列名
--rubric-col "评估要点"           # 评估要点列名
--answer-columns "回复1" "回复2" "回复3"  # 模型回复列名
```

## 📊 胸外科评测数据集

### 数据集概述

我们提供了一个专门的**胸外科评测数据集** (`data/input/GAPS-NSCLC-preview.xlsx`)，包含92个精心策划的临床案例，用于评估AI模型在胸外科场景中的表现。该数据集专注于胸外科的复杂临床决策，特别是非小细胞肺癌(NSCLC)的分期和治疗规划。

### 数据集结构

| 列名 | 描述                  | 数据类型 |
|-------------|---------------------|-----------|
| **question** | 涵盖胸外科场景的临床问题        | 文本 |
| **分类** | 医学专科分类              | 文本 |
| **rubrics** | JSON格式的评估标准，包含评分等级  | JSON数组 |
| **gpt_5_answer** | GPT-5模型对临床问题的回答     | 文本 |
| **gemini_2_5_pro_answer** | Gemini 2.5 Pro模型的回答 | 文本 |
| **claude_opus_4_answer** | Claude Opus模型的回答    | 文本 |

### 临床重点领域

数据集涵盖胸外科的关键方面，包括：

- **术前评估**：NSCLC患者(IIB-IIIA期)的综合评估方案
- **诊断程序**：EBUS-TBNA、纵隔镜检查、PET-CT解读
- **分期评估**：TNM分期、纵隔淋巴结评估
- **治疗规划**：手术vs非手术方法、新辅助治疗决策
- **风险评估**：肺功能评估、心脏风险分层
- **分子诊断**：EGFR、ALK、PD-L1检测策略

### 评估标准格式

每个问题都包含JSON格式的详细评估标准：

```json
[
  {
    "id": 1,
    "claim": "应进行覆盖胸廓入口至上腹部的增强胸部CT",
    "level": "A1",
    "type": "positive"
  },
  {
    "id": 2,
    "claim": "PET-CT对准确N分期和排除远处转移至关重要",
    "level": "A2", 
    "type": "positive"
  },
  {
    "id": 3,
    "claim": "错误地将上沟瘤MRI要求泛化到所有IIB/IIIA期患者",
    "level": "S2",
    "type": "negative"
  }
]
```

**评分等级**：
- **A1 (5分)**：影响患者安全的关键医学知识
- **A2 (3分)**：重要的临床考虑因素
- **A3 (1分)**：额外的相关信息
- **S1 (-1分)**：不影响核心治疗的轻微错误
- **S2 (-2分)**：可能误导的错误信息
- **S3 (-3分)**：严重的医疗错误
- **S4 (-4分)**：可能伤害患者的危险错误信息

### 临床问题示例

**问题**："对于IIB-IIIA期NSCLC患者，应进行哪些全面的治疗前评估？"

**关键评估要点**：
- 病理诊断和分子特征分析
- 准确的临床分期（T、N、M评估）
- N2评估的侵入性纵隔分期
- 肺功能和心功能评估
- 多学科团队(MDT)治疗规划

### 与GAPS框架的使用

该数据集设计为与GAPS评估流程无缝配合：

```bash
# 评估胸外科数据集
python medical_evaluation_pipeline.py data/input/GAPS-NSCLC-preview.xlsx \
  --judge-models m1 m2 m3 \
  --voting-strategy conservative \
  -o results/thoracic_surgery_evaluation.xlsx
```

### 临床验证

数据集已经过以下专家验证：
- **认证胸外科医师**
- **肺肿瘤科医师**
- **医学影像专家**
- **肺癌病理专家**

所有评估标准均基于当前临床指南，包括：
- NCCN非小细胞肺癌指南
- ESTS术中淋巴结分期指南
- IASLC胸部肿瘤学分期手册

### 研究应用

该数据集支持以下研究：
- **AI临床决策支持**：评估AI模型提供准确临床建议的能力
- **医学教育**：临床推理技能的培训和评估
- **质量保证**：根据既定临床标准对AI系统进行基准测试
- **比较分析**：专业医学领域的跨模型性能评估

### 数据质量指标

- **总案例数**：92个临床场景
- **完整性**：所有列100%数据覆盖
- **临床多样性**：涵盖IIB-IIIA期NSCLC的全谱表现
- **专家验证**：所有案例均经多学科临床团队审核

---

## 输入数据格式

### Excel文件结构

| 列名 | 描述 | 示例 |
|-------------|-------------|---------|
| question | 医疗问题 | "患者表现为胸痛症状，如何诊断？" |
| final_merged_json | 评估要点JSON | [{"id":1,"claim":"需要询问症状","level":"A1"}] |
| gpt_5_answer | GPT模型回复 | "首先需要详细询问患者症状..." |
| gemini_2_5_pro_answer | Gemini模型回复 | "建议进行心电图检查..." |
| claude_opus_4_answer | Claude模型回复 | "应考虑急性冠状动脉综合征..." |

### 评估要点JSON格式

```json
[
  {
    "id": 1,
    "claim": "需要询问症状持续时间",
    "level": "A1",
    "desc": "详细询问胸痛持续时间、性质等"
  },
  {
    "id": 2,
    "claim": "应避免提及无关治疗方案",
    "level": "S2",
    "desc": "不应提及与胸痛无关的治疗"
  }
]
```

**级别说明**：
- **A1-A3**：正分点（A1=5分，A2=3分，A3=1分）
- **S1-S4**：负分点（S1=-1分，S2=-2分，S3=-3分，S4=-4分）

## 输出结果

### 主要输出文件

1. **最终分数Excel** (`processed_result_final_YYYYMMDD_HHMMSS.xlsx`)
   - 包含所有原始数据
   - Met/Not Met审查结果
   - 无关内容检测结果
   - 详细评分统计

2. **数据分析报告** (`data/output/analysis/`)
   - `medical_evaluation_report_YYYYMMDD_HHMMSS.png` - 可视化图表
   - `medical_analysis_report_YYYYMMDD_HHMMSS.txt` - 详细分析报告
   - `model_performance_summary_YYYYMMDD_HHMMSS.csv` - 性能汇总

### 评分指标说明

| 指标 | 描述 |
|--------|-------------|
| max_possible | 理论最高分（所有正分点总和） |
| final_total_score | 实际得分（命中项得分-无关内容扣分） |
| normalized | 归一化分数（0-1之间） |
| positive_total_count | 正分点命中数量 |
| rubric_total_count | 负分点命中数量 |
| irrelevant_total_count | 无关内容总数 |

## 高级功能

### 1. 并行处理优化

系统支持步骤1（Met审查）和步骤2（无关内容检测）的并行执行：

```bash
# 启用所有步骤（自动并行）
python medical_evaluation_pipeline.py input.xlsx

# 仅启用Met审查
python medical_evaluation_pipeline.py input.xlsx --disable-irrelevant

# 仅启用无关内容检测
python medical_evaluation_pipeline.py input.xlsx --disable-met-nomet
```

### 2. 投票策略

支持处理多模型结果的三种投票策略：
- **conservative**：保守策略，优先考虑更严重的评级
- **majority**：多数投票，选择得票最多的结果
- **average**：平均策略，基于数值平均计算

```bash
python medical_evaluation_pipeline.py input.xlsx --voting-strategy conservative
```

### 3. 自定义模型配置

```bash
# 使用特定审查模型组合
python medical_evaluation_pipeline.py input.xlsx \
  --judge-models m1 m2 \
  --extract-model m5 \
  --grade-models m1 m3 m4
```

### 4. 数据分析自定义

创建 `config_visualization.yaml` 进行自定义分析配置：

```yaml
analysis:
  input_file: "data/processed_result.xlsx"
  columns:
    model_scores:
      GPT-5: "gpt_5_answer_judged_json_scores"
      Gemini-2.5-Pro: "gemini_2_5_pro_answer_judged_json_scores"
      Claude-Opus-4: "claude_opus_4_answer_judged_json_scores"

visualization:
  charts:
    bar_overall: true
    boxplot_distribution: true
    heatmap_category: true
    radar_chart: true
  style:
    figure_size: [24, 16]
    dpi: 300
```

## 🔧 独立模块使用

### 1. 单独运行Met审查

```python
import asyncio
from clinical_answer_judge import MultiModelMergedJsonJudge

async def run_judge():
    judge = MultiModelMergedJsonJudge(
        judge_models=['m1', 'm2'],
        question_col='question',
        rubric_col='rubrics'
    )
    result = await judge.process_excel_file('input.xlsx', 'output.xlsx')
    return result

# 运行异步函数
result = asyncio.run(run_judge())
```

### 2. 单独运行分数计算

```python
from clinical_scoring_calculator import process_excel_data

result = process_excel_data(
    input_file='judged_data.xlsx',
    output_file='scored_data.xlsx',
    model_columns=['gpt_5_answer_judged_json']
)
```

### 3. 单独运行数据分析

```python
from enhanced_analyzer import EnhancedMedicalAnalyzer

analyzer = EnhancedMedicalAnalyzer('config_visualization.yaml')
analyzer.run_analysis()
```

## 使用示例

### 示例1：完整流程处理

```bash
# 处理完整医疗评估数据
python medical_evaluation_pipeline.py medical_data.xlsx \
  -o results/final_report.xlsx \
  --judge-models m1 m2 m3 \
  --voting-strategy conservative \
  -v
```

### 示例2：快速测试

```bash
# 仅处理前10行数据
python medical_evaluation_pipeline.py test_data.xlsx \
  --max_rows 10 \
  --disable-data-analysis
```

### 示例3：自定义列名

```bash
# 使用中文列名
python medical_evaluation_pipeline.py data.xlsx \
  --question-col "临床问题" \
  --rubric-col "评分标准" \
  --answer-columns "GPT回复" "Claude回复"
```

## 故障排除

### 常见问题

1. **文件未找到错误**
   - 解决方案：检查输入文件路径是否正确

2. **列名不匹配**
   - 解决方案：使用 `--question-col`、`--rubric-col` 等参数指定正确列名

3. **内存不足**
   - 解决方案：使用 `--max_rows` 参数限制处理行数

4. **API调用失败**
   - 解决方案：检查模型配置和网络连接

### 调试模式

```bash
# 启用详细日志查看处理详情
python medical_evaluation_pipeline.py input.xlsx -v

# 保留临时文件用于调试
# 修改代码中的 cleanup() 调用
```

## 技术文档

### 核心模块

- `medical_evaluation_pipeline.py` - 主流程控制器
- `clinical_answer_judge.py` - Met/Not Met审查模块
- `clinical_scoring_calculator.py` - 分数计算模块
- `enhanced_analyzer.py` - 数据分析和可视化模块
- `judge_engine.py` - 审查引擎
- `irrelevant_content_grading.py` - 无关内容评分模块
- `extract_irrelevant_content.py` - 无关内容提取模块
- `general_negative_points.py` - 负分点处理模块

### 文件结构

```
medical-ai-bench-eval/
├── clinical_answer_judge.py      # 多模型审查处理器
├── clinical_scoring_calculator.py # 分数计算器
├── medical_evaluation_pipeline.py # 主流程控制器
├── enhanced_analyzer.py          # 数据分析器
├── judge_engine.py              # 审查引擎
├── irrelevant_content_grading.py # 无关内容评分
├── extract_irrelevant_content.py # 无关内容提取
├── general_negative_points.py   # 负分点处理
├── config.yaml                  # 主配置文件
├── config_model.yaml           # 模型配置文件
├── config_visualization.yaml   # 可视化配置
├── requirements.txt            # 依赖列表
└── data/                       # 数据目录
    ├── input/                  # 输入文件
    │   ├── GAPS-NSCLC-preview.xlsx  # 胸外科评测数据集 (92个案例)
    │   └── community_contributions.xlsx       # 社区贡献案例
    └── output/                 # 输出文件
        └── analysis/           # 分析报告
```

### 数据流程

1. **输入阶段**：读取Excel文件，验证数据格式
2. **并行处理**：同时执行Met审查和无关内容检测
3. **结果合并**：智能合并两个并行步骤的输出
4. **分数计算**：基于合并结果计算多维度分数
5. **分析输出**：生成统计报告和可视化图表

### 性能优化

- 异步并行处理提升效率
- 批处理减少API调用频率
- 智能重试机制处理网络异常
- 内存优化处理大文件

## 贡献指南

欢迎提交Issues和Pull Requests来改进系统功能。

### 开发环境设置

```bash
git clone <repository>
cd medical-ai-bench-eval
pip install -r requirements.txt
```

### 代码标准

- 遵循PEP 8编码标准
- 添加详细文档字符串
- 包含单元测试
- 更新README文档

## 🤝 社区共创 / Community Contribution

我们欢迎医疗AI社区的贡献，共同扩展和改进我们的评估数据集！您的专业知识将帮助构建更全面的医疗AI系统基准测试。

### 📋 如何贡献

#### 方式一：提交Issue
使用标签 `data-contribution` 创建新的Issue，请使用以下模板：

```markdown
**医疗问题**
[在此提供您的临床问题]

**评估要点（JSON格式）**
```json
[
  {
    "id": 1,
    "claim": "您的评估标准描述",
    "level": "A1|A2|A3|S1|S2|S3|S4",
    "type": "positive|negative"
  },
  {
    "id": 2,
    "claim": "另一个评估标准",
    "level": "A2",
    "type": "positive"
  }
]
```

**医学专科**
[例如：心内科、呼吸科、肿瘤科等]

**问题类型**
[例如：诊断、治疗、风险评估等]

**补充说明**
[任何相关的临床背景或参考文献]
```

#### 方式二：提交Pull Request
1. Fork本仓库
2. 将您的数据添加到 `data/input/community_contributions.xlsx`，遵循现有格式：
   - **question**: 您的医疗问题
   - **rubrics**: 评估标准JSON数组
   - **specialty**: 医学专科领域
   - **difficulty**: 简单/中等/困难
   - **source**: 您的姓名/机构（可选）

3. 确保您的贡献遵循以下指导原则：
   - **临床相关性**：问题应反映真实世界的医疗场景
   - **循证医学**：评估标准应基于已确立的医疗指南
   - **清晰评分**：正确使用我们的评分系统：
     - **正分点**：A1（5分）、A2（3分）、A3（1分）
     - **负分点**：S1（-1分）、S2（-2分）、S3（-3分）、S4（-4分）

### 📝 贡献指南

#### 评估标准设计
- **A1（关键，5分）**：可能影响患者安全的基本医学知识
- **A2（重要，3分）**：重要的临床考虑因素
- **A3（有用，1分）**：额外的相关信息
- **S1（轻微错误，-1分）**：不影响核心治疗的小错误
- **S2（中等错误，-2分）**：可能误导的错误信息
- **S3（重大错误，-3分）**：严重的医疗错误
- **S4（严重错误，-4分）**：可能伤害患者的危险错误信息

#### 质量标准
- 问题应该**临床真实**并基于实际医疗场景
- 评估标准必须**基于证据**并参考当前医疗指南
- 每个问题应有**3-8个评估点**以实现平衡评估
- 包括**正向标准**（应该提及的内容）和**负向标准**（应该避免的内容）

### 🎯 优先领域
我们特别欢迎以下领域的贡献：
- **罕见疾病**：挑战AI系统的罕见病例
- **多学科病例**：需要多个专科的复杂病例
- **文化考量**：反映不同患者群体的病例
- **急诊医学**：时间关键的决策场景
- **儿科医学**：年龄特异性医疗考虑

### 📊 数据格式示例
```json
{
  "question": "65岁患者出现胸痛和呼吸困难，您如何进行初步评估？",
  "rubrics": [
    {
      "id": 1,
      "claim": "应获得详细病史，包括疼痛特征、时间和伴随症状",
      "level": "A1",
      "type": "positive"
    },
    {
      "id": 2,
      "claim": "必须进行心电图和胸部X光作为初步诊断检查",
      "level": "A1", 
      "type": "positive"
    },
    {
      "id": 3,
      "claim": "在急性表现中不应延误评估进行不必要的检查",
      "level": "S2",
      "type": "negative"
    }
  ],
  "specialty": "急诊医学",
  "difficulty": "中等"
}
```

### 🔄 审核流程
1. **社区审核**：贡献将由医疗专业人员审核
2. **质量检查**：确保临床准确性和适当难度
3. **整合**：批准的贡献将合并到主数据集
4. **致谢**：贡献者将在我们的贡献者名单中得到认可

### 📞 联系方式
如有贡献相关问题，请：
- 使用 `question` 标签开启Issue
- 在GitHub Discussions部分参与讨论

感谢您帮助构建更好的医疗AI评估基准！🙏

---

## 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件。
