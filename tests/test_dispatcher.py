from core.permissions import PermissionLevel
from core.router import ToolDispatcher
from core.session import SessionContext
from core.tool_registry import Tool, ToolParameter, ToolRegistry


def safe_handler(text="", mock_mode=False, session=None, **_):
    return {"success": True, "message": f"echoed {text}", "data": {"text": text}}


def confirm_handler(path="", mock_mode=False, session=None, **_):
    return {"success": True, "message": f"deleted {path}", "data": {"path": path}}


def restricted_handler(mock_mode=False, session=None, **_):
    return {"success": True, "message": "should never run", "data": None}


def exploding_handler(mock_mode=False, session=None, **_):
    raise RuntimeError("boom")


def build_registry():
    registry = ToolRegistry()
    registry.register(Tool("safe_echo", "", PermissionLevel.SAFE, safe_handler, (ToolParameter("text", "string"),)))
    registry.register(Tool("delete_thing", "", PermissionLevel.CONFIRM, confirm_handler, (ToolParameter("path", "string"),)))
    registry.register(Tool("nuke", "", PermissionLevel.RESTRICTED, restricted_handler, ()))
    registry.register(Tool("boom", "", PermissionLevel.SAFE, exploding_handler, ()))
    return registry


def make_dispatcher():
    return ToolDispatcher(registry=build_registry(), session=SessionContext(), mock_mode=True)


def test_unknown_tool_fails_cleanly():
    d = make_dispatcher()
    outcome = d.dispatch("does_not_exist", {})
    assert outcome.executed is False
    assert outcome.result["success"] is False


def test_safe_tool_executes_immediately():
    d = make_dispatcher()
    outcome = d.dispatch("safe_echo", {"text": "hi"})
    assert outcome.executed is True
    assert outcome.result["success"] is True
    assert outcome.result["data"]["text"] == "hi"


def test_invalid_args_are_rejected_before_execution():
    d = make_dispatcher()
    outcome = d.dispatch("safe_echo", {"wrong_arg": "hi"})
    assert outcome.executed is False
    assert outcome.result["success"] is False


def test_restricted_tool_is_always_denied():
    d = make_dispatcher()
    outcome = d.dispatch("nuke", {})
    assert outcome.executed is False
    assert "restricted" in outcome.result["message"].lower()


def test_confirm_tool_requires_confirmation_first():
    d = make_dispatcher()
    outcome = d.dispatch("delete_thing", {"path": "C:/x.txt"})
    assert outcome.executed is False
    assert outcome.result["data"]["needs_confirmation"] is True
    token = outcome.result["data"]["confirmation_token"]

    # now confirm with the exact same args
    outcome2 = d.dispatch("delete_thing", {"path": "C:/x.txt", "_confirmation_token": token})
    assert outcome2.executed is True
    assert outcome2.result["success"] is True


def test_confirm_token_cannot_be_reused_for_different_args():
    d = make_dispatcher()
    outcome = d.dispatch("delete_thing", {"path": "C:/x.txt"})
    token = outcome.result["data"]["confirmation_token"]

    outcome2 = d.dispatch("delete_thing", {"path": "C:/DIFFERENT.txt", "_confirmation_token": token})
    assert outcome2.executed is False


def test_handler_exception_is_caught_and_structured():
    d = make_dispatcher()
    outcome = d.dispatch("boom", {})
    assert outcome.executed is False
    assert outcome.result["success"] is False
    assert "boom" in outcome.result["message"]


def test_session_records_history():
    d = make_dispatcher()
    d.dispatch("safe_echo", {"text": "hi"})
    assert len(d.session.history) == 1
    assert d.session.history[0].tool_name == "safe_echo"
