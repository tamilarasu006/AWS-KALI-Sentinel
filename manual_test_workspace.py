import shutil
from pathlib import Path
from OpenDEMON.kali.workspace.manager import WorkspaceManager
from OpenDEMON.kali.core.artifacts import ArtifactManager

def run():
    print("Testing Workspace & Artifacts...")
    
    base = Path("~/.opendemon/test_workspaces_manual").expanduser()
    if base.exists():
        shutil.rmtree(base)
        
    wm = WorkspaceManager(str(base))
    am = ArtifactManager(wm)
    
    print("\n--- Test 1: Workspace Creation & Traversal Protection ---")
    ws = wm.create_workspace("user1", "proj_alpha")
    print(f"Created Workspace at: {ws.root_path}")
    assert Path(ws.root_path).exists()
    
    # Try an injection
    ws_evil = wm.create_workspace("user1", "../../../windows/system32")
    print(f"Evil input resolved safely to: {ws_evil.root_path}")
    assert ".." not in ws_evil.root_path
    assert "system32" in ws_evil.root_path
    
    print("\n--- Test 2: Artifact Creation & Checksum ---")
    data = b"import sys\nprint('hello')\n"
    art = am.create("user1", "proj_alpha", "task_x", "script.py", data, {"author": "AI"})
    
    print(f"Artifact ID: {art.id}")
    print(f"Type: {art.type}, Size: {art.size}")
    print(f"Checksum: {art.checksum}")
    print(f"Reference: {art.reference}")
    
    assert art.type == "source"
    assert art.size == 26
    assert len(art.checksum) == 64
    
    print("\n--- Test 3: Download & Isolation ---")
    downloaded = am.download(art.id)
    assert downloaded == data
    
    print("\nALL TESTS PASSED MANUALLY!")
    
    if base.exists():
        shutil.rmtree(base)

if __name__ == "__main__":
    run()
