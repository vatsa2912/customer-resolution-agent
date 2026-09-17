from typing import Callable, Dict, Any, List

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, parameters: Dict[str, Any]):
        def decorator(func: Callable):
            self._tools[name] = func
            self._schemas[name] = {
                "name": name,
                "description": description,
                "parameters": parameters
            }
            return func
        return decorator

    def execute(self, name: str, **kwargs) -> Dict[str, Any]:
        if name not in self._tools:
            return {"success": False, "error": f"Tool '{name}' is not registered."}
        try:
            result = self._tools[name](**kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return list(self._schemas.values())

default_tool_registry = ToolRegistry()
