import os
from pathlib import Path
import pytest
from datetime import datetime
import re

# Add at the top of the file
ISO_TIMESTAMP_PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$'

def is_iso_timestamp(timestamp):
    """Check if a string is a valid ISO 8601 timestamp"""
    return bool(re.match(ISO_TIMESTAMP_PATTERN, timestamp))

def test_missing_api_key(client, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_AUTH_ENABLED", "true")
    monkeypatch.delenv("OBSIDIAN_API_KEY", raising=False)
    
    response = client.get("/files")
    assert response.status_code == 500
    assert response.json()["detail"] == "API key not configured. Set OBSIDIAN_API_KEY environment variable."

@pytest.mark.parametrize(
    "route",
    [
        {"method": "GET", "route": "/files", "body": None},
        {"method": "GET", "route": "/folders", "body": None},
        {"method": "GET", "route": "/files/Notes/test1.md", "body": None},
        {"method": "GET", "route": "/folders/Notes", "body": None},
        {"method": "POST", "route": "/files/Notes/new_file.md", "body": {"content": "# New File"}},
        {"method": "POST", "route": "/folders/NewFolder", "body": None},
        {"method": "PUT", "route": "/files/Notes/test1.md", "body": {"content": "# Updated Content"}},
        {"method": "PATCH", "route": "/files/Notes/test1.md", "body": {"new_path": "Notes/moved.md"}},
        {"method": "PATCH", "route": "/folders/Projects", "body": {"new_path": "Projects_moved"}},
    ],
    ids=lambda route: f"{route['method']} {route['route']}"
)
@pytest.mark.parametrize(
    "authScenario",
    [
        {
            "name": "MissingHeader",
            "headers": {},
            "expected_status": 401,
            "expected_message": "Missing authorization header"
        },{
            "name": "MissingScheme",
            "headers": {"Authorization": "invalid-format"},
            "expected_status": 401,
            "expected_message": "Wrong authorization scheme"
        },{
            "name": "WrongScheme",
            "headers": {"Authorization": "Basic invalid-token"},
            "expected_status": 401,
            "expected_message": "Wrong authorization scheme"
        },{
            "name": "MissingToken",
            "headers": {"Authorization": "Bearer"},
            "expected_status": 401,
            "expected_message": "Missing authorization token"
        },{
            "name": "InvalidToken",
            "headers": {"Authorization": "Bearer invalid-token"},
            "expected_status": 401,
            "expected_message": "Invalid authorization token"
        },{
            "name": "ValidToken",
            "headers": {"Authorization": "Bearer valid-test-token"},
            "expected_status": 200,
            "expected_message": None
        }
    ],
    ids=lambda scenario: scenario["name"]
)
def test_auth_exceptions(client, monkeypatch, authScenario, route):
    monkeypatch.setenv("OBSIDIAN_AUTH_ENABLED", "true")
    monkeypatch.setenv("OBSIDIAN_API_KEY", "valid-test-token")
    
    req = getattr(client, route["method"].lower())
    if route["body"]:
        response = req(route["route"], json=route["body"], headers=authScenario["headers"])
    else:
        response = req(route["route"], headers=authScenario["headers"])
    
    assert response.status_code == authScenario["expected_status"]
    if authScenario["expected_message"]:
        assert response.json()["detail"] == authScenario["expected_message"]

@pytest.mark.parametrize(
    "test_case",
    [
        {
            "method": "GET",
            "route": "/files",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                len(response.json()) == 3 and
                any(f["path"] == "Notes/test1.md" for f in response.json()) and
                any(f["path"] == "Notes/test2.md" for f in response.json()) and
                any(f["path"] == "Projects/test3.md" for f in response.json()) and
                all(f["type"] == "file" for f in response.json())
            )
        },{
            "method": "GET",
            "route": "/folders",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                len(response.json()) == 2 and
                any(f["path"] == "Notes" for f in response.json()) and
                any(f["path"] == "Projects" for f in response.json()) and
                all(f["type"] == "folder" for f in response.json())
            )
        },{
            "method": "GET",
            "route": "/files/Notes/test1.md",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["type"] == "file" and
                response.json()["name"] == "test1.md" and
                response.json()["path"] == "Notes/test1.md" and
                response.json()["content"] == "# Test File 1" and
                response.json()["size"] == len("# Test File 1") and
                is_iso_timestamp(response.json().get("created", "")) and
                is_iso_timestamp(response.json().get("modified", ""))
            )
        },{
            "method": "GET",
            "route": "/folders/Notes",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["type"] == "folder" and
                response.json()["name"] == "Notes" and
                response.json()["path"] == "Notes" and
                is_iso_timestamp(response.json().get("created", "")) and
                is_iso_timestamp(response.json().get("modified", ""))
            )
        },{
            "method": "POST",
            "route": "/files/Notes/new_file.md",
            "body": {"content": "# New File"},
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["type"] == "file" and
                response.json()["name"] == "new_file.md" and
                response.json()["path"] == "Notes/new_file.md" and
                response.json()["content"] == "# New File" and
                response.json()["size"] == len("# New File") and
                is_iso_timestamp(response.json().get("created", "")) and
                is_iso_timestamp(response.json().get("modified", ""))
            )
        },{
            "method": "POST",
            "route": "/folders/NewFolder",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["type"] == "folder" and
                response.json()["name"] == "NewFolder" and
                response.json()["path"] == "NewFolder" and
                is_iso_timestamp(response.json().get("created", "")) and
                is_iso_timestamp(response.json().get("modified", ""))
            )
        },{
            "method": "PUT",
            "route": "/files/Notes/test1.md",
            "body": {"content": "# Updated Content"},
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["type"] == "file" and
                response.json()["name"] == "test1.md" and
                response.json()["path"] == "Notes/test1.md" and
                response.json()["content"] == "# Updated Content" and
                response.json()["size"] == len("# Updated Content") and
                is_iso_timestamp(response.json().get("created", "")) and
                is_iso_timestamp(response.json().get("modified", ""))
            )
        },{
            "method": "PATCH",
            "route": "/files/Notes/test1.md",
            "body": {"new_path": "Notes/moved.md"},
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["type"] == "file" and
                response.json()["name"] == "moved.md" and
                response.json()["path"] == "Notes/moved.md" and
                response.json()["content"] == "# Test File 1" and
                response.json()["size"] == len("# Test File 1") and
                is_iso_timestamp(response.json().get("created", "")) and
                is_iso_timestamp(response.json().get("modified", ""))
            )
        },{
            "method": "PATCH",
            "route": "/folders/Projects",
            "body": {"new_path": "Projects_moved"},
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["type"] == "folder" and
                response.json()["name"] == "Projects_moved" and
                response.json()["path"] == "Projects_moved" and
                is_iso_timestamp(response.json().get("created", "")) and
                is_iso_timestamp(response.json().get("modified", ""))
            )
        }
    ],
    ids=lambda case: f"{case['method']} {case['route']}"
)
@pytest.mark.parametrize(
    "auth_enabled", 
    [True, False],
    ids=lambda enabled: "Auth" if enabled else "NoAuth"
)
def test_successful_operations(client, test_case, auth_enabled, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_AUTH_ENABLED", str(auth_enabled).lower())
    if auth_enabled:
        monkeypatch.setenv("OBSIDIAN_API_KEY", "test-api-key")
        headers = {"Authorization": "Bearer test-api-key"}
    else:
        headers = {}
    
    req = getattr(client, test_case["method"].lower())
    
    if test_case["body"]:
        response = req(test_case["route"], json=test_case["body"], headers=headers)
    else:
        response = req(test_case["route"], headers=headers)
    
    assert response.status_code == test_case["expected_status"]
    
    # Add debug logging for failing tests
    if "folders" in test_case["route"]:
        print(f"\nResponse for {test_case['route']}:")
        print(f"Status: {response.status_code}")
        print(f"Content: {response.json()}")
    
    assert test_case["verify_response"](response)

def test_route_exceptions(client):
    response = client.get("/nonexistent.md")
    assert response.status_code == 404
    
    response = client.post("/files/Notes/test1.md", content="", headers={"Content-Type": "text/plain"})
    assert response.status_code == 400
    
    response = client.patch("/files/Notes/test2.md", json={"new_path": "Notes/test1.md"})
    assert response.status_code == 400

def test_hidden_directories(client):
    dot_dir = Path(os.getenv("OBSIDIAN_API_VAULT_PATH")) / ".hidden"
    dot_dir.mkdir()
    (dot_dir / "test.md").write_text("# Hidden File")
    
    response = client.get("/files")
    assert response.status_code == 200
    files = response.json()
    assert len(files) == 3
    assert any(f["path"] == "Notes/test1.md" for f in files)
    assert any(f["path"] == "Notes/test2.md" for f in files)
    assert any(f["path"] == "Projects/test3.md" for f in files)
    assert not any(f["path"] == ".hidden/test.md" for f in files)
    
    response = client.get("/folders")
    assert response.status_code == 200
    folders = response.json()
    assert len(folders) == 2
    assert any(f["path"] == "Notes" for f in folders)
    assert any(f["path"] == "Projects" for f in folders)
    assert not any(f["path"] == ".hidden" for f in folders)

    response = client.get("/files/.hidden/test.md")
    assert response.status_code == 404

    response = client.get("/folders/.hidden")
    assert response.status_code == 404

@pytest.mark.parametrize(
    "path,encoded_path", 
    [
        ("Notes/Test File With Spaces.md", "Notes/Test%20File%20With%20Spaces.md"),
        ("Notes/File With Multiple  Spaces.md", "Notes/File%20With%20Multiple%20%20Spaces.md")
    ],
    ids=lambda path: path
)
def test_paths_with_spaces(client, path, encoded_path):
    # Test creating file with spaces
    response = client.post(f"/files/{path}", json={"content": "# Test Content"})
    assert response.status_code == 200
    assert response.json()["path"] == path
    assert response.json()["type"] == "file"
    assert response.json()["content"] == "# Test Content"
    
    # Test reading file with raw path
    response = client.get(f"/files/{path}")
    assert response.status_code == 200
    assert response.json()["content"] == "# Test Content"
    assert response.json()["type"] == "file"
    
    # Test reading file with URL-encoded path
    response = client.get(f"/files/{encoded_path}")
    assert response.status_code == 200
    assert response.json()["content"] == "# Test Content"
    assert response.json()["type"] == "file"