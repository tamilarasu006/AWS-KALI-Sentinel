# KALI Research Agent (STEP 38)

## Overview
The `ResearchAgent` orchestrates deep-dive web investigations, source aggregation, fact-checking, and report synthesis. It connects exclusively via KALI's Secure Internet Gateway, establishing a zero-trust model for web-retrieved content.

## Zero-Trust Architecture
1. **Network Boundaries:** 
   The agent utilizes the `internet_search` and `internet_fetch` tools, deferring all HTTP requests to the core KALI Gateway. The Gateway handles IP blacklisting, DNS filtering, and SSRF (Server-Side Request Forgery) protection natively.
2. **Error Handling & Resilience:**
   If a domain is blocked (`status: blocked`) or unresponsive (`status: timeout`), the agent gracefully logs the omission without abandoning the entire research pipeline.
3. **Prompt Injection Defense:**
   The Web is explicitly treated as adversarial. All successfully fetched HTML/Text payloads are wrapped natively inside strict XML boundary tags (`<UNTRUSTED_WEB_CONTENT>...</UNTRUSTED_WEB_CONTENT>`). Additionally, the agent's internal parser scans the raw payloads for hardcoded malicious overrides (e.g. `IGNORE PREVIOUS INSTRUCTIONS`) and silently rejects poisoned sources before they pollute the synthesis phase.

## Reporting & Citations
- **Source Tracing:** Every fact extracted during the `<UNTRUSTED>` traversal phase retains a 1:1 mapping back to its source URL.
- **Footnote Synthesis:** The final Markdown generation mandates footnote-style tracking. Sentences are synthesized and appended with `[1]`, directly linking to the `References` section at the bottom of the report to guarantee provenance.
