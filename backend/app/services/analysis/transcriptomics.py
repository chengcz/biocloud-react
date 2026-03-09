"""Transcriptomics analysis tools"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any

from .base import BaseAnalysis, ToolDefinition, ToolParameter, AnalysisResult
from .registry import register_tool


@register_tool
class VolcanoPlotTool(BaseAnalysis):
    """Volcano plot for differential expression analysis"""

    tool_name = "volcano_plot"
    tool_description = "Generate a volcano plot to visualize differential gene expression. Shows log2 fold change vs significance."
    tool_category = "transcriptomics"

    @classmethod
    def get_definition(cls) -> ToolDefinition:
        return ToolDefinition(
            name=cls.tool_name,
            description=cls.tool_description,
            parameters=[
                ToolParameter(
                    name="data",
                    type="object",
                    description="Differential expression data with columns: gene, log2fc, pvalue",
                    required=True
                ),
                ToolParameter(
                    name="fc_threshold",
                    type="number",
                    description="Fold change threshold for significance",
                    required=False,
                    default=1.0,
                    min_value=0
                ),
                ToolParameter(
                    name="p_threshold",
                    type="number",
                    description="P-value threshold for significance",
                    required=False,
                    default=0.05,
                    min_value=0,
                    max_value=1
                ),
                ToolParameter(
                    name="title",
                    type="string",
                    description="Plot title",
                    required=False,
                    default="Volcano Plot"
                )
            ]
        )

    @classmethod
    def get_parameters_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Differential expression data"
                },
                "fc_threshold": {"type": "number", "default": 1.0},
                "p_threshold": {"type": "number", "default": 0.05},
                "title": {"type": "string", "default": "Volcano Plot"}
            },
            "required": ["data"]
        }

    async def validate_input(self, params: Dict[str, Any]) -> bool:
        """Validate input data"""
        if "data" not in params:
            return False
        data = params["data"]
        required_cols = ["log2fc", "pvalue"]
        if isinstance(data, dict):
            return all(col in data for col in required_cols)
        elif isinstance(data, pd.DataFrame):
            return all(col in data.columns for col in required_cols)
        return False

    async def run(self, params: Dict[str, Any]) -> AnalysisResult:
        """Execute volcano plot analysis"""
        try:
            data = params["data"]
            fc_threshold = params.get("fc_threshold", 1.0)
            p_threshold = params.get("p_threshold", 0.05)
            title = params.get("title", "Volcano Plot")

            # Convert to DataFrame if needed
            if isinstance(data, dict):
                df = pd.DataFrame(data)
            else:
                df = data.copy()

            # Calculate -log10(p-value)
            df["log10p"] = -np.log10(df["pvalue"])

            # Classify genes
            df["significant"] = "not significant"
            df.loc[
                (df["log2fc"] >= fc_threshold) & (df["pvalue"] <= p_threshold),
                "significant"
            ] = "upregulated"
            df.loc[
                (df["log2fc"] <= -fc_threshold) & (df["pvalue"] <= p_threshold),
                "significant"
            ] = "downregulated"

            # Generate figure
            figure = await self.generate_visualization({
                "df": df.to_dict(),
                "fc_threshold": fc_threshold,
                "p_threshold": p_threshold,
                "title": title
            })

            # Statistics
            up_count = (df["significant"] == "upregulated").sum()
            down_count = (df["significant"] == "downregulated").sum()

            return AnalysisResult(
                success=True,
                data={
                    "total_genes": len(df),
                    "upregulated": int(up_count),
                    "downregulated": int(down_count),
                    "not_significant": int((df["significant"] == "not significant").sum())
                },
                figure=figure,
                message=f"Found {up_count} upregulated and {down_count} downregulated genes"
            )

        except Exception as e:
            return AnalysisResult(success=False, error=str(e))

    async def generate_visualization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Plotly figure"""
        df = pd.DataFrame(data["df"])
        fc_threshold = data["fc_threshold"]
        p_threshold = data["p_threshold"]
        title = data["title"]

        fig = go.Figure()

        # Plot each category
        colors = {
            "upregulated": "red",
            "downregulated": "blue",
            "not significant": "gray"
        }

        for category, color in colors.items():
            subset = df[df["significant"] == category]
            fig.add_trace(go.Scatter(
                x=subset["log2fc"],
                y=subset["log10p"],
                mode="markers",
                marker=dict(color=color, size=4, opacity=0.6),
                name=category.capitalize(),
                text=subset.get("gene", subset.index.astype(str)),
                hovertemplate="<b>%{text}</b><br>log2FC: %{x:.2f}<br>-log10(p): %{y:.2f}<extra></extra>"
            ))

        # Add threshold lines
        log10_p_thresh = -np.log10(p_threshold)
        fig.add_hline(y=log10_p_thresh, line_dash="dash", line_color="black",
                      annotation_text=f"p = {p_threshold}")
        fig.add_vline(x=fc_threshold, line_dash="dash", line_color="black")
        fig.add_vline(x=-fc_threshold, line_dash="dash", line_color="black")

        fig.update_layout(
            title=title,
            xaxis_title="log₂(Fold Change)",
            yaxis_title="-log₁₀(p-value)",
            template="plotly_white",
            height=600,
            showlegend=True
        )

        return fig.to_dict()


