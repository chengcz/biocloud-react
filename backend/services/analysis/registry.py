"""Tool registry for managing bioinformatics analysis tools"""

from typing import Dict, Type, List, Any
from .base import BaseAnalysis, ToolDefinition


class ToolRegistry:
    """Registry for all available analysis tools"""

    _tools: Dict[str, Type[BaseAnalysis]] = {}
    _definitions: Dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, tool_class: Type[BaseAnalysis]) -> Type[BaseAnalysis]:
        """Register a tool class"""
        if not tool_class.tool_name:
            raise ValueError(f"Tool class {tool_class.__name__} has no tool_name")

        cls._tools[tool_class.tool_name] = tool_class
        cls._definitions[tool_class.tool_name] = tool_class.get_definition()
        return tool_class

    @classmethod
    def get_tool(cls, name: str) -> BaseAnalysis:
        """Get an instance of a tool by name"""
        if name not in cls._tools:
            raise ValueError(f"Tool '{name}' not found")
        return cls._tools[name]()

    @classmethod
    def get_definition(cls, name: str) -> ToolDefinition:
        """Get tool definition by name"""
        if name not in cls._definitions:
            raise ValueError(f"Tool '{name}' not found")
        return cls._definitions[name]

    @classmethod
    def list_tools(cls) -> List[str]:
        """List all registered tool names"""
        return list(cls._tools.keys())

    @classmethod
    def get_all_definitions(cls) -> List[ToolDefinition]:
        """Get all tool definitions"""
        return list(cls._definitions.values())

    @classmethod
    def get_openai_tools(cls) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI function calling format"""
        return [defn.to_openai_tool() for defn in cls._definitions.values()]

    @classmethod
    def get_tools_by_category(cls) -> Dict[str, List[str]]:
        """Get tools grouped by category"""
        categories = {}
        for name, tool_class in cls._tools.items():
            category = tool_class.tool_category or "other"
            if category not in categories:
                categories[category] = []
            categories[category].append(name)
        return categories


def register_tool(tool_class: Type[BaseAnalysis]) -> Type[BaseAnalysis]:
    """Decorator to register a tool"""
    return ToolRegistry.register(tool_class)