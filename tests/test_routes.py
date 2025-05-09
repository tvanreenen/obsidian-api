import os
from pathlib import Path
import pytest
from datetime import datetime

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
            "expected_content": None,
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
            "expected_content": None,
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
            "expected_content": {
                "type": "file",
                "name": "test1.md",
                "path": "Notes/test1.md",
                "content": "# Test File 1",
                "size": len("# Test File 1")
            }
        },{
            "method": "GET",
            "route": "/folders/Notes",
            "body": None,
            "expected_status": 200,
            "expected_content": {
                "type": "folder",
                "name": "Notes",
                "path": "Notes",
                "children": []
            }
        },{
            "method": "POST",
            "route": "/files/Notes/new_file.md",
            "body": {"content": "# New File"},
            "expected_status": 200,
            "expected_content": {
                "type": "file",
                "name": "new_file.md",
                "path": "Notes/new_file.md",
                "content": "# New File",
                "size": len("# New File")
            }
        },{
            "method": "POST",
            "route": "/folders/NewFolder",
            "body": None,
            "expected_status": 200,
            "expected_content": {
                "type": "folder",
                "name": "NewFolder",
                "path": "NewFolder",
                "children": []
            }
        },{
            "method": "PUT",
            "route": "/files/Notes/test1.md",
            "body": {"content": "# Updated Content"},
            "expected_status": 200,
            "expected_content": {
                "type": "file",
                "name": "test1.md",
                "path": "Notes/test1.md",
                "content": "# Updated Content",
                "size": len("# Updated Content")
            }
        },{
            "method": "PATCH",
            "route": "/files/Notes/test1.md",
            "body": {"new_path": "Notes/moved.md"},
            "expected_status": 200,
            "expected_content": {
                "type": "file",
                "name": "moved.md",
                "path": "Notes/moved.md",
                "content": "# Test File 1",
                "size": len("# Test File 1")
            }
        },{
            "method": "PATCH",
            "route": "/folders/Projects",
            "body": {"new_path": "Projects_moved"},
            "expected_status": 200,
            "expected_content": {
                "type": "folder",
                "name": "Projects_moved",
                "path": "Projects_moved",
                "children": []
            }
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
    
    if test_case["expected_content"]:
        response_json = response.json()
        
        # Verify timestamps exist and are valid
        if 'created' in response_json:
            assert isinstance(response_json['created'], str)
            assert len(response_json['created']) > 0
        if 'modified' in response_json:
            assert isinstance(response_json['modified'], str)
            assert len(response_json['modified']) > 0
            
        # Compare expected values (ignoring children)
        for key, value in test_case["expected_content"].items():
            if key != 'children':  # Skip children for now
                assert response_json[key] == value
    
    if "verify_response" in test_case:
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