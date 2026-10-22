from tools.applications import list_applications, open_application, resolve_application


def test_resolve_known_alias():
    resolved = resolve_application("vs code")
    assert resolved is not None
    assert resolved.key == "vscode"


def test_resolve_case_insensitive_and_fuzzy():
    resolved = resolve_application("please open Google Chrome")
    assert resolved is not None
    assert resolved.key == "chrome"


def test_resolve_unknown_app():
    assert resolve_application("some_totally_unknown_app_xyz") is None


def test_open_application_mock_mode_unknown_app():
    result = open_application("totally_unknown_app_xyz", mock_mode=True)
    assert result["success"] is False


def test_open_application_mock_mode_known_app():
    result = open_application("Notepad", mock_mode=True)
    assert result["success"] is True
    assert "[mock]" in result["message"]


def test_list_applications_returns_results():
    result = list_applications()
    assert result["success"] is True
    assert len(result["data"]["results"]) > 0
