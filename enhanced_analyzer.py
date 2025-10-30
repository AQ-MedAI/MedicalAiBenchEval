import pandas as pd
import json
import yaml
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import argparse
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class EnhancedMedicalAnalyzer:
    """
    Enhanced Medical Model Evaluation Analyzer

    Main functions:
    1. Load and parse medical model evaluation data
    2. Extract multi-dimensional scoring indicators (A-class positive scores, S-class deductions, irrelevant content deductions)
    3. Generate comprehensive statistical analysis reports
    4. Create diverse visualization charts
    5. Perform detailed comparative analysis by category

    Usage:
    analyzer = EnhancedMedicalAnalyzer('config.yaml')
    analyzer.run_analysis()
    """

    def __init__(self, config_file=None):
        """
        Initialize analyzer

        Args:
            config_file: Configuration file path, uses default configuration if None

        Note:
            - Load configuration file or use default configuration
            - Initialize various data storage containers
            - Set Chinese fonts to avoid chart garbled text
        """
        self.config = self._load_config(config_file)
        self.df = None
        self.model_scores = {}  # Store basic scores for each model
        self.overall_stats = {}  # Store overall statistical data
        self.category_results = {}  # Store category-wise analysis results
        self.deduction_stats = {}  # Store deduction statistics data
        self.detailed_scores = {}  # Store detailed score distribution
        self._setup_chinese_fonts()

    def _load_config(self, config_file):
        """
        Load configuration file

        Args:
            config_file: Configuration file path

        Returns:
            dict: Configuration dictionary

        Note:
            - Prioritize loading specified configuration file
            - Use default configuration if file doesn't exist or not specified
            - Return configuration content from analysis section
        """
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config['analysis']  # Return analysis section directly
        else:
            return self._get_default_config()

    def _get_default_config(self):
        """
        Get default configuration

        Returns:
            dict: Default configuration dictionary

        Note:
            - Define input file path and column mappings
            - Set output file paths
            - Configure visualization parameters (chart types, styles, colors, etc.)
            - These default values can be modified as needed
        """
        return {
            'input_file': 'data/input/new/medical_evaluation_result_V2.xlsx',
            'columns': {
                'model_scores': {
                    'GPT-5': 'gpt_5_answer_judged_json_scores',
                    'Gemini-2.5-Pro': 'gemini_2_5_pro_answer_judged_json_scores',
                    'Claude-Opus-4': 'claude_opus_4_answer_judged_json_scores'
                },
                'category_column': 'category',
                'score_field': 'normalized'
            },
            'output': {
                'visualization': 'data/output/analysis/medical_evaluation_report.png',
                'detailed_report': 'data/output/analysis/medical_analysis_report.txt',
                'csv_summary': 'data/output/analysis/model_performance_summary.csv'
            },
            'visualization': {
                'charts': {
                    'bar_overall': True,
                    'boxplot_distribution': True,
                    'heatmap_category': True,
                    'bar_category': True,
                    'radar_chart': True,
                    'density_plot': True
                },
                'style': {
                    'figure_size': [24, 16],
                    'dpi': 300,
                    'colors': {
                        'GPT-5': '#FF6B6B',
                        'Gemini-2.5-Pro': '#4ECDC4',
                        'Claude-Opus-4': '#45B7D1'
                    }
                }
            }
        }

    def _setup_chinese_fonts(self):
        """
        Set Chinese fonts to solve chart garbled text problem

        Note:
            - Try to use available Chinese fonts on system
            - Support multiple platforms (macOS, Windows, Linux)
            - Set font parameters for matplotlib and seaborn
            - Use fallback solution if font setting fails
        """
        try:
            # Try to use available Chinese fonts on system
            system_fonts = [
                'Heiti TC',           # macOS Chinese Black
                'SimHei',             # Windows Black
                'Arial Unicode MS',   # Universal Unicode font
                'DejaVu Sans',        # Open source font
                'sans-serif'          # Final fallback
            ]

            # Set fonts
            plt.rcParams['font.sans-serif'] = system_fonts
            plt.rcParams['axes.unicode_minus'] = False
            sns.set_style("whitegrid")

            print("    Chinese font setup successful")
        except Exception as e:
            print(f"    Font setup warning: {e}")
            # Use default font setting
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

    def extract_irrelevant_content_stats(self, json_str):
        """
        Extract level count statistics from irrelevant content JSON

        Args:
            json_str: JSON string of irrelevant content

        Returns:
            dict: Dictionary containing statistics for each level

        Note:
            - Parse irrelevant content scoring data
            - Count occurrences of each level S1-S4
            - Calculate total irrelevant content count
            - Handle JSON parsing exceptions, return default values
        """
        try:
            if pd.isna(json_str):
                return {
                    'S1': 0, 'S2': 0, 'S3': 0, 'S4': 0, 'total': 0
                }

            data = json.loads(str(json_str))

            # Count occurrences for each level
            level_counts = {'S1': 0, 'S2': 0, 'S3': 0, 'S4': 0}

            # Count each level from final_grades
            final_grades = data.get('final_grades', [])
            for grade in final_grades:
                level = grade.get('final_level', '')
                if level in level_counts:
                    level_counts[level] += 1

            level_counts['total'] = sum(level_counts.values())
            return level_counts

        except Exception as e:
            print(f"Error parsing irrelevant content JSON: {e}")
            return {'S1': 0, 'S2': 0, 'S3': 0, 'S4': 0, 'total': 0}

    def extract_detailed_scores(self, json_str):
        """
        Extract detailed score and deduction information from JSON

        Args:
            json_str: JSON string of scoring results

        Returns:
            dict/None: Detailed scoring data dictionary, returns None if parsing fails

        Note:
            - Extract normalized scores and final scores
            - Count occurrences and scores for A-class positive indicators (A1, A2, A3)
            - Count occurrences and deductions for S-class negative indicators (S1-S4)
            - Calculate totals for each category
            - Adapt to actual JSON data format
        """
        try:
            if pd.isna(json_str):
                return None
            data = json.loads(str(json_str))

            result = {
                'normalized_score': float(data.get('normalized', 0)),
                'final_score': float(data.get('final_total_score', 0)),

                # A-class scoring statistics
                'A_counts': {
                    'A1': int(data.get('A1_count', 0)),
                    'A2': int(data.get('A2_count', 0)),
                    'A3': int(data.get('A3_count', 0))
                },
                'A_scores': {
                    'A1': float(data.get('A1_score', 0)),
                    'A2': float(data.get('A2_score', 0)),
                    'A3': float(data.get('A3_score', 0))
                },
                'positive_total_count': int(data.get('positive_total_count', 0)),
                'positive_all_score': float(data.get('positive_all_score_with_met', 0)),

                # Rubric scoring statistics
                'rubric_counts': {
                    'S1': int(data.get('rubric_S1_count', 0)),
                    'S2': int(data.get('rubric_S2_count', 0)),
                    'S3': int(data.get('rubric_S3_count', 0)),
                    'S4': int(data.get('rubric_S4_count', 0))
                },
                'rubric_total_count': int(data.get('rubric_total_count', 0)),
                'rubric_all_score': float(data.get('rubric_all_score_with_met', 0))
            }

            return result
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return None

    def extract_score(self, json_str, field_name='normalized'):
        """
        Extract score for specified field from JSON

        Args:
            json_str: JSON string
            field_name: Field name to extract, default is 'normalized'

        Returns:
            float/None: Extracted score value, returns None if failed

        Note:
            - Used to extract basic score data
            - Support specifying different score fields
            - Handle JSON parsing exceptions
        """
        try:
            if pd.isna(json_str):
                return None
            data = json.loads(str(json_str))
            return float(data.get(field_name, data.get('score', 0)))
        except:
            return None

    def load_data(self):
        """
        Load Excel data file

        Returns:
            pd.DataFrame: Loaded data frame

        Note:
            - Check if input file exists
            - Read Excel file to DataFrame
            - Output number of successfully loaded records
            - Raises FileNotFoundError if file doesn't exist
        """
        input_file = self.config['input_file']
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"File not found: {input_file}")

        self.df = pd.read_excel(input_file)
        print(f"    Load successful: {len(self.df)} records")
        return self.df

    def extract_scores(self):
        """
        Extract model scores and detailed scoring items

        Note:
            - Iterate through all model columns specified in configuration
            - Extract basic score data for each model
            - Extract detailed scoring statistical information
            - Associate corresponding irrelevant content deduction data
            - Store in respective data containers
        """
        model_config = self.config['columns']['model_scores']
        score_field = self.config['columns']['score_field']

        # Irrelevant content column mapping
        irrelevant_columns = {
            'GPT-5': 'gpt_5_answer_irrelevant_content',
            'Gemini-2.5-Pro': 'gemini_2_5_pro_answer_irrelevant_content',
            'Claude-Opus-4': 'claude_opus_4_answer_irrelevant_content'
        }

        for model_name, column_name in model_config.items():
            if column_name in self.df.columns:
                # Extract scores
                scores = self.df[column_name].apply(
                    lambda x: self.extract_score(x, score_field)
                ).dropna()

                # Extract detailed scores
                detailed_data = []
                for idx, row in self.df.iterrows():
                    detailed = self.extract_detailed_scores(row[column_name])
                    if detailed:
                        # Extract corresponding irrelevant content statistics
                        irrelevant_col = irrelevant_columns.get(model_name)
                        if irrelevant_col and irrelevant_col in self.df.columns:
                            irrelevant_stats = self.extract_irrelevant_content_stats(row[irrelevant_col])
                            detailed['irrelevant_counts'] = irrelevant_stats
                        else:
                            detailed['irrelevant_counts'] = {'S1': 0, 'S2': 0, 'S3': 0, 'S4': 0, 'total': 0}

                        detailed_data.append(detailed)

                self.model_scores[model_name] = scores
                self.deduction_stats[model_name] = {
                    'detailed_data': detailed_data,
                    'total_records': len(detailed_data)
                }
                self.detailed_scores[model_name] = detailed_data

                print(f"    {model_name}: {len(scores)} scores, {len(detailed_data)} detailed records")

    def _get_score_range(self, score):
        """
        Map score to range

        Args:
            score: Normalized score (between 0-1)

        Returns:
            str: Score range string

        Note:
            - Convert continuous scores to discrete range labels
            - Facilitate grouped statistics and visualization
        """
        if score >= 0.9: return '90-100%'
        elif score >= 0.8: return '80-89%'
        elif score >= 0.7: return '70-79%'
        elif score >= 0.6: return '60-69%'
        else: return '0-59%'

    def calculate_stats(self):
        """
        Calculate statistical indicators including detailed scoring items

        Returns:
            dict: Overall statistical results

        Note:
            - Calculate basic statistical indicators for each model (mean, std, median, etc.)
            - Aggregate detailed statistics for A-class positive indicators
            - Aggregate detailed statistics for S-class negative indicators
            - Aggregate detailed statistics for irrelevant content deductions
            - Calculate derived indicators like average scores
        """
        for model, scores in self.model_scores.items():
            # Basic statistics
            base_stats = {
                'Average Score': round(scores.mean(), 4),
                'Standard Deviation': round(scores.std(), 4),
                'Median': round(scores.median(), 4),
                'Sample Size': len(scores)
            }

            # Aggregate detailed statistical data
            detailed_data = self.deduction_stats[model]['detailed_data']
            if detailed_data:
                # A-class indicator statistics
                base_stats.update({
                    'A1 Total Count': sum(d['A_counts']['A1'] for d in detailed_data),
                    'A2 Total Count': sum(d['A_counts']['A2'] for d in detailed_data),
                    'A3 Total Count': sum(d['A_counts']['A3'] for d in detailed_data),
                    'positive_total_count': sum(d['positive_total_count'] for d in detailed_data),
                    'positive_avg_score': round(sum(d['positive_all_score'] for d in detailed_data) / len(detailed_data), 2)
                })

                # Rubric indicator statistics
                base_stats.update({
                    'S1 Total Count': sum(d['rubric_counts']['S1'] for d in detailed_data),
                    'S2 Total Count': sum(d['rubric_counts']['S2'] for d in detailed_data),
                    'S3 Total Count': sum(d['rubric_counts']['S3'] for d in detailed_data),
                    'S4 Total Count': sum(d['rubric_counts']['S4'] for d in detailed_data),
                    'rubric_total_count': sum(d['rubric_total_count'] for d in detailed_data),
                    'rubric_avg_score': round(sum(d['rubric_all_score'] for d in detailed_data) / len(detailed_data), 2)
                })

                # Irrelevant content deduction statistics - extracted from dedicated irrelevant content columns
                base_stats.update({
                    'Irrelevant S1 Count': sum(d['irrelevant_counts']['S1'] for d in detailed_data),
                    'Irrelevant S2 Count': sum(d['irrelevant_counts']['S2'] for d in detailed_data),
                    'Irrelevant S3 Count': sum(d['irrelevant_counts']['S3'] for d in detailed_data),
                    'Irrelevant S4 Count': sum(d['irrelevant_counts']['S4'] for d in detailed_data),
                    'Irrelevant Total Count': sum(d['irrelevant_counts']['total'] for d in detailed_data)
                })
            else:
                # Provide default values if detailed data is empty
                base_stats.update({
                    'A1 Total Count': 0, 'A2 Total Count': 0, 'A3 Total Count': 0, 'positive_total_count': 0, 'positive_avg_score': 0,
                    'S1 Total Count': 0, 'S2 Total Count': 0, 'S3 Total Count': 0, 'S4 Total Count': 0, 'rubric_total_count': 0, 'rubric_avg_score': 0,
                    'Irrelevant S1 Count': 0, 'Irrelevant S2 Count': 0, 'Irrelevant S3 Count': 0, 'Irrelevant S4 Count': 0, 'Irrelevant Total Count': 0
                })

            self.overall_stats[model] = base_stats
        return self.overall_stats

    def analyze_categories(self):
        """
        Analyze by category including detailed scoring items

        Returns:
            dict: Category-wise analysis results

        Note:
            - Group analysis based on category column specified in configuration
            - Calculate statistical indicators for each model in each category
            - Include detailed statistics for A-class, S-class, irrelevant content
            - Support multi-dimensional comparative analysis
        """
        category_col = self.config['columns']['category_column']
        score_field = self.config['columns']['score_field']

        # Irrelevant content column mapping
        irrelevant_columns = {
            'GPT-5': 'gpt_5_answer_irrelevant_content',
            'Gemini-2.5-Pro': 'gemini_2_5_pro_answer_irrelevant_content',
            'Claude-Opus-4': 'claude_opus_4_answer_irrelevant_content'
        }

        if category_col not in self.df.columns:
            return {}

        for category in self.df[category_col].unique():
            if pd.isna(category):
                continue

            cat_data = self.df[self.df[category_col] == category]
            self.category_results[str(category)] = {}

            for model_name, column_name in self.config['columns']['model_scores'].items():
                if column_name in cat_data.columns:
                    # Basic scores
                    scores = cat_data[column_name].apply(
                        lambda x: self.extract_score(x, score_field)
                    ).dropna()

                    # Detailed scoring analysis
                    detailed_data = []
                    for idx, row in cat_data.iterrows():
                        detailed = self.extract_detailed_scores(row[column_name])
                        if detailed:
                            # Extract corresponding irrelevant content statistics
                            irrelevant_col = irrelevant_columns.get(model_name)
                            if irrelevant_col and irrelevant_col in cat_data.columns:
                                irrelevant_stats = self.extract_irrelevant_content_stats(row[irrelevant_col])
                                detailed['irrelevant_counts'] = irrelevant_stats
                            else:
                                detailed['irrelevant_counts'] = {'S1': 0, 'S2': 0, 'S3': 0, 'S4': 0, 'total': 0}

                            detailed_data.append(detailed)

                    if len(scores) > 0 and detailed_data:
                        stats = {
                            'Average Score': round(scores.mean(), 4),
                            'Standard Deviation': round(scores.std(), 4),
                            'Sample Size': len(scores),
                            # A-class statistics
                            'A1 Total Count': sum(d['A_counts']['A1'] for d in detailed_data),
                            'A2 Total Count': sum(d['A_counts']['A2'] for d in detailed_data),
                            'A3 Total Count': sum(d['A_counts']['A3'] for d in detailed_data),
                            'Positive Total Hits': sum(d['positive_total_count'] for d in detailed_data),
                            # Rubric statistics
                            'S1 Total Count': sum(d['rubric_counts']['S1'] for d in detailed_data),
                            'S2 Total Count': sum(d['rubric_counts']['S2'] for d in detailed_data),
                            'S3 Total Count': sum(d['rubric_counts']['S3'] for d in detailed_data),
                            'S4 Total Count': sum(d['rubric_counts']['S4'] for d in detailed_data),
                            'Rubric Total Hits': sum(d['rubric_total_count'] for d in detailed_data),
                            # Irrelevant content deduction statistics - extracted from dedicated irrelevant content columns
                            'Irrelevant S1 Count': sum(d['irrelevant_counts']['S1'] for d in detailed_data),
                            'Irrelevant S2 Count': sum(d['irrelevant_counts']['S2'] for d in detailed_data),
                            'Irrelevant S3 Count': sum(d['irrelevant_counts']['S3'] for d in detailed_data),
                            'Irrelevant S4 Count': sum(d['irrelevant_counts']['S4'] for d in detailed_data),
                            'Irrelevant Total Count': sum(d['irrelevant_counts']['total'] for d in detailed_data)
                        }
                        self.category_results[str(category)][model_name] = stats
        return self.category_results

    def create_deduction_visualizations(self):
        """
        Create deduction analysis visualization charts

        Note:
            - Generate A-class indicator comparison charts
            - Generate irrelevant content deduction comparison charts
            - Generate Rubric indicator comparison charts
            - Use color scheme from configuration
            - Save as independent detailed analysis chart file
        """
        fig, axes = plt.subplots(2, 3, figsize=[24, 16])
        axes = axes.flatten()

        model_names = list(self.deduction_stats.keys())
        colors = self.config['visualization']['style']['colors']

        # 1. A-class indicator comparison
        ax_idx = 0
        for model in model_names:
            if ax_idx < len(axes) and self.deduction_stats[model]['detailed_data']:
                ax = axes[ax_idx]
                detailed_data = self.deduction_stats[model]['detailed_data']

                a1_count = sum(d['A_counts']['A1'] for d in detailed_data)
                a2_count = sum(d['A_counts']['A2'] for d in detailed_data)
                a3_count = sum(d['A_counts']['A3'] for d in detailed_data)

                bars = ax.bar(['A1', 'A2', 'A3'], [a1_count, a2_count, a3_count],
                              color=colors[model], alpha=0.7)
                ax.set_title(f'{model} A-class Indicators')
                ax.set_ylabel('Count')

                for bar, count in zip(bars, [a1_count, a2_count, a3_count]):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                            f'{count}', ha='center', va='bottom')
                ax_idx += 1

        # 2. Irrelevant content deduction comparison - corrected to extract from dedicated irrelevant content columns
        if len(model_names) > 0 and ax_idx < len(axes):
            ax = axes[ax_idx]
            irrelevant_data = []
            for model in model_names:
                if self.deduction_stats[model]['detailed_data']:
                    detailed_data = self.deduction_stats[model]['detailed_data']
                    irrelevant_data.extend([
                        {'Model': model, 'Level': 'S1', 'Count': sum(d['irrelevant_counts']['S1'] for d in detailed_data)},
                        {'Model': model, 'Level': 'S2', 'Count': sum(d['irrelevant_counts']['S2'] for d in detailed_data)},
                        {'Model': model, 'Level': 'S3', 'Count': sum(d['irrelevant_counts']['S3'] for d in detailed_data)},
                        {'Model': model, 'Level': 'S4', 'Count': sum(d['irrelevant_counts']['S4'] for d in detailed_data)}
                    ])

            if irrelevant_data:
                irr_df = pd.DataFrame(irrelevant_data)
                sns.barplot(data=irr_df, x='Level', y='Count', hue='Model', ax=ax)
                ax.set_title('Irrelevant Content Deductions')
                ax.legend(title='Model')
                ax_idx += 1

        # 3. Rubric indicator comparison
        if len(model_names) > 0 and ax_idx < len(axes):
            ax = axes[ax_idx]
            rubric_data = []
            for model in model_names:
                if self.deduction_stats[model]['detailed_data']:
                    detailed_data = self.deduction_stats[model]['detailed_data']
                    rubric_data.extend([
                        {'Model': model, 'Rubric': 'S1', 'Count': sum(d['rubric_counts']['S1'] for d in detailed_data)},
                        {'Model': model, 'Rubric': 'S2', 'Count': sum(d['rubric_counts']['S2'] for d in detailed_data)},
                        {'Model': model, 'Rubric': 'S3', 'Count': sum(d['rubric_counts']['S3'] for d in detailed_data)},
                        {'Model': model, 'Rubric': 'S4', 'Count': sum(d['rubric_counts']['S4'] for d in detailed_data)}
                    ])

            if rubric_data:
                rub_df = pd.DataFrame(rubric_data)
                sns.barplot(data=rub_df, x='Rubric', y='Count', hue='Model', ax=ax)
                ax.set_title('Rubric Indicators')
                ax.legend(title='Model')

        plt.tight_layout()
        deduction_file = self.config['output']['visualization'].replace('.png', '_detailed_analysis.png')
        plt.savefig(deduction_file, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"    Detailed analysis saved: {deduction_file}")
        plt.close()

    def create_visualizations(self):
        """
        Create main visualization charts

        Note:
            - Generate multiple types of charts based on configuration
            - Include bar charts, box plots, heatmaps, radar charts, density plots, etc.
            - Automatically adjust subplot layout
            - Use configured color scheme and styles
            - Support detailed comparative analysis by category
        """
        charts_config = self.config['visualization']['charts']
        active_charts = [name for name, enabled in charts_config.items() if enabled]

        if not active_charts:
            print("    No charts selected")
            return

        # Calculate chart count and layout
        chart_count = len(active_charts)
        cols = min(3, chart_count)
        rows = (chart_count + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols,
                                 figsize=self.config['visualization']['style']['figure_size'])

        # Ensure axes is always in list/array format
        if chart_count == 1:
            axes = [axes]
        elif chart_count <= 3:
            axes = [axes]
        else:
            axes = axes.flatten()

        colors = self.config['visualization']['style']['colors']
        model_names = list(self.overall_stats.keys())

        chart_index = 0

        # 1. Overall average score comparison
        if charts_config.get('bar_overall', True) and chart_index < len(axes):
            ax = axes[chart_index] if chart_count > 1 else axes[0]
            avg_scores = [self.overall_stats[model]['Average Score'] for model in model_names]

            bars = ax.bar(model_names, avg_scores,
                          color=[colors[model] for model in model_names], alpha=0.8)
            ax.set_title('Overall Average Scores', fontsize=14)
            ax.set_ylabel('Normalized Score')

            for bar, score in zip(bars, avg_scores):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{score:.3f}', ha='center', va='bottom')
            chart_index += 1

        # 2. Score distribution box plot
        if charts_config.get('boxplot_distribution', True) and chart_index < len(axes):
            ax = axes[chart_index]
            box_data = [(model, score) for model in model_names
                        for score in self.model_scores[model]]

            box_df = pd.DataFrame(box_data, columns=['Model', 'Score'])
            sns.boxplot(data=box_df, x='Model', y='Score',
                        palette=[colors[model] for model in model_names], ax=ax)
            ax.set_title('Score Distribution', fontsize=14)
            ax.tick_params(axis='x', rotation=15)
            chart_index += 1

        # 3. Category-wise heatmap
        if charts_config.get('heatmap_category', True) and chart_index < len(axes) and self.category_results:
            ax = axes[chart_index]
            heatmap_data = [(category, model, stats['Average Score'])
                            for category, model_stats in self.category_results.items()
                            for model, stats in model_stats.items()]

            heat_df = pd.DataFrame(heatmap_data, columns=['Category', 'Model', 'Score'])
            pivot_df = heat_df.pivot(index='Model', columns='Category', values='Score')
            sns.heatmap(pivot_df, annot=True, fmt='.3f', cmap='RdYlBu_r',
                        center=0.5, vmin=0, vmax=1, ax=ax)
            ax.set_title('Performance by Category', fontsize=14)
            chart_index += 1

        # 4. Category-wise bar chart comparison
        if charts_config.get('bar_category', True) and chart_index < len(axes) and self.category_results:
            ax = axes[chart_index]
            bar_data = [(category, model, stats['Average Score'])
                        for category, model_stats in self.category_results.items()
                        for model, stats in model_stats.items()]

            bar_df = pd.DataFrame(bar_data, columns=['Category', 'Model', 'Score'])
            sns.barplot(data=bar_df, x='Category', y='Score', hue='Model',
                        palette=[colors[model] for model in model_names], ax=ax)
            ax.set_title('Performance Comparison by Category', fontsize=14)
            ax.legend(title='Model')
            chart_index += 1

        # 5. Radar chart
        if charts_config.get('radar_chart', True) and chart_index < len(axes) and self.category_results:
            if chart_index < len(axes):
                ax = plt.subplot(2, 3, chart_index+1, projection='polar')
                categories = sorted(self.category_results.keys())
                angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)
                angles = np.concatenate((angles, [angles[0]]))

                for model in model_names:
                    scores = [self.category_results[cat][model]['Average Score']
                              for cat in categories]
                    scores = scores + [scores[0]]

                    ax.plot(angles, scores, 'o-', linewidth=2.5,
                            label=model, color=colors[model])
                    ax.fill(angles, scores, alpha=0.15, color=colors[model])

                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(categories)
                ax.set_ylim(0, 1)
                ax.set_title('Radar Chart', fontsize=14, pad=20)
                ax.legend()
                chart_index += 1

        # 6. Density distribution plot
        if charts_config.get('density_plot', True) and chart_index < len(axes):
            ax = axes[chart_index] if chart_index < len(axes) else axes[-1]
            for model in model_names:
                sns.kdeplot(data=self.model_scores[model], label=model,
                            color=colors[model], linewidth=2.5, ax=ax)
            ax.set_title('Score Density Distribution', fontsize=14)
            ax.set_xlabel('Normalized Score')
            ax.set_xlim(0, 1)
            ax.legend()

        # Hide unused subplots
        if chart_count > 1:
            for idx in range(chart_index, len(axes)):
                if idx < len(axes):
                    axes[idx].set_visible(False)

        plt.tight_layout()
        output_file = self.config['output']['visualization']

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"    Visualization saved: {output_file}")

    def save_reports(self):
        """
        Save analysis reports including detailed scoring item analysis

        Note:
            - Generate CSV format data summary table
            - Generate text format detailed analysis report
            - Include overall statistics and category-wise statistics
            - Cover complete statistics for A-class, S-class, irrelevant content
            - Automatically create output directory
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.config['output']['csv_summary']), exist_ok=True)

        # CSV summary - including detailed scoring items
        csv_data = []
        for model, stats in self.overall_stats.items():
            row = {
                'Dimension': 'Overall',
                'Model': model,
                'Average Score': stats['Average Score'],
                'Standard Deviation': stats['Standard Deviation'],
                'Sample Size': stats['Sample Size'],

                # A-class indicators
                'A1 Total Count': stats['A1 Total Count'],
                'A2 Total Count': stats['A2 Total Count'],
                'A3 Total Count': stats['A3 Total Count'],
                'positive_total_count': stats['positive_total_count'],
                'positive_avg_score': stats['positive_avg_score'],

                # Rubric indicators
                'S1 Total Count': stats['S1 Total Count'],
                'S2 Total Count': stats['S2 Total Count'],
                'S3 Total Count': stats['S3 Total Count'],
                'S4 Total Count': stats['S4 Total Count'],
                'rubric_total_count': stats['rubric_total_count'],
                'rubric_avg_score': stats['rubric_avg_score'],

                # Irrelevant content deduction statistics - add counts for each level
                'Irrelevant S1 Count': stats['Irrelevant S1 Count'],
                'Irrelevant S2 Count': stats['Irrelevant S2 Count'],
                'Irrelevant S3 Count': stats['Irrelevant S3 Count'],
                'Irrelevant S4 Count': stats['Irrelevant S4 Count'],
                'Irrelevant Total Count': stats['Irrelevant Total Count']
            }
            csv_data.append(row)

        for category, model_stats in self.category_results.items():
            for model, stats in model_stats.items():
                row = {
                    'Dimension': category,
                    'Model': model,
                    'Average Score': stats['Average Score'],
                    'Standard Deviation': stats['Standard Deviation'],
                    'Sample Size': stats['Sample Size'],

                    # A-class indicators
                    'A1 Total Count': stats['A1 Total Count'],
                    'A2 Total Count': stats['A2 Total Count'],
                    'A3 Total Count': stats['A3 Total Count'],
                    'Positive Total Hits': stats['Positive Total Hits'],

                    # Rubric indicators
                    'S1 Total Count': stats['S1 Total Count'],
                    'S2 Total Count': stats['S2 Total Count'],
                    'S3 Total Count': stats['S3 Total Count'],
                    'S4 Total Count': stats['S4 Total Count'],
                    'Rubric Total Hits': stats['Rubric Total Hits'],

                    # Irrelevant content deduction statistics - add counts for each level
                    'Irrelevant S1 Count': stats['Irrelevant S1 Count'],
                    'Irrelevant S2 Count': stats['Irrelevant S2 Count'],
                    'Irrelevant S3 Count': stats['Irrelevant S3 Count'],
                    'Irrelevant S4 Count': stats['Irrelevant S4 Count'],
                    'Irrelevant Total Count': stats['Irrelevant Total Count']
                }
                csv_data.append(row)

        csv_df = pd.DataFrame(csv_data)
        csv_df.to_csv(self.config['output']['csv_summary'], index=False, encoding='utf-8')

        # Detailed report - including complete scoring items
        lines = ["="*60, "    Medical Model Detailed Evaluation Report", "="*60]

        # Overall ranking
        best_model = max(self.overall_stats.items(), key=lambda x: x[1]['Average Score'])
        lines.append(f"\n    Best Model: {best_model[0]} ({best_model[1]['Average Score']:.4f})")

        lines.append("\n    Overall Statistics:")
        for model, stats in sorted(self.overall_stats.items(),
                                   key=lambda x: x[1]['Average Score'], reverse=True):
            lines.append(f"\n{model}:")
            lines.append(f"  Average Score: {stats['Average Score']:.4f} ± {stats['Standard Deviation']:.4f} (n={stats['Sample Size']})")

            lines.append(f"  A-class Indicators:")
            lines.append(f"    A1: {stats['A1 Total Count']} times  A2: {stats['A2 Total Count']} times  A3: {stats['A3 Total Count']} times")
            lines.append(f"    positive hits: {stats['positive_total_count']} times  avg_score: {stats['positive_avg_score']:.2f}")

            lines.append(f"  Rubric Indicators:")
            lines.append(f"    S1: {stats['S1 Total Count']} times  S2: {stats['S2 Total Count']} times  S3: {stats['S3 Total Count']} times  S4: {stats['S4 Total Count']} times")
            lines.append(f"    rubric hits: {stats['rubric_total_count']} times  avg_score: {stats['rubric_avg_score']:.2f}")

            # Add irrelevant content deduction counts for each level
            lines.append(f"  Irrelevant Content Deductions:")
            lines.append(f"    S1: {stats['Irrelevant S1 Count']} times  S2: {stats['Irrelevant S2 Count']} times  S3: {stats['Irrelevant S3 Count']} times  S4: {stats['Irrelevant S4 Count']} times")
            lines.append(f"    irrelevant content hits: {stats['Irrelevant Total Count']} times")

        if self.category_results:
            lines.append("\n🏗️ Dimension-wise Comparison:")
            for category in sorted(self.category_results.keys()):
                lines.append(f"\n【{category}】:")
                for model, stats in sorted(self.category_results[category].items(),
                                           key=lambda x: x[1]['Average Score'], reverse=True):
                    lines.append(f"   {model}: {stats['Average Score']:.4f} ± {stats['Standard Deviation']:.4f} (n={stats['Sample Size']})")
                    lines.append(f"   A-class: A1={stats['A1 Total Count']} A2={stats['A2 Total Count']} A3={stats['A3 Total Count']}")
                    lines.append(f"   Rubric: S1={stats['S1 Total Count']} S2={stats['S2 Total Count']} S3={stats['S3 Total Count']} S4={stats['S4 Total Count']}")
                    lines.append(f"   Irrelevant: S1={stats['Irrelevant S1 Count']} S2={stats['Irrelevant S2 Count']} S3={stats['Irrelevant S3 Count']} S4={stats['Irrelevant S4 Count']} irrelevant hits={stats['Irrelevant Total Count']}")

        with open(self.config['output']['detailed_report'], 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def run_analysis(self):
        """
        Run complete analysis workflow

        Note:
            - Execute complete data loading and analysis workflow
            - Include data extraction, statistical calculation, visualization generation, report saving
            - Generate specialized charts for deduction analysis
            - Output processing progress and result file information
            - Include exception handling to ensure program stability
        """
        try:
            print("    Starting medical model evaluation analysis (including deduction statistics)...")

            self.load_data()
            self.extract_scores()
            self.calculate_stats()
            self.analyze_categories()
            self.create_visualizations()
            self.create_deduction_visualizations()  # Add deduction analysis charts
            self.save_reports()

            print("\n" + "="*50)
            print("    Analysis complete! Files saved to data/output/analysis/ folder")
            print("\n    New files:")
            print("  - Deduction analysis charts: medical_evaluation_report_detailed_analysis.png")
            print("  - Detailed deduction report: medical_analysis_report.txt")
            print("  - Complete data CSV: model_performance_summary.csv")
            print("="*50)

        except Exception as e:
            print(f"    Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """
    Main function - Entry point for medical model evaluation analysis tool

    Note:
        - Parse command line arguments
        - Support custom configuration files, input files, chart selection, etc.
        - Provide data sample viewing functionality
        - Execute complete analysis workflow

    Command line arguments:
        -c, --config: Configuration file path
        -f, --file: Custom Excel file path
        --charts: Specify chart types to generate
        --show-sample: View data sample

    Usage examples:
        python script.py -c config.yaml -f data.xlsx
        python script.py --charts bar_overall,boxplot_distribution
        python script.py --show-sample
    """
    parser = argparse.ArgumentParser(description='Enhanced Medical Model Evaluation Analysis Tool')
    parser.add_argument('-c', '--config', default='config_visualization.yaml',
                        help='Configuration file path')
    parser.add_argument('-f', '--file', help='Custom Excel file path')
    parser.add_argument('--charts', help='Chart list, separated by commas')
    parser.add_argument('--show-sample', action='store_true', help='View data sample')

    args = parser.parse_args()

    analyzer = EnhancedMedicalAnalyzer(args.config)

    if args.file:
        analyzer.config['input_file'] = args.file

    if args.charts:
        # Parse chart parameters
        selected_charts = args.charts.split(',')
        for chart in selected_charts:
            chart = chart.strip()
            if chart in analyzer.config['visualization']['charts']:
                analyzer.config['visualization']['charts'][chart] = True

    if args.show_sample:
        df = analyzer.load_data()
        print("\n Data Sample:")
        print(df.head())
        return

    analyzer.run_analysis()


if __name__ == "__main__":
    main()