@register_tool
class HeatmapTool(BaseAnalysis):
    """Heatmap for gene expression visualization"""

    tool_name = "heatmap"
    tool_description = "Generate a heatmap to visualize gene expression across samples"
    tool_category = "transcriptomics"

    @classmethod
    def get_definition(cls) -> ToolDefinition:
        return ToolDefinition(
            name=cls.tool_name,
            description=cls.tool_description,
            parameters=[
                ToolParameter(
                    name="data",
                    type="object",
                    description="Expression matrix with genes as rows and samples as columns",
                    required=True
                ),
                ToolParameter(
                    name="cluster_rows",
                    type="boolean",
                    description="Whether to cluster rows (genes)",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="cluster_cols",
                    type="boolean",
                    description="Whether to cluster columns (samples)",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="colorscale",
                    type="string",
                    description="Color scale for heatmap",
                    required=False,
                    default="RdBu_r",
                    enum=["RdBu_r", "Viridis", "Plasma", "Hot", "Cool"]
                )
            ]
        )

    @classmethod
    def get_parameters_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "cluster_rows": {"type": "boolean", "default": True},
                "cluster_cols": {"type": "boolean", "default": True},
                "colorscale": {"type": "string", "default": "RdBu_r"}
            },
            "required": ["data"]
        }

    async def validate_input(self, params: Dict[str, Any]) -> bool:
        return "data" in params

    async def run(self, params: Dict[str, Any]) -> AnalysisResult:
        try:
            data = params["data"]
            colorscale = params.get("colorscale", "RdBu_r")

            if isinstance(data, dict):
                df = pd.DataFrame(data)
            else:
                df = data.copy()

            figure = await self.generate_visualization({
                "df": df.to_dict(),
                "colorscale": colorscale
            })

            return AnalysisResult(
                success=True,
                data={"genes": len(df), "samples": len(df.columns)},
                figure=figure,
                message=f"Generated heatmap with {len(df)} genes and {len(df.columns)} samples"
            )

        except Exception as e:
            return AnalysisResult(success=False, error=str(e))

    async def generate_visualization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        df = pd.DataFrame(data["df"])
        colorscale = data["colorscale"]

        fig = go.Figure(data=go.Heatmap(
            z=df.values,
            x=df.columns,
            y=df.index.astype(str),
            colorscale=colorscale,
            hoverongaps=False
        ))

        fig.update_layout(
            title="Gene Expression Heatmap",
            xaxis_title="Samples",
            yaxis_title="Genes",
            template="plotly_white",
            height=600
        )

        return fig.to_dict()