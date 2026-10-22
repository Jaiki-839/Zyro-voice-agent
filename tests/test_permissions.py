import time

from core.permissions import ConfirmationManager, PendingConfirmation, PermissionLevel


def test_permission_levels_exist():
    assert PermissionLevel.SAFE == "SAFE"
    assert PermissionLevel.CONFIRM == "CONFIRM"
    assert PermissionLevel.RESTRICTED == "RESTRICTED"


def test_confirmation_round_trip():
    mgr = ConfirmationManager()
    ticket = mgr.request("delete_file", {"path": "C:/x.txt"})
    assert mgr.confirm(ticket.token, "delete_file", {"path": "C:/x.txt"}) is True


def test_confirmation_is_one_shot():
    mgr = ConfirmationManager()
    ticket = mgr.request("delete_file", {"path": "C:/x.txt"})
    assert mgr.confirm(ticket.token, "delete_file", {"path": "C:/x.txt"}) is True
    # replaying the same token must fail
    assert mgr.confirm(ticket.token, "delete_file", {"path": "C:/x.txt"}) is False


def test_confirmation_rejects_mismatched_args():
    mgr = ConfirmationManager()
    ticket = mgr.request("delete_file", {"path": "C:/x.txt"})
    assert mgr.confirm(ticket.token, "delete_file", {"path": "C:/other.txt"}) is False


def test_confirmation_rejects_mismatched_tool():
    mgr = ConfirmationManager()
    ticket = mgr.request("delete_file", {"path": "C:/x.txt"})
    assert mgr.confirm(ticket.token, "bulk_delete", {"path": "C:/x.txt"}) is False


def test_confirmation_rejects_unknown_token():
    mgr = ConfirmationManager()
    assert mgr.confirm("not-a-real-token", "delete_file", {"path": "C:/x.txt"}) is False


def test_confirmation_expires():
    ticket = PendingConfirmation(
        token="t", tool_name="x", args_fingerprint="x:[]", created_at=time.time() - 1000, ttl_seconds=1.0
    )
    assert ticket.is_expired() is True
