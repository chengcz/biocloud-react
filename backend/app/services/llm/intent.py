"""Intent detection and tool calling for user queries"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel
import json

from app.services.llm.router import llm_router, LLMProvider
from app.services.analysis import ToolRegistry


class UserIntent(str, Enum):
    """User intent categories"""
    GENERAL_CHAT = "general_chat"
    TOOL_CALL = "tool_call"
    FILE_ANALYSIS = "file_analysis"
    HELP = "help"


class ToolCallResult(BaseModel):
    """Result of tool call detection"""
    needs_tool: bool
    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = {}
    confidence: float = 0.0
    response_text: str = ""


async def detect_tool_call(query: str) -> ToolCallResult:
    """
    Detect if user wants to run a tool and extract parameters

    Uses LLM with function calling to determine:
    1. Which tool the user wants to use
    2. What parameters to use
    """
    tools = ToolRegistry.get_openai_tools()

    if not tools:
        return ToolCallResult(needs_tool=False)

    system_prompt = """You are a bioinformatics analysis assistant. When users request analysis,
select the appropriate tool and extract parameters from their request.

Available tools and their purposes:
- volcano_plot: Differential expression visualization
- heatmap: Gene expression heatmap
- taxonomy_plot: Microbiome composition visualization
- alpha_diversity: Diversity index calculation

If the user provides data, extract it. If parameters are missing, use defaults."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

    try:
        # Use function calling
        response = await llm_router.chat(
            messages=messages,
            provider=LLMProvider.CLAUDE,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        # Check if tool was called
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_call = message.tool_calls[0]
            return ToolCallResult(
                needs_tool=True,
                tool_name=tool_call.function.name,
                tool_args=json.loads(tool_call.function.arguments),
                confidence=0.9
            )

        # No tool call - regular chat
        return ToolCallResult(
            needs_tool=False,
            response_text=message.content or ""
        )

    except Exception as e:
        return ToolCallResult(needs_tool=False, response_text=f"Error detecting tool: {str(e)}")


async def execute_tool_call(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool call and return results

    Args:
        tool_name: Name of the tool to execute
        args: Arguments for the tool

    Returns:
        Dict with success status, figure, and data
    """
    try:
        tool = ToolRegistry.get_tool(tool_name)

        # Validate input
        if not await tool.validate_input(args):
            return {
                "success": False,
                "error": "Invalid input parameters",
                "tool_name": tool_name
            }

        # Run analysis
        result = await tool.run(args)

        return {
            "success": result.success,
            "data": result.data,
            "figure": result.figure,
            "message": result.message,
            "error": result.error,
            "tool_name": tool_name
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tool_name": tool_name
        }


async def generate_chat_with_tools(
    messages: list,
    model: Optional[str] = None
):
    """
    Generate chat response with potential tool calls

    Yields:
        Response chunks (text or JSON for tool results)
    """
    # First, check if this requires a tool
    last_message = messages[-1]["content"] if messages else ""

    tool_result = await detect_tool_call(last_message)

    if tool_result.needs_tool and tool_result.tool_name:
        # Execute tool
        result = await execute_tool_call(tool_result.tool_name, tool_result.tool_args)

        # Yield tool call info
        yield json.dumps({
            "type": "tool_call",
            "tool_name": tool_result.tool_name,
            "args": tool_result.tool_args
        }) + "\n"

        # Yield result
        yield json.dumps({
            "type": "tool_result",
            "result": result
        }) + "\n"

    else:
        # Regular chat
        system_prompt = """You are BioCloud, an AI assistant specialized in bioinformatics analysis.
You help users with:
- Understanding bioinformatics concepts
- Guiding them through analysis workflows
- Explaining analysis results
- Answering questions about genomics, transcriptomics, proteomics, and microbiome research

Be helpful, accurate, and concise."""

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        async for chunk in llm_router.chat_stream(messages=full_messages, model=model):
            yield chunk