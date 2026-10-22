import pytest

from core.permissions import PermissionLevel
from core.tool_registry import Tool, ToolParameter, ToolRegistry, ToolValidationError


def _dummy_handler(**kwargs):
    return {"success": True, "message": "ok", "data": kwargs}


def make_tool():
    return Tool(
        name="echo",
        description="Echoes its argument.",
        permission=PermissionLevel.SAFE,
        handler=_dummy_handler,
        parameters=(ToolParameter("text", "string", "text to echo"),),
    )


def test_register_and_get():
    registry = ToolRegistry()
    tool = make_tool()
    registry.register(tool)
    assert registry.get("echo") is tool
    assert registry.exists("echo") is True
    assert registry.exists("nope") is False


def test_duplicate_registration_raises():
    registry = ToolRegistry()
    registry.register(make_tool())
    with pytest.raises(ValueError):
        registry.register(make_tool())


def test_validate_args_ok():
    tool = make_tool()
    validated = tool.validate_args({"text": "hi"})
    assert validated == {"text": "hi"}


def test_validate_args_missing_required():
    tool = make_tool()
    with pytest.raises(ToolValidationError):
        tool.validate_args({})


def test_validate_args_wrong_type():
    tool = make_tool()
    with pytest.raises(ToolValidationError):
        tool.validate_args({"text": 123})


def test_validate_args_unexpected_arg():
    tool = make_tool()
    with pytest.raises(ToolValidationError):
        tool.validate_args({"text": "hi", "extra": "nope"})


def test_optional_param_with_default():
    tool = Tool(
        name="greet",
        description="",
        permission=PermissionLevel.SAFE,
        handler=_dummy_handler,
        parameters=(ToolParameter("name", "string", required=False, default="world"),),
    )
    assert tool.validate_args({}) == {"name": "world"}


def test_enum_validation():
    tool = Tool(
        name="pick",
        description="",
        permission=PermissionLevel.SAFE,
        handler=_dummy_handler,
        parameters=(ToolParameter("choice", "string", enum=("a", "b")),),
    )
    assert tool.validate_args({"choice": "a"}) == {"choice": "a"}
    with pytest.raises(ToolValidationError):
        tool.validate_args({"choice": "z"})


def test_gemini_function_declaration_shape():
    registry = ToolRegistry()
    registry.register(make_tool())
    decls = registry.to_gemini_function_declarations()
    assert decls[0]["name"] == "echo"
    assert decls[0]["parameters"]["required"] == ["text"]
    assert "text" in decls[0]["parameters"]["properties"]
