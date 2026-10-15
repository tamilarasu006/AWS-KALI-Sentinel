# KALI Workspace and Artifact System (STEP 28)

## Overview
The KALI Workspace and Artifact system provides secure, isolated storage for files generated or consumed by the AI agents. It ensures that data from one project cannot leak into another, and prevents the model from attempting to read or write arbitrary locations on the host filesystem.

## Workspaces
A **Workspace** is a physical directory bound strictly to a `user_id` and `project_id`.
The `WorkspaceManager` intercepts all requests for directory paths and aggressively sanitizes input to prevent Path Traversal attacks (e.g. `../../../etc/passwd` is sanitized to `etcpasswd`). Furthermore, it explicitly resolves the path and verifies it remains rooted within the designated `~/.opendemon/workspaces` sandbox.

## Artifacts
An **Artifact** is a managed file resulting from a model action (e.g., source code, datasets, generated images).
The `ArtifactManager` handles the lifecycle of these files:
- **Storage**: Files are written into `<workspace_root>/<task_id>/<filename>`.
- **Typing**: Files are automatically typed based on extension (`source`, `image`, `dataset`, `document`, `log`, `report`).
- **Integrity**: Every artifact receives an automatic SHA-256 `checksum` and a byte `size` count upon creation to ensure verifiability.
- **Reference**: Artifacts are referenced by an absolute UUID, masking the physical disk path from the model or end user. The `reference` path stored internally is strictly relative to the workspace root.

## Sandbox Integration
When the `SandboxManager` completes a code execution, it yields transient `artifacts`. The system bridges these by having the Executor call `ArtifactManager.create(...)` for each transient file, promoting it into a persistent Workspace Artifact.
