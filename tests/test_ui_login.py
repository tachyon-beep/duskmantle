from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gateway.api.app import create_app
from gateway.config.settings import get_settings
from tests.test_app_smoke import _stub_connection_managers


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_ui_login_flow(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.PathLike[str]) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))
    monkeypatch.setenv("KM_AUTH_ENABLED", "false")
    monkeypatch.setenv("KM_UI_LOGIN_ENABLED", "true")
    monkeypatch.setenv("KM_UI_PASSWORD", "secret-pass")
    monkeypatch.setenv("KM_UI_USERNAME", "console")
    monkeypatch.setenv("KM_UI_SESSION_SECURE_COOKIE", "false")
    monkeypatch.setenv("KM_STRICT_DEPENDENCY_STARTUP", "false")
    _stub_connection_managers(monkeypatch)

    app = create_app()
    client = TestClient(app)

    unauth = client.get("/ui/", follow_redirects=False)
    assert unauth.status_code == 303
    assert unauth.headers["Location"].startswith("/ui/login")

    login_page = client.get(unauth.headers["Location"])
    assert login_page.status_code == 200
    assert "Sign in" in login_page.text

    bad_login = client.post("/ui/login", data={"password": "wrong", "next": "/ui/subsystems"}, follow_redirects=False)
    assert bad_login.status_code == 303
    assert "error=invalid" in bad_login.headers["Location"]

    good_login = client.post("/ui/login", data={"password": "secret-pass", "next": "/ui/subsystems"}, follow_redirects=False)
    assert good_login.status_code == 303
    assert good_login.headers["Location"] == "/ui/subsystems"

    authorised = client.get("/ui/subsystems")
    assert authorised.status_code == 200

    logout = client.post("/ui/logout", follow_redirects=False)
    assert logout.status_code == 303
    assert logout.headers["Location"].startswith("/ui/login")

    back_to_login = client.get("/ui/", follow_redirects=False)
    assert back_to_login.status_code == 303


def test_ui_requires_token_when_login_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.PathLike[str]) -> None:
    monkeypatch.setenv("KM_STATE_PATH", str(tmp_path))
    monkeypatch.setenv("KM_AUTH_ENABLED", "true")
    monkeypatch.setenv("KM_ADMIN_TOKEN", "maintainer-token")
    monkeypatch.setenv("KM_READER_TOKEN", "reader-token")
    monkeypatch.setenv("KM_NEO4J_PASSWORD", "safe-pass")
    monkeypatch.delenv("KM_UI_LOGIN_ENABLED", raising=False)
    monkeypatch.setenv("KM_STRICT_DEPENDENCY_STARTUP", "false")
    monkeypatch.setenv("KM_UI_SESSION_SECURE_COOKIE", "false")
    _stub_connection_managers(monkeypatch)

    app = create_app()
    client = TestClient(app)

    without_token = client.get("/ui/", follow_redirects=False)
    assert without_token.status_code == 401

    with_token = client.get("/ui/", headers={"Authorization": "Bearer reader-token"})
    assert with_token.status_code == 200
