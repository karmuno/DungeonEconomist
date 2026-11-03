from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.frontend import mount_frontend

SECRET = "this file is outside dist"
INDEX_HTML = "<html>venturekeep</html>"


@pytest.fixture
def secret_file(tmp_path: Path) -> Path:
    """A file two levels above dist, the depth of the repo root from frontend/dist."""
    secret = tmp_path / "secret.txt"
    secret.write_text(SECRET)
    return secret


@pytest.fixture
def client(tmp_path: Path, secret_file: Path) -> TestClient:
    dist = tmp_path / "frontend" / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text(INDEX_HTML)
    (dist / "favicon.png").write_text("favicon")
    (dist / "assets" / "app.js").write_text("app")

    app = FastAPI()

    @app.get("/keeps/")
    def list_keeps() -> list[str]:
        return ["a keep"]

    mount_frontend(app, dist)
    return TestClient(app)


@pytest.mark.parametrize(
    "path",
    [
        "/..%2f..%2fsecret.txt",
        "/%2e%2e%2f%2e%2e%2fsecret.txt",
        "/..%5c..%5csecret.txt",
        "/assets/..%2f..%2f..%2fsecret.txt",
    ],
)
def test_relative_escape_does_not_serve_file_outside_dist(client: TestClient, path: str):
    assert SECRET not in client.get(path).text


def test_absolute_path_does_not_serve_file_outside_dist(client: TestClient, secret_file: Path):
    assert SECRET not in client.get("/" + secret_file.as_posix()).text


def test_encoded_absolute_path_does_not_serve_file_outside_dist(client: TestClient, secret_file: Path):
    assert SECRET not in client.get("/" + quote(secret_file.as_posix(), safe="")).text


def test_null_byte_falls_back_to_spa(client: TestClient):
    response = client.get("/favicon%00.png")
    assert response.status_code == 200
    assert response.text == INDEX_HTML


@pytest.mark.parametrize("path", ["/api", "/api/", "/api/does-not-exist"])
def test_unknown_api_path_is_404_not_spa(client: TestClient, path: str):
    response = client.get(path)
    assert response.status_code == 404
    assert INDEX_HTML not in response.text


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/", INDEX_HTML),
        ("/keeps/1/dashboard", INDEX_HTML),
        ("/apiary", INDEX_HTML),
        ("/favicon.png", "favicon"),
        ("/assets/app.js", "app"),
    ],
)
def test_spa_routes_and_build_files_still_served(client: TestClient, path: str, body: str):
    response = client.get(path)
    assert response.status_code == 200
    assert response.text == body


def test_api_routes_win_over_catch_all(client: TestClient):
    assert client.get("/keeps/").json() == ["a keep"]
