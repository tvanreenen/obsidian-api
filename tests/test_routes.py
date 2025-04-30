import os
from pathlib import Path

def test_list_files(client):
    response = client.get("/files")
    assert response.status_code == 200
    files = response.json()
    assert len(files) == 3
    assert "Notes/test1.md" in files
    assert "Notes/test2.md" in files
    assert "Projects/test3.md" in files
    
def test_list_folders(client):
    response = client.get("/folders")
    assert response.status_code == 200
    folders = response.json()
    assert len(folders) == 2
    assert "Notes" in folders
    assert "Projects" in folders

def test_list_folder_files(client):
    response = client.get("/folders/Notes")
    assert response.status_code == 200
    files = response.json()
    assert len(files) == 2
    assert "Notes/test1.md" in files
    assert "Notes/test2.md" in files

def test_read_file(client):
    response = client.get("/files/Notes/test1.md")
    assert response.status_code == 200
    content = response.json()
    assert content["content"] == "# Test File 1"

def test_create_file(client):
    response = client.post(
        "/files/Notes/new_file.md",
        json={"content": "# New File"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "File created successfully: Notes/new_file.md"
    
    # Verify file was created
    response = client.get("/files/Notes/new_file.md")
    assert response.status_code == 200
    assert response.json()["content"] == "# New File"

def test_update_file(client):
    response = client.put(
        "/files/Notes/test1.md",
        json={"content": "# Updated Content"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "File updated successfully: Notes/test1.md"
    
    # Verify content was updated
    response = client.get("/files/Notes/test1.md")
    assert response.status_code == 200
    assert response.json()["content"] == "# Updated Content"

def test_create_folder(client):
    response = client.post("/folders/NewFolder")
    assert response.status_code == 200
    assert response.json()["message"] == "Folder created successfully: NewFolder"
    
    # Verify folder was created
    response = client.get("/folders")
    assert "NewFolder" in response.json()

def test_move_file(client):
    # Move an existing test file
    response = client.patch(
        "/files/Notes/test1.md",
        json={"new_path": "Notes/moved.md"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "File moved successfully to Notes/moved.md"
    
    # Verify the file was moved
    response = client.get("/files/Notes/moved.md")
    assert response.status_code == 200
    assert response.json()["content"] == "# Test File 1"
    
    # Verify the old file is gone
    response = client.get("/files/Notes/test1.md")
    assert response.status_code == 404

def test_move_folder(client):
    # Move the Projects folder
    response = client.patch(
        "/folders/Projects",
        json={"new_path": "Projects_moved"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Folder moved successfully to Projects_moved"
    
    # Verify old folder is gone
    response = client.get("/folders")
    assert "Projects" not in response.json()
    
    # Verify new folder exists
    response = client.get("/folders")
    assert "Projects_moved" in response.json()

def test_error_cases(client):
    # Try to read non-existent file
    response = client.get("/nonexistent.md")
    assert response.status_code == 404
    
    # Try to create file that already exists
    response = client.post(
        "/files/Notes/test1.md",
        content="# Duplicate",
        headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 400  # File already exists
    
    # Try to move to existing path
    response = client.patch(
        "/files/Notes/test2.md",
        json={"new_path": "Notes/test1.md"}  # Try to move test1.md to test2.md
    )
    assert response.status_code == 400  # Path already exists 

def test_hidden_directories(client):
    # Create a dot-prefixed directory in the test vault. Still might create through API or as fixture.
    dot_dir = Path(os.getenv("OBSIDIAN_API_VAULT_PATH")) / ".hidden"
    dot_dir.mkdir()
    (dot_dir / "test.md").write_text("# Hidden File")
    
    # Test /files endpoint - should not include files from dot-prefixed directory
    response = client.get("/files")
    assert response.status_code == 200
    files = response.json()
    assert len(files) == 3  # Original test files should still be visible
    assert "Notes/test1.md" in files
    assert "Notes/test2.md" in files
    assert "Projects/test3.md" in files
    assert ".hidden/test.md" not in files
    
    # Test /folders endpoint - should not include dot-prefixed directory
    response = client.get("/folders")
    assert response.status_code == 200
    folders = response.json()
    assert len(folders) == 2
    assert "Notes" in folders
    assert "Projects" in folders
    assert ".hidden" not in folders

    # Test reading file from dot-prefixed directory, should not be able to read files in dot-prefixed directories 
    response = client.get("/files/.hidden/test.md")
    assert response.status_code == 404

    # Test listing contents of dot-prefixed directory, should not be able to list contents of dot-prefixed directories 
    response = client.get("/folders/.hidden")
    assert response.status_code == 404