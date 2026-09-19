"""
Base tool definitions and schema converter for Gemini Function Calling.
"""

from typing import Dict, Any, Callable, List, Optional
import inspect

class BaseTool:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any],
        is_dangerous: bool = False,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.is_dangerous = is_dangerous

    def to_gemini_schema(self) -> Dict[str, Any]:
        """Convert to Gemini FunctionDeclaration format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    async def execute(self, **kwargs) -> Any:
        if inspect.iscoroutinefunction(self.handler):
            return await self.handler(**kwargs)
        return self.handler(**kwargs)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def to_gemini_tools(self) -> List[Dict[str, Any]]:
        declarations = [tool.to_gemini_schema() for tool in self._tools.values()]
        return [{"functionDeclarations": declarations}]

# Global registry
registry = ToolRegistry()
