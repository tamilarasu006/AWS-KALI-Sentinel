# Unified KALI Chat Frontend (STEP 33)

## Overview
The KALI Unified Chat Frontend provides a single interface for all conversational, coding, research, and analysis interactions. It strips away verbose, raw JSON chain-of-thought in favor of clean, structured timeline and status indicators.

## API Configuration Fixes
Previously, desktop integrations directly fell back to `http://localhost:8000`. This broke production or hosted environments. The API configuration hooks (`useTauriApi.ts` and `api.ts`) have been patched to correctly respect `window.location.origin` inside standard browser frames while defaulting appropriately when wrapped in Tauri native OS bindings.

## Chat Components
The main interface (`ChatArea.tsx` and `MessageBubble.tsx`) has been enhanced to gracefully handle KALI internal task logic.

### 1. Tool Execution Status
Rather than printing raw JSON blobs for KALI's internal tool orchestration, the UI uses the `ToolCallCard.tsx` to render:
- `running`: Pulsing loader with the tool name.
- `success`: Green check with execution latency and truncated result previews.
- `error`: Red failure state for sandbox exceptions or capability denials.

### 2. Approval UI
If a high-risk tool triggers the Permission Manager and halts execution, the event stream pushes a `requires_approval` status block. The `ToolCallCard` parses this block and renders **Approve** and **Reject** action buttons inline within the chat. Pressing these buttons dispatches a POST to the `/v1/approvals/{id}/approve` endpoint, allowing the agent to seamlessly resume.

### 3. File Uploads (Documents/RAG)
Users can now connect data sources directly from the Chat context. Documents are routed to the `POST /api/kali/v1/documents` endpoint and instantly made available for semantic retrieval.

## Responsive Design
The Layout utilizes flexible CSS containers and Tailwind breakpoints to ensure that the `SystemPanel` drops down into a drawer or hidden panel on mobile viewports, prioritizing the core Chat Area.
