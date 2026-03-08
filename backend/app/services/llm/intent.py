"""Intent detection for user queries"""

from typing import Optional
from enum import Enum
from pydantic import BaseModel
import json

from app.services.llm.router import llm_router, LLMProvider


class UserIntent(str, Enum):
    """User intent categories"""
    GENERAL_CHAT = "general_chat"
    BIO_ANALYSIS = "bio_analysis"
    FILE_ANALYSIS = "file_analysis"
    HELP = "help"


class AnalysisType(str, Enum):
    """Types of bioinformatics analysis"""
    # Transcriptomics
    VOLCANO_PLOT = "volcano_plot"
    HEATMAP = "heatmap"
    GO_ENRICHMENT = "go_enrichment"
    KEGG_ENRICHMENT = "kegg_enrichment"
    # Genomics
    SNP_DENSITY = "snp_density"
    CIRCOS = "circos"
    VCF_ANALYSIS = "vcf_analysis"
    # Proteomics
    PROTEIN_NETWORK = "protein_network"
    # Microbiome
    TAXONOMY_PLOT = "taxonomy_plot"
    ALPHA_DIVERSITY = "alpha_diversity"
    BETA_DIVERSITY = "beta_diversity"


class IntentResult(BaseModel):
    """Intent detection result"""
    intent: UserIntent
    confidence: float
    analysis_type: Optional[AnalysisType] = None
    parameters: dict = {}
    reason: str = ""


INTENT_PROMPT = """You are an intent classifier for a bioinformatics analysis platform.

Analyze the user's query and classify their intent. Respond in JSON format.

Possible intents:
- general_chat: General conversation, questions not related to bioinformatics analysis
- bio_analysis: Request for bioinformatics analysis (volcano plot, heatmap, enrichment analysis, etc.)
- file_analysis: User wants to analyze uploaded data files
- help: User needs help or guidance

If the intent is bio_analysis, also identify the analysis type:
- volcano_plot: Volcano plot for differential expression
- heatmap: Gene expression heatmap
- go_enrichment: GO enrichment analysis
- kegg_enrichment: KEGG pathway analysis
- snp_density: SNP density visualization
- circos: Circular genome plot
- vcf_analysis: VCF variant analysis
- protein_network: Protein interaction network
- taxonomy_plot: Taxonomy composition plot
- alpha_diversity: Alpha diversity analysis
- beta_diversity: Beta diversity analysis

User query: {query}

Respond in JSON format:
{{"intent": "<intent>", "confidence": <0.0-1.0>, "analysis_type": "<type or null>", "parameters": {{}}, "reason": "<brief explanation>"}}
"""


async def detect_intent(query: str) -> IntentResult:
    """
    Detect user intent from their query

    Args:
        query: User's input text

    Returns:
        IntentResult with classified intent and parameters
    """
    messages = [
        {"role": "system", "content": "You are an intent classifier. Respond only with valid JSON."},
        {"role": "user", "content": INTENT_PROMPT.format(query=query)}
    ]

    try:
        # Use fast model for intent detection
        response = await llm_router.chat_complete(
            messages=messages,
            provider=LLMProvider.CLAUDE,
            fast=True,
            max_tokens=200,
            temperature=0.1
        )

        # Parse JSON response
        result = json.loads(response.strip())

        return IntentResult(
            intent=UserIntent(result.get("intent", "general_chat")),
            confidence=result.get("confidence", 0.5),
            analysis_type=AnalysisType(result["analysis_type"]) if result.get("analysis_type") else None,
            parameters=result.get("parameters", {}),
            reason=result.get("reason", "")
        )

    except Exception:
        # Default to general chat on error
        return IntentResult(
            intent=UserIntent.GENERAL_CHAT,
            confidence=0.5,
            reason="Unable to classify intent, defaulting to general chat"
        )


async def generate_chat_response(
    messages: list,
    model: Optional[str] = None
):
    """
    Generate a chat response using the LLM

    Args:
        messages: Conversation history
        model: Optional model override

    Yields:
        Response chunks
    """
    system_prompt = """You are BioCloud, an AI assistant specialized in bioinformatics analysis.
You help users with:
- Understanding bioinformatics concepts
- Guiding them through analysis workflows
- Explaining analysis results
- Answering questions about genomics, transcriptomics, proteomics, and microbiome research

Be helpful, accurate, and concise. If users want to run analysis, guide them to upload their data or use specific commands."""

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    async for chunk in llm_router.chat_stream(messages=full_messages, model=model):
        yield chunk