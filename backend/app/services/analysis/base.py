"""Base class for bioinformatics analysis tools"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolParameter(BaseModel):
    """Tool parameter definition"""
    name: str
    type: str = "string"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[str]] = None
    min_value: Optional[float] = Field(None, alias="min")
    max_value: Optional[float] = Field(None, alias="max")


class ToolDefinition(BaseModel):
    """Tool definition for LLM function calling"""
    name: str
    description: str
    parameters: List[ToolParameter]

    def to_openai_tool(self) -> Dict[str, Any]:
        """Convert to OpenAI tool format"""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.min_value is not None:
                prop["minimum"] = param.min_value
            if param.max_value is not None:
                prop["maximum"] = param.max_value
            if param.default is not None:
                prop["default"] = param.default

            properties[param.name] = prop
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        }


class AnalysisResult(BaseModel):
    """Analysis result"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    figure: Optional[Dict[str, Any]] = None  # Plotly figure JSON
    error: Optional[str] = None
    message: Optional[str] = None


class BaseAnalysis(ABC):
    """Base class for all bioinformatics analysis tools"""

    # Tool metadata (override in subclass)
    tool_name: str = ""
    tool_description: str = ""
    tool_category: str = ""  # genomics, transcriptomics, proteomics, microbiome

    @classmethod
    @abstractmethod
    def get_definition(cls) -> ToolDefinition:
        """Get tool definition for LLM"""
        pass

    @classmethod
    @abstractmethod
    def get_parameters_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for parameters validation"""
        pass

    @abstractmethod
    async def validate_input(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        pass

    @abstractmethod
    async def run(self, params: Dict[str, Any]) -> AnalysisResult:
        """Execute the analysis"""
        pass

    @abstractmethod
    async def generate_visualization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Plotly figure JSON"""
        pass