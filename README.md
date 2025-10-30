# Medical AI Evaluation Framework: Clinical Benchmark Dataset and Automated Assessment Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Basic Usage](#basic-usage)
- [System Architecture](#system-architecture)
- [Data Format](#data-format)
  - [Input Format](#input-format)
  - [Output Format](#output-format)
- [Configuration](#configuration)
  - [Basic Configuration](#basic-configuration)
  - [Advanced Configuration](#advanced-configuration)
- [Usage Guide](#usage-guide)
  - [Command Line Interface](#command-line-interface)
  - [Python API](#python-api)
  - [Examples](#examples)
- [Evaluation Framework](#evaluation-framework)
  - [Scoring System](#scoring-system)
  - [Evaluation Metrics](#evaluation-metrics)
- [Dataset](#dataset)
  - [Thoracic Surgery Dataset](#thoracic-surgery-dataset)
  - [Data Quality](#data-quality)
- [Advanced Features](#advanced-features)
  - [Parallel Processing](#parallel-processing)
  - [Voting Strategies](#voting-strategies)
  - [Custom Models](#custom-models)
- [Development](#development)
  - [Technical Documentation](#technical-documentation)
  - [API Reference](#api-reference)
  - [Troubleshooting](#troubleshooting)
- [Community](#community)
  - [Contributing](#contributing)
  - [Citation](#citation)
- [License](#license)

## Overview

This Medical AI Evaluation Framework provides a comprehensive evaluation system designed specifically for assessing AI models in clinical scenarios. Based on the GAPS (Grounded, Automated, Personalized, Scalable) methodology, this framework includes both a curated clinical benchmark dataset and an automated assessment pipeline for medical AI systems.

The framework addresses the critical need for standardized evaluation of AI clinical decision-making by providing:
- **Clinically Grounded Assessment**: Evaluation criteria based on real medical guidelines and expert knowledge
- **Automated Pipeline**: Streamlined processing from raw responses to detailed performance metrics
- **Multi-Model Support**: Simultaneous evaluation of multiple AI models with comparative analysis
- **Scalable Architecture**: Efficient processing of large datasets with parallel execution capabilities

## Key Features

- **🏥 Medical-Specific Evaluation**: Specialized rubrics for clinical scenarios with positive/negative scoring
- **🔄 Parallel Processing**: Simultaneous execution of Met/Not Met review and irrelevant content detection
- **📊 Comprehensive Analytics**: Detailed statistical analysis with visualization reports
- **🎯 Multi-Model Assessment**: Support for evaluating multiple AI models simultaneously
- **⚙️ Flexible Configuration**: Customizable models, voting strategies, and evaluation parameters
- **📈 Rich Visualization**: Automated generation of performance charts and comparative analysis
- **🔧 Modular Design**: Independent modules for different evaluation stages
- **📋 Standardized Output**: Consistent Excel-based reporting with detailed metrics

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd medical-ai-bench-eval

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run complete evaluation pipeline
python medical_evaluation_pipeline.py input_data.xlsx

# With custom output file
python medical_evaluation_pipeline.py input_data.xlsx -o results/evaluation_results.xlsx

# Enable verbose logging
python medical_evaluation_pipeline.py input_data.xlsx -v
```

## System Architecture

The system processes medical AI responses through a sophisticated pipeline that includes:

1. **Input Processing**: Reads Excel files containing medical questions, evaluation rubrics, and AI model responses
2. **Parallel Evaluation**: Simultaneously executes Met/Not Met review and irrelevant content detection
3. **Intelligent Scoring**: Calculates comprehensive scores based on clinical evaluation criteria
4. **Analysis & Reporting**: Generates detailed statistical reports and visualizations

## System Architecture

```
Input Excel File
↓
┌─────────────────────────────────────────┐
│          Parallel Processing Phase       │
├─────────────────┬─────────────────────┤
│   Step 1: Met Review │  Step 2: Irrelevant Content │
│   - Multi-model Review │  - Content Extraction     │
│   - Voting Decision    │  - Level Assessment       │
│   - Result Summary     │  - Voting Classification  │
└─────────────────┴─────────────────────┘
↓
┌─────────────────────────────────────────┐
│          Result Merging                 │
│   - Intelligent merging of parallel results │
│   - Data integrity check                │
└─────────────────────────────────────────┘
↓
┌─────────────────────────────────────────┐
│        Step 3: Score Calculation        │
│   - Multi-dimensional score statistics  │
│   - Irrelevant content deduction        │
│   - Normalization processing            │
└─────────────────────────────────────────┘
↓
┌─────────────────────────────────────────┐
│      Step 4: Data Analysis & Visualization │
│   - Statistical analysis reports        │
│   - Diverse charts                      │
│   - CSV data export                     │
└─────────────────────────────────────────┘
↓
Output Excel File + Analysis Report
```

## Data Format

### Input Format

The system accepts Excel files with the following structure:

| Column Name | Description | Example |
|-------------|-------------|---------|
| question | Medical question | "Patient presents with chest pain symptoms, how to diagnose?" |
| final_merged_json | Evaluation points JSON | [{"id":1,"claim":"Need to inquire about symptoms","level":"A1"}] |
| gpt_5_answer | GPT model response | "First need to ask the patient about symptoms in detail..." |
| gemini_2_5_pro_answer | Gemini model response | "Recommend performing ECG examination..." |
| claude_opus_4_answer | Claude model response | "Should consider acute coronary syndrome..." |

#### Evaluation Points JSON Format

```json
[
  {
    "id": 1,
    "claim": "Need to ask about symptom duration",
    "level": "A1",
    "desc": "Detailed inquiry about chest pain duration, nature, etc."
  },
  {
    "id": 2,
    "claim": "Should avoid mentioning unrelated treatment plans",
    "level": "S2",
    "desc": "Should not mention treatments unrelated to chest pain"
  }
]
```

**Level Description**:
- **A1-A3**: Positive points (A1=5 points, A2=3 points, A3=1 point)
- **S1-S4**: Negative points (S1=-1 point, S2=-2 points, S3=-3 points, S4=-4 points)

### Output Format

The system generates multiple output files:

1. **Final Score Excel** (`processed_result_final_YYYYMMDD_HHMMSS.xlsx`)
   - Contains all original data
   - Met/Not Met review results
   - Irrelevant content detection results
   - Detailed scoring statistics

2. **Data Analysis Report** (`data/output/analysis/`)
   - `medical_evaluation_report_YYYYMMDD_HHMMSS.png` - Visualization charts
   - `medical_analysis_report_YYYYMMDD_HHMMSS.txt` - Detailed analysis report
   - `model_performance_summary_YYYYMMDD_HHMMSS.csv` - Performance summary

#### Scoring Metrics

| Metric | Description |
|--------|-------------|
| max_possible | Theoretical maximum score (sum of all positive points) |
| final_total_score | Actual score (Met items score - irrelevant content deduction) |
| normalized | Normalized score (between 0-1) |
| positive_total_count | Number of positive point hits |
| rubric_total_count | Number of negative point hits |
| irrelevant_total_count | Total irrelevant content count |

## Configuration

### Basic Configuration

### Environment Requirements
- **Python**: 3.12+
- **Operating System**: Windows, macOS, Linux
- **Core Dependencies**: pandas, numpy, matplotlib, seaborn, asyncio, langchain, openpyxl, xlsxwriter

### Installation Steps

1. **Clone the repository**:
```bash
git clone <repository-url>
cd medical-ai-bench-eval
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure API Keys** (if using external AI model services):

   ### API Configuration Guide

   #### Environment Variables Setup

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

   # Alibaba Qwen
   export DASHSCOPE_API_KEY="your-dashscope-key"
   export DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/api/v1"

   # Baichuan
   export BAICHUAN_API_KEY="your-baichuan-key"
   export BAICHUAN_BASE_URL="https://api.baichuan-ai.com/v1"

   # DeepSeek
   export DEEPSEEK_API_KEY="sk-your-deepseek-key"
   export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"

   # Zhipu ChatGLM
   export ZHIPU_API_KEY="your-zhipu-key"
   export ZHIPU_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
   ```

   **Windows PowerShell:**
   ```powershell
   $Env:OPENAI_API_KEY="sk-your-actual-key"
   $Env:OPENAI_BASE_URL="https://api.openai.com/v1"
   ```

   #### Model Configuration

   **⚠️ IMPORTANT: OpenAI-Compatible API Only**
   
   This system currently supports **ONLY OpenAI-compatible API interfaces**. All models must provide OpenAI-compatible endpoints, regardless of the actual provider.

   **🌐 Third-Party Multi-Model Platforms (Recommended)**
   
   For models that don't natively support OpenAI-compatible APIs (like Claude, Gemini), you can use third-party platforms that provide unified OpenAI-compatible access:
   
   - **[OpenRouter](https://openrouter.ai/)** - Access Claude, Gemini, GPT, and many other models via OpenAI-compatible API
   - **[Together AI](https://together.ai/)** - Various open-source and commercial models
   - **[Anyscale](https://anyscale.com/)** - Multiple LLMs via OpenAI-compatible endpoints

   Edit `config_model.yaml` to configure your preferred models:

   ```yaml
   models:
     m1:  # OpenAI GPT-4 (Native)
       api_key_env: "OPENAI_API_KEY"
       api_base_env: "OPENAI_BASE_URL"
       model: "gpt-4-turbo-preview"
       temperature: 0.2
       max_tokens: 4000

     m2:  # Kimi (OpenAI-Compatible)
       api_key_env: "MOONSHOT_API_KEY"
       api_base_env: "MOONSHOT_BASE_URL"
       model: "kimi-latest"
       temperature: 0.2
       max_tokens: 4000

     m3:  # Qwen (OpenAI-Compatible)
       api_key_env: "DASHSCOPE_API_KEY"
       api_base_env: "DASHSCOPE_BASE_URL"
       model: "qwen-max"
       temperature: 0.1
       max_tokens: 4000

     m4:  # DeepSeek (OpenAI-Compatible)
       api_key_env: "DEEPSEEK_API_KEY"
       api_base_env: "DEEPSEEK_BASE_URL"
       model: "deepseek-chat"
       temperature: 0.2
       max_tokens: 4000

     m5:  # Local Model (via OpenAI-Compatible Server)
       api_key_env: "LOCAL_API_KEY"
       api_base_env: "LOCAL_BASE_URL"
       model: "llama3-medical"
       temperature: 0.2
       max_tokens: 4000

     # OpenRouter Examples (uncomment to use)
     # m6:  # Claude via OpenRouter
     #   api_key_env: "OPENROUTER_API_KEY"
     #   api_base_env: "OPENROUTER_BASE_URL"  # https://openrouter.ai/api/v1
     #   model: "anthropic/claude-3-5-sonnet-20241022"
     #   temperature: 0.2
     #   max_tokens: 4000

     # m7:  # Gemini via OpenRouter
     #   api_key_env: "OPENROUTER_API_KEY"
     #   api_base_env: "OPENROUTER_BASE_URL"  # https://openrouter.ai/api/v1
     #   model: "google/gemini-pro-1.5"
     #   temperature: 0.1
     #   max_tokens: 4000
   ```

   #### Supported vs Unsupported Providers

   | Provider | Status | API Type | Notes |
   |----------|--------|----------|-------|
   | **OpenAI** | ✅ Supported | Native OpenAI | Direct support |
   | **OpenRouter** | ✅ Supported | Multi-Model Platform | Access Claude, Gemini, GPT via OpenAI-compatible API |
   | **Together AI** | ✅ Supported | Multi-Model Platform | Various models via OpenAI-compatible API |
   | **Anyscale** | ✅ Supported | Multi-Model Platform | Multiple LLMs via OpenAI-compatible API |
   | **Kimi/Moonshot** | ✅ Supported | OpenAI-Compatible | Via compatible endpoint |
   | **Qwen/DashScope** | ✅ Supported | OpenAI-Compatible | Via compatible endpoint |
   | **DeepSeek** | ✅ Supported | OpenAI-Compatible | Via compatible endpoint |
   | **Baichuan** | ✅ Supported | OpenAI-Compatible | Via compatible endpoint |
   | **Zhipu** | ✅ Supported | OpenAI-Compatible | Via compatible endpoint |
   | **Claude/Anthropic** | ⚠️ Via OpenRouter | Native Anthropic API | Use OpenRouter for OpenAI-compatible access |
   | **Gemini/Google** | ⚠️ Via OpenRouter | Native Google API | Use OpenRouter for OpenAI-compatible access |

   #### Medical Model Recommendations (OpenAI-Compatible Only)

   | Use Case | Recommended Models | Temperature | Notes |
   |----------|-------------------|-------------|--------|
   | **Diagnostic Tasks** | gpt-4-turbo, deepseek-chat | 0.1-0.2 | High accuracy |
   | **Chinese Medical** | qwen-max, baichuan-medical | 0.2-0.3 | Better CJK support |
   | **Cost-effective** | deepseek-chat, kimi | 0.2-0.3 | Good balance |
   | **Real-time** | kimi, deepseek-chat | 0.1-0.2 | Fast response |
   | **Privacy-focused** | local-llama3-medical | 0.2-0.3 | On-premise via OpenAI-compatible server |

   #### Quick Model Setup Commands

   **For GPT-4 testing:**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   # Run with GPT-4
   python medical_evaluation_pipeline.py input.xlsx --judge-models m1
   ```

   **For Chinese medical models:**
   ```bash
   export DASHSCOPE_API_KEY="your-key-here"
   # Run with Qwen
   python medical_evaluation_pipeline.py input.xlsx --judge-models m4
   ```

   **For mixed model evaluation:**
   ```bash
   export OPENAI_API_KEY="your-key"
   export DASHSCOPE_API_KEY="your-key"
   # Use GPT-4 and Qwen for evaluation
   python medical_evaluation_pipeline.py input.xlsx \
     --judge-models m1 m4 \
     --extract-model m5

### Basic Usage

1. **Prepare input data**:
   - Excel file format
   - Contains columns for questions, scoring criteria (JSON format), model responses, etc.
   - Default column names can be configured in `config.yaml`

2. **Run the complete evaluation pipeline**:
```bash
python medical_evaluation_pipeline.py input.xlsx -o output.xlsx
```

3. **View results**:
   - Output Excel file contains detailed review results and scores
   - Data analysis reports are saved in the `data/output/analysis/` directory

## ⚙️ System Configuration

### Configuration File (config.yaml)

```yaml
# File path configuration
files:
  input_file: "data/medical_evaluation_result.xlsx"
  output_file: "data/output/processed_result.xlsx"

# Process control
pipeline:
  disable_met_nomet: false          # Whether to disable Met review
  disable_irrelevant_extraction: false  # Whether to disable irrelevant content detection
  exclude_irrelevant_scoring: false     # Whether to exclude irrelevant content from scoring
  disable_data_analysis: false          # Whether to disable data analysis
  analysis_config_file: "config_visualization.yaml"

# Model configuration
models:
  judge_models: ["m1", "m2", "m3"]      # Met review models
  extract_model: "m5"                   # Irrelevant content extraction model
  grade_models: ["m1", "m2", "m3"]      # Irrelevant content grading models
  voting_strategy: "conservative"       # Voting strategy

# Column name mapping
columns:
  question_col: "question"
  rubric_col: "final_merged_json"
  answer_columns:
    - "gpt_5_answer"
    - "gemini_2_5_pro_answer"
    - "claude_opus_4_answer"

# Scoring system
point:
  A1: 5
  A2: 3
  A3: 1
  S1: -1
  S2: -2
  S3: -3
  S4: -4
```

### Command Line Arguments

```bash
# Process control
--disable-met-nomet          # Skip Met review step
--disable-irrelevant         # Skip irrelevant content detection
--exclude-irrelevant-scoring # Exclude irrelevant content deduction from scoring
--disable-data-analysis      # Skip data analysis

# Model configuration
--judge-models m1 m2         # Specify Met review models
--extract-model m3           # Specify irrelevant content extraction model
--grade-models m1 m2 m4      # Specify irrelevant content grading models
--voting-strategy majority   # Voting strategy: conservative/majority/average

# Data column configuration
--question-col "Question"         # Question column name
--rubric-col "Evaluation Points"  # Evaluation points column name
--answer-columns "Response1" "Response2" "Response3"  # Model response column names
```

## 📊 Thoracic Surgery Evaluation Dataset

### Dataset Overview

We provide a specialized **Thoracic Surgery Evaluation Dataset** (`data/input/specialty_evaluation_dataset.xlsx`) containing 92 carefully curated clinical cases for evaluating AI models' performance in thoracic surgery scenarios. This dataset focuses on complex clinical decision-making in chest surgery, particularly for non-small cell lung cancer (NSCLC) staging and treatment planning.

### Dataset Structure

| Column Name | Description | Data Type |
|-------------|-------------|-----------|
| **question** | Clinical questions covering thoracic surgery scenarios | Text |
| **分类** (Category) | Medical specialty classification | Text |
| **rubrics** | Evaluation criteria in JSON format with scoring levels | JSON Array |
| **gpt_5_answer** | GPT-4 model responses to clinical questions | Text |
| **gemini_2_5_pro_answer** | Gemini 2.5 Pro model responses | Text |
| **claude_opus_4_answer** | Claude Opus model responses | Text |

### Clinical Focus Areas

The dataset covers critical aspects of thoracic surgery, including:

- **Pre-operative Evaluation**: Comprehensive assessment protocols for NSCLC patients (IIB-IIIA staging)
- **Diagnostic Procedures**: EBUS-TBNA, mediastinoscopy, PET-CT interpretation
- **Staging Assessment**: TNM staging, mediastinal lymph node evaluation
- **Treatment Planning**: Surgical vs. non-surgical approaches, neoadjuvant therapy decisions
- **Risk Assessment**: Pulmonary function evaluation, cardiac risk stratification
- **Molecular Diagnostics**: EGFR, ALK, PD-L1 testing strategies

### Evaluation Rubrics Format

Each question includes detailed evaluation criteria in JSON format:

```json
[
  {
    "id": 1,
    "claim": "Should perform enhanced chest CT covering thoracic inlet to upper abdomen",
    "level": "A1",
    "type": "positive"
  },
  {
    "id": 2,
    "claim": "PET-CT is essential for accurate N-staging and excluding distant metastases",
    "level": "A2", 
    "type": "positive"
  },
  {
    "id": 3,
    "claim": "Incorrectly generalizing upper sulcus tumor MRI requirements to all IIB/IIIA patients",
    "level": "S2",
    "type": "negative"
  }
]
```

**Scoring Levels**:
- **A1 (5 points)**: Critical medical knowledge affecting patient safety
- **A2 (3 points)**: Important clinical considerations  
- **A3 (1 point)**: Additional relevant information
- **S1 (-1 point)**: Minor inaccuracies not affecting core treatment
- **S2 (-2 points)**: Incorrect information that could mislead
- **S3 (-3 points)**: Serious medical errors
- **S4 (-4 points)**: Dangerous misinformation that could harm patients

### Sample Clinical Question

**Question**: "For NSCLC patients with IIB-IIIA staging, what comprehensive pre-treatment evaluation should be performed?"

**Key Evaluation Points**:
- Pathological diagnosis and molecular characterization
- Accurate clinical staging (T, N, M assessment)
- Invasive mediastinal staging for N2 evaluation
- Pulmonary and cardiac function assessment
- Multidisciplinary team (MDT) treatment planning

### Usage with GAPS Framework

This dataset is designed to work seamlessly with the GAPS evaluation pipeline:

```bash
# Evaluate thoracic surgery dataset
python medical_evaluation_pipeline.py data/input/specialty_evaluation_dataset.xlsx \
  --judge-models m1 m2 m3 \
  --voting-strategy conservative \
  -o results/thoracic_surgery_evaluation.xlsx
```

### Clinical Validation

The dataset has been validated by:
- **Board-certified thoracic surgeons**
- **Pulmonary oncologists** 
- **Medical imaging specialists**
- **Pathologists specializing in lung cancer**

All evaluation criteria are based on current clinical guidelines including:
- NCCN Guidelines for Non-Small Cell Lung Cancer
- ESTS Guidelines for Intraoperative Lymph Node Staging
- IASLC Staging Manual in Thoracic Oncology

### Research Applications

This dataset enables research in:
- **AI Clinical Decision Support**: Evaluating AI models' ability to provide accurate clinical recommendations
- **Medical Education**: Training and assessment of clinical reasoning skills
- **Quality Assurance**: Benchmarking AI systems against established clinical standards
- **Comparative Analysis**: Cross-model performance evaluation in specialized medical domains

### Data Quality Metrics

- **Total Cases**: 92 clinical scenarios
- **Completeness**: 100% data coverage across all columns
- **Clinical Diversity**: Covers full spectrum of IIB-IIIA NSCLC presentations
- **Expert Validation**: All cases reviewed by multidisciplinary clinical team

---

## Input Data Format

### Excel File Structure

| Column Name | Description | Example |
|-------------|-------------|---------|
| question | Medical question | "Patient presents with chest pain symptoms, how to diagnose?" |
| final_merged_json | Evaluation points JSON | [{"id":1,"claim":"Need to inquire about symptoms","level":"A1"}] |
| gpt_5_answer | GPT model response | "First need to ask the patient about symptoms in detail..." |
| gemini_2_5_pro_answer | Gemini model response | "Recommend performing ECG examination..." |
| claude_opus_4_answer | Claude model response | "Should consider acute coronary syndrome..." |

### Evaluation Points JSON Format

```json
[
  {
    "id": 1,
    "claim": "Need to ask about symptom duration",
    "level": "A1",
    "desc": "Detailed inquiry about chest pain duration, nature, etc."
  },
  {
    "id": 2,
    "claim": "Should avoid mentioning unrelated treatment plans",
    "level": "S2",
    "desc": "Should not mention treatments unrelated to chest pain"
  }
]
```

**Level Description**:
- **A1-A3**: Positive points (A1=5 points, A2=3 points, A3=1 point)
- **S1-S4**: Negative points (S1=-1 point, S2=-2 points, S3=-3 points, S4=-4 points)

## Output Results

### Main Output Files

1. **Final Score Excel** (`processed_result_final_YYYYMMDD_HHMMSS.xlsx`)
   - Contains all original data
   - Met/Not Met review results
   - Irrelevant content detection results
   - Detailed scoring statistics

2. **Data Analysis Report** (`data/output/analysis/`)
   - `medical_evaluation_report_YYYYMMDD_HHMMSS.png` - Visualization charts
   - `medical_analysis_report_YYYYMMDD_HHMMSS.txt` - Detailed analysis report
   - `model_performance_summary_YYYYMMDD_HHMMSS.csv` - Performance summary

### Scoring Metrics Description

| Metric | Description |
|--------|-------------|
| max_possible | Theoretical maximum score (sum of all positive points) |
| final_total_score | Actual score (Met items score - irrelevant content deduction) |
| normalized | Normalized score (between 0-1) |
| positive_total_count | Number of positive point hits |
| rubric_total_count | Number of negative point hits |
| irrelevant_total_count | Total irrelevant content count |

## Advanced Features

### 1. Parallel Processing Optimization

The system supports parallel execution of Step 1 (Met Review) and Step 2 (Irrelevant Content Detection):

```bash
# Enable all steps (auto parallel)
python medical_evaluation_pipeline.py input.xlsx

# Enable only Met Review
python medical_evaluation_pipeline.py input.xlsx --disable-irrelevant

# Enable only Irrelevant Content Detection
python medical_evaluation_pipeline.py input.xlsx --disable-met-nomet
```

### 2. Voting Strategy

Supports three voting strategies for processing multi-model results:
- **conservative**: Conservative strategy, prioritizes more severe ratings
- **majority**: Majority voting, selects the result with the most votes
- **average**: Average strategy, calculates based on numerical average

```bash
python medical_evaluation_pipeline.py input.xlsx --voting-strategy conservative
```

### 3. Custom Model Configuration

```bash
# Use specific review model combinations
python medical_evaluation_pipeline.py input.xlsx \
  --judge-models m1 m2 \
  --extract-model m5 \
  --grade-models m1 m3 m4
```

### 4. Data Analysis Customization

Create `config_visualization.yaml` for custom analysis configuration:

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

## 🔧 Independent Module Usage

### 1. Run Met Review Separately

```python
import asyncio
from clinical_answer_judge import MultiModelMergedJsonJudge

async def run_judge():
    judge = MultiModelMergedJsonJudge(
        judge_models=['m1', 'm2', 'm3'],
        question_col='question',
        rubric_col='rubrics'
    )
    result = await judge.process_excel_file('input.xlsx', 'output.xlsx')
    return result

# Run the async function
result = asyncio.run(run_judge())
```

### 2. Run Score Calculation Separately

```python
from clinical_scoring_calculator import process_excel_data

result = process_excel_data(
    input_file='judged_data.xlsx',
    output_file='scored_data.xlsx',
    model_columns=['gpt_5_answer_judged_json']
)
```

### 3. Run Data Analysis Separately

```python
from enhanced_analyzer import EnhancedMedicalAnalyzer

analyzer = EnhancedMedicalAnalyzer('config_visualization.yaml')
analyzer.run_analysis()
```

## Usage Examples

### Example 1: Complete Process Handling

```bash
# Process complete medical evaluation data
python medical_evaluation_pipeline.py medical_data.xlsx \
  -o results/final_report.xlsx \
  --judge-models m1 m2 m3 \
  --voting-strategy conservative \
  -v
```

### Example 2: Quick Testing

```bash
# Process only first 10 rows of data
python medical_evaluation_pipeline.py test_data.xlsx \
  --max_rows 10 \
  --disable-data-analysis
```

### Example 3: Custom Column Names

```bash
# Use Chinese column names
python medical_evaluation_pipeline.py data.xlsx \
  --question-col "Clinical Question" \
  --rubric-col "Scoring Criteria" \
  --answer-columns "GPT Response" "Claude Response"
```

## Troubleshooting

### Common Issues

1. **File Not Found Error**
   - Solution: Check if the input file path is correct

2. **Column Name Mismatch**
   - Solution: Use `--question-col`, `--rubric-col` and other parameters to specify correct column names

3. **Insufficient Memory**
   - Solution: Use `--max_rows` parameter to limit the number of rows processed

4. **API Call Failure**
   - Solution: Check model configuration and network connection

### Debug Mode

```bash
# Enable verbose logging to view processing details
python medical_evaluation_pipeline.py input.xlsx -v

# Keep temporary files for debugging
# Modify the cleanup() call in the code
```

## Technical Documentation

### Core Modules

- `medical_evaluation_pipeline.py` - Main pipeline controller
- `clinical_answer_judge.py` - Met/Not Met review module
- `clinical_scoring_calculator.py` - Score calculation module
- `enhanced_analyzer.py` - Data analysis and visualization module
- `general_negative_points.py` - Irrelevant content processing module

### File Structure

```
MedicalAiBenchEval/
├── clinical_answer_judge.py      # Multi-model review processor
├── clinical_scoring_calculator.py # Score calculator
├── medical_evaluation_pipeline.py # Main pipeline controller
├── enhanced_analyzer.py          # Data analyzer
├── judge_engine.py              # Review engine
├── irrelevant_content_grading.py # Irrelevant content scoring
├── extract_irrelevant_content.py # Irrelevant content extraction
├── general_negative_points.py   # Negative point processing
├── config.yaml                  # Main configuration file
├── config_model.yaml           # Model configuration file
├── config_visualization.yaml   # Visualization configuration
├── requirements.txt            # Dependency list
└── data/                       # Data directory
    ├── input/                  # Input files
    │   ├── specialty_evaluation_dataset.xlsx  # Thoracic surgery evaluation dataset (92 cases)
    │   └── community_contributions.xlsx       # Community contributed cases
    └── output/                 # Output files
        └── analysis/           # Analysis reports
```

### Data Flow

1. **Input Phase**: Read Excel file, validate data format
2. **Parallel Processing**: Simultaneously execute Met review and irrelevant content detection
3. **Result Merging**: Intelligently merge outputs from both parallel steps
4. **Score Calculation**: Calculate multi-dimensional scores based on merged results
5. **Analysis Output**: Generate statistical reports and visualization charts

### Performance Optimization

- Asynchronous parallel processing improves efficiency
- Batch processing reduces API call frequency
- Intelligent retry mechanism handles network exceptions
- Memory optimization handles large files

## Contribution Guidelines

Welcome to submit Issues and Pull Requests to improve system functionality.

### Development Environment Setup

```bash
git clone <repository>
cd medical-ai-bench-eval
pip install -r requirements.txt
```

### Code Standards

- Follow PEP 8 coding standards
- Add detailed docstrings
- Include unit tests
- Update README documentation

## Citation

If you use this system in your research, please cite our paper:

**English:**
> Xiuyuan Chen, Tao Sun, Dexin Su, Ailing Yu, Junwei Liu, Zhe Chen, Gangzeng Jin, Xin Wang, Jingnan Liu, Hansong Xiao, Hualei Zhou, Dongjie Tao, Chunxiao Guo, Minghui Yang, Yuan Xia, Jing Zhao, Qianrui Fan, Yanyun Wang, Shuai Zhen, Kezhong Chen, Jun Wang, Zewen Sun, Heng Zhao, Tian Guan, Shaodong Wang, Geyun Chang, Jiaming Deng, Hongchengcheng Chen, Kexin Feng, Ruzhen Li, Jiayi Geng, Changtai Zhao, Jun Wang, Guihu Lin, Peihao Li, Liqi Liu, Peng Wei, Jian Wang, Jinjie Gu, Ping Wang, Fan Yang (2025). GAPS: A Clinically Grounded, Automated Benchmark for Evaluating AI Clinicians. *arXiv preprint* arXiv:2510.13734. https://arxiv.org/abs/2510.13734

```bibtex
@article{chen2025gaps,
  title={GAPS: A Clinically Grounded, Automated Benchmark for Evaluating AI Clinicians},
  author={Chen, Xiuyuan and Sun, Tao and Su, Dexin and Yu, Ailing and Liu, Junwei and Chen, Zhe and Jin, Gangzeng and Wang, Xin and Liu, Jingnan and Xiao, Hansong and Zhou, Hualei and Tao, Dongjie and Guo, Chunxiao and Yang, Minghui and Xia, Yuan and Zhao, Jing and Fan, Qianrui and Wang, Yanyun and Zhen, Shuai and Chen, Kezhong and Wang, Jun and Sun, Zewen and Zhao, Heng and Guan, Tian and Wang, Shaodong and Chang, Geyun and Deng, Jiaming and Chen, Hongchengcheng and Feng, Kexin and Li, Ruzhen and Geng, Jiayi and Zhao, Changtai and Wang, Jun and Lin, Guihu and Li, Peihao and Liu, Liqi and Wei, Peng and Wang, Jian and Gu, Jinjie and Wang, Ping and Yang, Fan},
  journal={arXiv preprint arXiv:2510.13734},
  year={2025},
  url={https://arxiv.org/abs/2510.13734}
}
```

## 🤝 Community Contribution / 共创呼吁

We welcome contributions from the medical AI community to expand and improve our evaluation dataset! Your expertise can help build a more comprehensive benchmark for medical AI systems.

### 📋 How to Contribute

#### Option 1: Submit an Issue
Create a new issue with the label `data-contribution` using the following template:

```markdown
**Medical Question**
[Provide your clinical question here]

**Evaluation Rubrics (JSON Format)**
```json
[
  {
    "id": 1,
    "claim": "Your evaluation criterion description",
    "level": "A1|A2|A3|S1|S2|S3|S4",
    "type": "positive|negative"
  },
  {
    "id": 2,
    "claim": "Another evaluation criterion",
    "level": "A2",
    "type": "positive"
  }
]
```

**Medical Specialty**
[e.g., Cardiology, Pulmonology, Oncology, etc.]

**Question Type**
[e.g., Diagnosis, Treatment, Risk Assessment, etc.]

**Additional Context**
[Any relevant clinical context or references]
```

#### Option 2: Submit a Pull Request
1. Fork this repository
2. Add your data to `data/input/community_contributions.xlsx` following the existing format:
   - **question**: Your medical question
   - **rubrics**: JSON array of evaluation criteria
   - **specialty**: Medical specialty area
   - **difficulty**: Easy/Medium/Hard
   - **source**: Your name/institution (optional)

3. Ensure your contribution follows these guidelines:
   - **Clinical Relevance**: Questions should reflect real-world medical scenarios
   - **Evidence-Based**: Evaluation criteria should be based on established medical guidelines
   - **Clear Scoring**: Use our scoring system appropriately:
     - **Positive Points**: A1 (5 pts), A2 (3 pts), A3 (1 pt)
     - **Negative Points**: S1 (-1 pt), S2 (-2 pts), S3 (-3 pts), S4 (-4 pts)

### 📝 Contribution Guidelines

#### Evaluation Criteria Design
- **A1 (Critical, 5 points)**: Essential medical knowledge that could impact patient safety
- **A2 (Important, 3 points)**: Significant clinical considerations
- **A3 (Helpful, 1 point)**: Additional relevant information
- **S1 (Minor Error, -1 point)**: Small inaccuracies that don't affect core treatment
- **S2 (Moderate Error, -2 points)**: Incorrect information that could mislead
- **S3 (Major Error, -3 points)**: Serious medical errors
- **S4 (Critical Error, -4 points)**: Dangerous misinformation that could harm patients

#### Quality Standards
- Questions should be **clinically realistic** and based on actual medical scenarios
- Evaluation criteria must be **evidence-based** and reference current medical guidelines
- Each question should have **3-8 evaluation points** for balanced assessment
- Include both **positive criteria** (what should be mentioned) and **negative criteria** (what should be avoided)

### 🎯 Priority Areas
We especially welcome contributions in:
- **Rare Diseases**: Uncommon conditions that challenge AI systems
- **Multidisciplinary Cases**: Complex cases requiring multiple specialties
- **Cultural Considerations**: Cases reflecting diverse patient populations
- **Emergency Medicine**: Time-critical decision-making scenarios
- **Pediatric Medicine**: Age-specific medical considerations

### 📊 Data Format Example
```json
{
  "question": "A 65-year-old patient presents with chest pain and shortness of breath. How would you approach the initial evaluation?",
  "rubrics": [
    {
      "id": 1,
      "claim": "Should obtain detailed history including pain characteristics, timing, and associated symptoms",
      "level": "A1",
      "type": "positive"
    },
    {
      "id": 2,
      "claim": "Must perform ECG and chest X-ray as initial diagnostic tests",
      "level": "A1", 
      "type": "positive"
    },
    {
      "id": 3,
      "claim": "Should not delay evaluation with unnecessary tests in acute presentation",
      "level": "S2",
      "type": "negative"
    }
  ],
  "specialty": "Emergency Medicine",
  "difficulty": "Medium"
}
```

### 🔄 Review Process
1. **Community Review**: Contributions will be reviewed by medical professionals
2. **Quality Check**: Ensure clinical accuracy and appropriate difficulty
3. **Integration**: Approved contributions will be merged into the main dataset
4. **Attribution**: Contributors will be acknowledged in our contributor list

### 📞 Contact
For questions about contributing, please:
- Open an issue with the `question` label
- Join our discussion in the GitHub Discussions section

Thank you for helping build a better benchmark for medical AI evaluation! 🙏

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
