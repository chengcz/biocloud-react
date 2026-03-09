"""Microbiome analysis tools"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any

from .base import BaseAnalysis, ToolDefinition, ToolParameter, AnalysisResult
from .registry import register_tool


@register_tool
class TaxonomyPlotTool(BaseAnalysis):
    """Taxonomy composition visualization"""

    tool_name = "taxonomy_plot"
    tool_description = "Generate a stacked bar chart or pie chart showing taxonomic composition"
    tool_category = "microbiome"

    @classmethod
    def get_definition(cls) -> ToolDefinition:
        return ToolDefinition(
            name=cls.tool_name,
            description=cls.tool_description,
            parameters=[
                ToolParameter(
                    name="data",
                    type="object",
                    description="Taxonomy abundance data with taxa as rows and samples as columns",
                    required=True
                ),
                ToolParameter(
                    name="level",
                    type="string",
                    description="Taxonomic level to display",
                    required=False,
                    default="genus",
                    enum=["phylum", "class", "order", "family", "genus", "species"]
                ),
                ToolParameter(
                    name="top_n",
                    type="integer",
                    description="Number of top taxa to display",
                    required=False,
                    default=10,
                    min_value=1,
                    max_value=50
                ),
                ToolParameter(
                    name="chart_type",
                    type="string",
                    description="Type of chart to generate",
                    required=False,
                    default="bar",
                    enum=["bar", "pie"]
                )
            ]
        )

    @classmethod
    def get_parameters_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "level": {"type": "string", "default": "genus"},
                "top_n": {"type": "integer", "default": 10},
                "chart_type": {"type": "string", "default": "bar"}
            },
            "required": ["data"]
        }

    async def validate_input(self, params: Dict[str, Any]) -> bool:
        return "data" in params

    async def run(self, params: Dict[str, Any]) -> AnalysisResult:
        try:
            data = params["data"]
            top_n = params.get("top_n", 10)
            chart_type = params.get("chart_type", "bar")

            if isinstance(data, dict):
                df = pd.DataFrame(data)
            else:
                df = data.copy()

            # Calculate mean abundance and get top taxa
            df["mean_abundance"] = df.mean(axis=1)
            df_top = df.nlargest(top_n, "mean_abundance")

            figure = await self.generate_visualization({
                "df": df_top.to_dict(),
                "chart_type": chart_type
            })

            return AnalysisResult(
                success=True,
                data={"top_taxa": list(df_top.index)},
                figure=figure,
                message=f"Showing top {top_n} taxa"
            )

        except Exception as e:
            return AnalysisResult(success=False, error=str(e))

    async def generate_visualization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        df = pd.DataFrame(data["df"])
        chart_type = data["chart_type"]

        if chart_type == "pie":
            # Pie chart for single sample or mean
            values = df["mean_abundance"].values if "mean_abundance" in df.columns else df.sum(axis=1).values
            fig = go.Figure(data=[go.Pie(
                labels=df.index.astype(str),
                values=values,
                hole=0.3
            )])
            fig.update_layout(title="Taxonomic Composition", template="plotly_white")
        else:
            # Stacked bar chart
            df_plot = df.drop(columns=["mean_abundance"], errors="ignore")
            fig = go.Figure()
            for taxon in df_plot.index:
                fig.add_trace(go.Bar(
                    name=str(taxon),
                    x=df_plot.columns,
                    y=df_plot.loc[taxon],
                ))
            fig.update_layout(
                barmode="stack",
                title="Taxonomic Composition",
                xaxis_title="Samples",
                yaxis_title="Relative Abundance",
                template="plotly_white",
                height=600
            )

        return fig.to_dict()


@register_tool
class AlphaDiversityTool(BaseAnalysis):
    """Alpha diversity analysis"""

    tool_name = "alpha_diversity"
    tool_description = "Calculate and visualize alpha diversity indices (Shannon, Simpson, Chao1)"
    tool_category = "microbiome"

    @classmethod
    def get_definition(cls) -> ToolDefinition:
        return ToolDefinition(
            name=cls.tool_name,
            description=cls.tool_description,
            parameters=[
                ToolParameter(
                    name="data",
                    type="object",
                    description="OTU/ASV abundance table",
                    required=True
                ),
                ToolParameter(
                    name="indices",
                    type="array",
                    description="Diversity indices to calculate",
                    required=False,
                    default=["shannon", "simpson"],
                    enum=["shannon", "simpson", "chao1", "observed"]
                )
            ]
        )

    @classmethod
    def get_parameters_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "indices": {"type": "array", "default": ["shannon", "simpson"]}
            },
            "required": ["data"]
        }

    async def validate_input(self, params: Dict[str, Any]) -> bool:
        return "data" in params

    async def run(self, params: Dict[str, Any]) -> AnalysisResult:
        try:
            data = params["data"]
            indices = params.get("indices", ["shannon", "simpson"])

            if isinstance(data, dict):
                df = pd.DataFrame(data)
            else:
                df = data.copy()

            # Calculate diversity indices
            results = {}
            for col in df.columns:
                sample_data = df[col].values
                results[col] = {}

                if "shannon" in indices:
                    # Shannon index
                    p = sample_data / sample_data.sum()
                    p = p[p > 0]
                    results[col]["shannon"] = -np.sum(p * np.log(p))

                if "simpson" in indices:
                    # Simpson index
                    p = sample_data / sample_data.sum()
                    results[col]["simpson"] = 1 - np.sum(p ** 2)

                if "observed" in indices:
                    # Observed species
                    results[col]["observed"] = np.sum(sample_data > 0)

            figure = await self.generate_visualization({
                "results": results,
                "indices": indices
            })

            return AnalysisResult(
                success=True,
                data=results,
                figure=figure,
                message=f"Calculated {len(indices)} diversity indices"
            )

        except Exception as e:
            return AnalysisResult(success=False, error=str(e))

    async def generate_visualization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        results = data["results"]
        indices = data["indices"]

        df_results = pd.DataFrame(results).T

        fig = go.Figure()
        for idx in indices:
            if idx in df_results.columns:
                fig.add_trace(go.Box(
                    y=df_results[idx],
                    name=idx.capitalize(),
                    boxpoints="all"
                ))

        fig.update_layout(
            title="Alpha Diversity",
            yaxis_title="Diversity Index",
            template="plotly_white",
            height=500
        )

        return fig.to_dict()