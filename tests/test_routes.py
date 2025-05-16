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

@pytest.fixture(autouse=True)
def reset_obsidian_auth(monkeypatch):
    monkeypatch.setenv("OBSIDIAN_AUTH_ENABLED", "false")
    monkeypatch.delenv("OBSIDIAN_API_KEY", raising=False)

@pytest.mark.parametrize(
    "route",
    [
        {"method": "GET", "route": "/files", "body": None},
        {"method": "GET", "route": "/folders", "body": None},
        {"method": "GET", "route": "/files/Notes/test1.md", "body": None},
        {"method": "GET", "route": "/folders/Notes", "body": None},
        {"method": "POST", "route": "/files/Notes/new_file.md", "body": {"frontmatter": {"title": "New Note", "tags": ["note", "test"]}, "body": "# New File"}},
        {"method": "POST", "route": "/folders/NewFolder", "body": None},
        {"method": "PATCH", "route": "/folders/Projects", "body": {"path": "Projects_moved"}},
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
                len(response.json()) == 4 and
                any(f["metadata"]["path"] == "Notes/test1.md" for f in response.json()) and
                any(f["metadata"]["path"] == "Notes/test2.md" for f in response.json()) and
                any(f["metadata"]["path"] == "Projects/test3.md" for f in response.json()) and
                any(f["metadata"]["path"] == "Notes/file_with_frontmatter.md" for f in response.json()) and
                all(f["metadata"]["type"] == "file" for f in response.json())
            )
        },{
            "method": "GET",
            "route": "/folders",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                len(response.json()) == 2 and
                any(f["metadata"]["path"] == "Notes" for f in response.json()) and
                any(f["metadata"]["path"] == "Projects" for f in response.json()) and
                all(f["metadata"]["type"] == "folder" for f in response.json())
            )
        },{
            "method": "GET",
            "route": "/files/Notes/test1.md",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "file" and
                response.json()["metadata"]["name"] == "test1.md" and
                response.json()["metadata"]["path"] == "Notes/test1.md" and
                response.json()["content"]["body"] == "# Test File 1" and
                response.json()["content"]["frontmatter"] is None and
                response.json()["metadata"]["size"] == len("# Test File 1") and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },{
            "method": "GET",
            "route": "/folders/Notes",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "folder" and
                response.json()["metadata"]["name"] == "Notes" and
                response.json()["metadata"]["path"] == "Notes" and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },{
            "method": "POST",
            "route": "/files/Notes/new_file.md",
            "body": {
                "frontmatter": {"title": "New Note", "tags": ["note", "test"]},
                "body": "# New File"
            },
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "file" and
                response.json()["metadata"]["name"] == "new_file.md" and
                response.json()["metadata"]["path"] == "Notes/new_file.md" and
                response.json()["content"]["body"] == "# New File" and
                response.json()["content"]["frontmatter"] == {"title": "New Note", "tags": ["note", "test"]} and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },
        {
            "method": "POST",
            "route": "/files/Notes/new_file_no_frontmatter.md",
            "body": {
                "body": "# New File Without Frontmatter"
            },
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "file" and
                response.json()["metadata"]["name"] == "new_file_no_frontmatter.md" and
                response.json()["metadata"]["path"] == "Notes/new_file_no_frontmatter.md" and
                response.json()["content"]["body"] == "# New File Without Frontmatter" and
                response.json()["content"]["frontmatter"] is None and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },
        {
            "method": "POST",
            "route": "/files/Notes/new_file_frontmatter_only.md",
            "body": {
                "frontmatter": {"title": "Frontmatter Only", "tags": ["test"]}
            },
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "file" and
                response.json()["metadata"]["name"] == "new_file_frontmatter_only.md" and
                response.json()["metadata"]["path"] == "Notes/new_file_frontmatter_only.md" and
                response.json()["content"]["body"] == "" and
                response.json()["content"]["frontmatter"] == {"title": "Frontmatter Only", "tags": ["test"]} and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },
        {
            "method": "POST",
            "route": "/folders/NewFolder",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "folder" and
                response.json()["metadata"]["name"] == "NewFolder" and
                response.json()["metadata"]["path"] == "NewFolder" and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },{
            "method": "PATCH",
            "route": "/folders/Projects",
            "body": {"path": "Projects_moved"},
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "folder" and
                response.json()["metadata"]["name"] == "Projects_moved" and
                response.json()["metadata"]["path"] == "Projects_moved" and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },{
            "method": "GET",
            "route": "/files/Notes/test1.md/raw",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.text == "# Test File 1"
            )
        },{
            "method": "GET",
            "route": "/files/Notes/test1.md/metadata",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["type"] == "file" and
                response.json()["name"] == "test1.md" and
                response.json()["path"] == "Notes/test1.md" and
                "body" not in response.json() and
                "frontmatter" not in response.json() and
                response.json()["size"] == len("# Test File 1") and
                is_iso_timestamp(response.json().get("created", "")) and
                is_iso_timestamp(response.json().get("modified", ""))
            )
        },{
            "method": "GET",
            "route": "/files/Notes/test1.md/frontmatter",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json() == {}
            )
        },{
            "method": "GET",
            "route": "/files/Notes/test1.md/body",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.text == "# Test File 1"
            )
        },{
            "method": "GET",
            "route": "/files/Notes/file_with_frontmatter.md",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "file" and
                response.json()["metadata"]["name"] == "file_with_frontmatter.md" and
                response.json()["metadata"]["path"] == "Notes/file_with_frontmatter.md" and
                response.json()["content"]["body"] == "# New File" and
                response.json()["content"]["frontmatter"] == {"title": "New Note", "tags": ["note", "test"]} and
                response.json()["metadata"]["size"] == len("---\ntitle: New Note\ntags: [note, test]\n---\n# New File") and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },{
            "method": "GET",
            "route": "/files/Notes/file_with_frontmatter.md/raw",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.text == "---\ntitle: New Note\ntags: [note, test]\n---\n# New File"
            )
        },{
            "method": "GET",
            "route": "/files/Notes/file_with_frontmatter.md/metadata",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["type"] == "file" and
                response.json()["name"] == "file_with_frontmatter.md" and
                response.json()["path"] == "Notes/file_with_frontmatter.md" and
                "body" not in response.json() and
                "frontmatter" not in response.json() and
                response.json()["size"] == len("---\ntitle: New Note\ntags: [note, test]\n---\n# New File") and
                is_iso_timestamp(response.json().get("created", "")) and
                is_iso_timestamp(response.json().get("modified", ""))
            )
        },{
            "method": "GET",
            "route": "/files/Notes/file_with_frontmatter.md/frontmatter",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json() == {"title": "New Note", "tags": ["note", "test"]}
            )
        },{
            "method": "GET",
            "route": "/files/Notes/file_with_frontmatter.md/body",
            "body": None,
            "expected_status": 200,
            "verify_response": lambda response: (
                response.text == "# New File"
            )
        },
        {
            "method": "POST",
            "route": "/files/Notes/new_file_raw.md/raw",
            "body": "---\ntitle: Raw Note\ntags: [raw, test]\n---\n# Raw File Content",
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "file" and
                response.json()["metadata"]["name"] == "new_file_raw.md" and
                response.json()["metadata"]["path"] == "Notes/new_file_raw.md" and
                response.json()["content"]["body"] == "# Raw File Content" and
                response.json()["content"]["frontmatter"] == {"title": "Raw Note", "tags": ["raw", "test"]} and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },
        {
            "method": "PUT",
            "route": "/files/Notes/test1.md/raw",
            "body": "---\ntitle: Updated Raw\ntags: [updated]\n---\n# Updated Raw Content",
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "file" and
                response.json()["metadata"]["name"] == "test1.md" and
                response.json()["metadata"]["path"] == "Notes/test1.md" and
                response.json()["content"]["body"] == "# Updated Raw Content" and
                response.json()["content"]["frontmatter"] == {"title": "Updated Raw", "tags": ["updated"]} and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },
        {
            "method": "PUT",
            "route": "/files/Notes/test1.md/frontmatter",
            "body": {"title": "Updated Frontmatter", "tags": ["updated"]},
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "file" and
                response.json()["metadata"]["name"] == "test1.md" and
                response.json()["metadata"]["path"] == "Notes/test1.md" and
                response.json()["content"]["frontmatter"] == {"title": "Updated Frontmatter", "tags": ["updated"]} and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },
        {
            "method": "PUT",
            "route": "/files/Notes/test1.md/body",
            "body": "# Updated Body Content",
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "file" and
                response.json()["metadata"]["name"] == "test1.md" and
                response.json()["metadata"]["path"] == "Notes/test1.md" and
                response.json()["content"]["body"] == "# Updated Body Content" and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
            )
        },
        {
            "method": "PATCH",
            "route": "/files/Notes/test1.md/frontmatter",
            "body": {"new_tag": "patched"},
            "expected_status": 200,
            "verify_response": lambda response: (
                response.json()["metadata"]["type"] == "file" and
                response.json()["metadata"]["name"] == "test1.md" and
                response.json()["metadata"]["path"] == "Notes/test1.md" and
                response.json()["content"]["frontmatter"] == {"new_tag": "patched"} and
                is_iso_timestamp(response.json()["metadata"].get("created", "")) and
                is_iso_timestamp(response.json()["metadata"].get("modified", ""))
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
    if auth_enabled:
        monkeypatch.setenv("OBSIDIAN_AUTH_ENABLED", "true")
        monkeypatch.setenv("OBSIDIAN_API_KEY", "valid-test-token")
        headers = {"Authorization": "Bearer valid-test-token"}
    else:
        monkeypatch.setenv("OBSIDIAN_AUTH_ENABLED", "false")
        headers = {}
    
    req = getattr(client, test_case["method"].lower())
    
    # Handle different request types
    if test_case["method"] == "GET":
        response = req(test_case["route"], headers=headers)
    elif test_case["route"].endswith("/raw") and test_case["method"] in ["POST", "PUT"]:
        response = req(test_case["route"], content=test_case["body"], headers=headers)
    elif test_case["route"].endswith("/body") and test_case["method"] == "PUT":
        response = req(test_case["route"], content=test_case["body"], headers=headers)
    else:
        response = req(test_case["route"], json=test_case["body"], headers=headers)
    
    assert response.status_code == test_case["expected_status"]
    if test_case["verify_response"]:
        test_case["verify_response"](response)

@pytest.mark.parametrize(
    "test_case",
    [
        {
            "name": "Non-existent resource",
            "method": "GET",
            "route": "/nonexistent.md",
            "body": None,
            "expected_status": 404
        },
        {
            "name": "File already exists",
            "method": "POST",
            "route": "/files/Notes/test1.md",
            "body": {"frontmatter": {}, "body": ""},
            "expected_status": 409
        },
        {
            "name": "File patch already exists",
            "method": "PATCH",
            "route": "/files/Notes/test1.md/metadata",
            "body": {"path": "Notes/test2.md"},
            "expected_status": 409
        },
        {
            "name": "Invalid path for move operation",
            "method": "PATCH",
            "route": "/files/Notes/test1.md/metadata",
            "body": {"path": "../invalid/path.md"},
            "expected_status": 400
        },
        {
            "name": "Invalid folder path",
            "method": "POST",
            "route": "/folders/../invalid/folder",
            "body": None,
            "expected_status": 404
        },
        {
            "name": "Invalid file path (GET)",
            "method": "GET",
            "route": "/files/../invalid/file.md",
            "body": None,
            "expected_status": 404
        },
        {
            "name": "Invalid file path (POST)",
            "method": "POST",
            "route": "/files/../invalid/file.md",
            "body": {"frontmatter": {}, "body": ""},
            "expected_status": 404
        }
    ],
    ids=lambda case: case["name"]
)
def test_route_exceptions(client, test_case):
    req = getattr(client, test_case["method"].lower())
    
    # Handle different request types
    if test_case["method"] == "GET":
        response = req(test_case["route"])
    elif test_case["route"].endswith("/raw") or test_case["route"].endswith("/body"):
        response = req(test_case["route"], content=test_case["body"])
    else:
        response = req(test_case["route"], json=test_case["body"])
    
    assert response.status_code == test_case["expected_status"]

def test_hidden_directories(client):
    dot_dir = Path(os.getenv("OBSIDIAN_API_VAULT_PATH")) / ".hidden"
    dot_dir.mkdir()
    (dot_dir / "test.md").write_text("# Hidden File")
    
    response = client.get("/files")
    assert response.status_code == 200
    files = response.json()
    assert len(files) == 4
    assert any(f["metadata"]["path"] == "Notes/test1.md" for f in files)
    assert any(f["metadata"]["path"] == "Notes/test2.md" for f in files)
    assert any(f["metadata"]["path"] == "Projects/test3.md" for f in files)
    assert any(f["metadata"]["path"] == "Notes/file_with_frontmatter.md" for f in files)
    assert not any(f["metadata"]["path"] == ".hidden/test.md" for f in files)
    
    response = client.get("/folders")
    assert response.status_code == 200
    folders = response.json()
    assert len(folders) == 2
    assert any(f["metadata"]["path"] == "Notes" for f in folders)
    assert any(f["metadata"]["path"] == "Projects" for f in folders)
    assert not any(f["metadata"]["path"] == ".hidden" for f in folders)

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
    response = client.post(f"/files/{encoded_path}", json={"frontmatter": {}, "body": "# Test Content"})
    assert response.status_code == 200
    assert response.json()["content"]["body"] == "# Test Content"
    
    # Test reading file with raw path
    response = client.get(f"/files/{path}")
    assert response.status_code == 200
    assert response.json()["content"]["body"] == "# Test Content"
    assert response.json()["metadata"]["type"] == "file"
    
    # Test reading file with URL-encoded path
    response = client.get(f"/files/{encoded_path}")
    assert response.status_code == 200
    assert response.json()["content"]["body"] == "# Test Content"
    assert response.json()["metadata"]["type"] == "file"