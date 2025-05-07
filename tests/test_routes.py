import os
from pathlib import Path
import pytest

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
                "Notes/test1.md" in response.json() and
                "Notes/test2.md" in response.json() and
                "Projects/test3.md" in response.json()
            )
        },{
            "method": "GET",
            "route": "/folders",
            "body": None,
            "expected_status": 200,
            "expected_content": None,
            "verify_response": lambda response: (
                len(response.json()) == 2 and
                "Notes" in response.json() and
                "Projects" in response.json()
            )
        },{
            "method": "GET",
            "route": "/files/Notes/test1.md",
            "body": None,
            "expected_status": 200,
            "expected_content": {"content": "# Test File 1"}
        },{
            "method": "GET",
            "route": "/folders/Notes",
            "body": None,
            "expected_status": 200,
            "expected_content": None,
            "verify_response": lambda response: (
                len(response.json()) == 2 and
                "Notes/test1.md" in response.json() and
                "Notes/test2.md" in response.json()
            )
        },{
            "method": "POST",
            "route": "/files/Notes/new_file.md",
            "body": {"content": "# New File"},
            "expected_status": 200,
            "expected_content": {"message": "File created successfully: Notes/new_file.md"},
            "verify_operation": lambda client, headers: (
                client.get("/files/Notes/new_file.md", headers=headers).json()["content"] == "# New File"
            )
        },{
            "method": "POST",
            "route": "/folders/NewFolder",
            "body": None,
            "expected_status": 200,
            "expected_content": {"message": "Folder created successfully: NewFolder"},
            "verify_operation": lambda client, headers: (
                "NewFolder" in client.get("/folders", headers=headers).json()
            )
        },{
            "method": "PUT",
            "route": "/files/Notes/test1.md",
            "body": {"content": "# Updated Content"},
            "expected_status": 200,
            "expected_content": {"message": "File updated successfully: Notes/test1.md"},
            "verify_operation": lambda client, headers: (
                client.get("/files/Notes/test1.md", headers=headers).json()["content"] == "# Updated Content"
            )
        },{
            "method": "PATCH",
            "route": "/files/Notes/test1.md",
            "body": {"new_path": "Notes/moved.md"},
            "expected_status": 200,
            "expected_content": {"message": "File moved successfully to Notes/moved.md"},
            "verify_operation": lambda client, headers: (
                client.get("/files/Notes/moved.md", headers=headers).json()["content"] == "# Test File 1" and
                client.get("/files/Notes/test1.md", headers=headers).status_code == 404
            )
        },{
            "method": "PATCH",
            "route": "/folders/Projects",
            "body": {"new_path": "Projects_moved"},
            "expected_status": 200,
            "expected_content": {"message": "Folder moved successfully to Projects_moved"},
            "verify_operation": lambda client, headers: (
                "Projects" not in client.get("/folders", headers=headers).json() and
                "Projects_moved" in client.get("/folders", headers=headers).json()
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
    
    if test_case["expected_content"]:
        assert response.json() == test_case["expected_content"]
    
    if "verify_response" in test_case:
        assert test_case["verify_response"](response)
    
    if "verify_operation" in test_case:
        assert test_case["verify_operation"](client, headers)

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
    assert "Notes/test1.md" in files
    assert "Notes/test2.md" in files
    assert "Projects/test3.md" in files
    assert ".hidden/test.md" not in files
    
    response = client.get("/folders")
    assert response.status_code == 200
    folders = response.json()
    assert len(folders) == 2
    assert "Notes" in folders
    assert "Projects" in folders
    assert ".hidden" not in folders

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
    assert response.json()["message"] == f"File created successfully: {path}"
    
    # Test reading file with raw path
    response = client.get(f"/files/{path}")
    assert response.status_code == 200
    assert response.json()["content"] == "# Test Content"
    
    # Test reading file with URL-encoded path
    response = client.get(f"/files/{encoded_path}")
    assert response.status_code == 200
    assert response.json()["content"] == "# Test Content"