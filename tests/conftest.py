import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def test_vault():

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create some test files and folders
        notes_dir = os.path.join(tmp_dir, "Notes")
        projects_dir = os.path.join(tmp_dir, "Projects")
        os.makedirs(notes_dir)
        os.makedirs(projects_dir)
        
        # Create some test markdown files
        with open(os.path.join(notes_dir, "test1.md"), "w") as f:
            f.write("# Test File 1")
        with open(os.path.join(notes_dir, "test2.md"), "w") as f:
            f.write("# Test File 2")
        with open(os.path.join(projects_dir, "test3.md"), "w") as f:
            f.write("# Test File 3")
        
        yield tmp_dir

@pytest.fixture
def client(test_vault, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_API_VAULT_PATH", test_vault)
    monkeypatch.setenv("OBSIDIAN_API_KEY", "test-api-key")
    monkeypatch.setenv("OBSIDIAN_AUTH_ENABLED", "true")
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-api-key"} 