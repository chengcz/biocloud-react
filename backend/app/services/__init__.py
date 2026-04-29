"""Services module"""

from .llm import llm_router, detect_tool_call, execute_tool_call, generate_chat_with_tools
from .vep_runner import (
    load_species_config,
    get_species_config,
    run_vep_annotation_async,
    compute_variant_hash,
    parse_vep_result,
)
from .vcf_parser import (
    parse_vcf_file,
    extract_variants_from_vcf,
    validate_vcf_format,
    parse_vcf_string,
)

__all__ = [
    # LLM
    "llm_router",
    "detect_tool_call",
    "execute_tool_call",
    "generate_chat_with_tools",
    # VEP
    "load_species_config",
    "get_species_config",
    "run_vep_annotation_async",
    "compute_variant_hash",
    "parse_vep_result",
    # VCF Parser
    "parse_vcf_file",
    "extract_variants_from_vcf",
    "validate_vcf_format",
    "parse_vcf_string",
]