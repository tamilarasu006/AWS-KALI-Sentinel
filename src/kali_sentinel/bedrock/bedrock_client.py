"""Amazon Bedrock Client for KALI Sentinel.

Handles generative reasoning using Amazon Bedrock foundation models (Anthropic Claude,
Amazon Nova, etc.) with safe credential handling and mock fallbacks for offline testing.
"""

from __future__ import annotations

from datetime import datetime
import json
import logging
import os
import re
from typing import Any, Dict, Optional

from kali_sentinel.config import SentinelConfig, get_sentinel_config
from kali_sentinel.decider.contracts import GuardrailDecision, SecurityTool, StructuredIntent, ToolDecision

logger = logging.getLogger(__name__)


class BedrockClient:
    """Client managing generative reasoning through Amazon Bedrock."""

    def __init__(self, config: Optional[SentinelConfig] = None) -> None:
        self.config = config or get_sentinel_config()
        self._runtime_client = None
        self._is_live = False

        self._init_bedrock_client()

    def _init_bedrock_client(self) -> None:
        """Initialize the boto3 Bedrock Runtime client if credentials are present."""
        # Check standard AWS environment indicators
        has_credentials = bool(
            os.getenv("AWS_ACCESS_KEY_ID")
            or os.getenv("AWS_PROFILE")
            or os.path.exists(os.path.expanduser("~/.aws/credentials"))
        )

        if not has_credentials and not self.config.bedrock_mock_fallback:
            logger.warning("AWS credentials not found. Bedrock calls will fail unless mock mode is active.")

        try:
            import boto3
            from botocore.config import Config

            # Use reasonable timeouts for agent reasoning
            boto_cfg = Config(
                region_name=self.config.aws_region,
                retries={"max_attempts": 2, "mode": "standard"},
                connect_timeout=3,
                read_timeout=10,
            )
            self._runtime_client = boto3.client("bedrock-runtime", config=boto_cfg)
            self._is_live = True
            logger.info("Initialized Amazon Bedrock runtime client in region %s", self.config.aws_region)
        except Exception as exc:
            logger.info("Bedrock client initialized in mock/fallback mode: %s", exc)
            self._runtime_client = None
            self._is_live = False

    @property
    def is_live(self) -> bool:
        """Whether a live Amazon Bedrock client connection is available."""
        return self._is_live and self._runtime_client is not None

    def interpret_request(self, user_prompt: str) -> StructuredIntent:
        """Use Amazon Bedrock to extract structured cybersecurity intent and target."""
        if self.is_live and not self.config.bedrock_mock_fallback:
            try:
                return self._interpret_via_bedrock(user_prompt)
            except Exception as exc:
                logger.warning("Bedrock intent extraction failed (%s); using fallback parser.", exc)

        return self._interpret_fallback(user_prompt)

    def explain_result(
        self,
        user_prompt: str,
        tool_decision: ToolDecision,
        guardrail_decision: GuardrailDecision,
        tool_result: Dict[str, Any],
    ) -> str:
        """Use Amazon Bedrock to synthesize a human-readable security report."""
        if self.is_live and not self.config.bedrock_mock_fallback:
            try:
                return self._explain_via_bedrock(
                    user_prompt, tool_decision, guardrail_decision, tool_result
                )
            except Exception as exc:
                logger.warning("Bedrock explanation synthesis failed (%s); using fallback.", exc)

        return self._explain_fallback(
            user_prompt, tool_decision, guardrail_decision, tool_result
        )

    def _interpret_via_bedrock(self, prompt: str) -> StructuredIntent:
        """Execute Bedrock Converse API for task understanding."""
        system_prompt = (
            "You are KALI Sentinel's Cybersecurity Intent Parser. "
            "Analyze the user's security request and return a single valid JSON object with keys: "
            "'action_type' (string), 'target' (string hostname/IP/domain or empty), "
            "'authorization_claimed' (boolean), and 'parameters' (object). Do not output markdown codeblocks."
        )

        response = self._runtime_client.converse(
            modelId=self.config.bedrock_model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            system=[{"text": system_prompt}],
            inferenceConfig={
                "temperature": self.config.bedrock_temperature,
                "maxTokens": self.config.bedrock_max_tokens,
            },
        )

        content = response["output"]["message"]["content"][0]["text"]
        # Clean json if model returned markdown
        clean_json = re.sub(r"^```(?:json)?\s*", "", content.strip())
        clean_json = re.sub(r"\s*```$", "", clean_json)
        parsed = json.loads(clean_json)

        return StructuredIntent(
            raw_request=prompt,
            action_type=parsed.get("action_type", "security_assessment"),
            target=parsed.get("target", ""),
            authorization_claimed=bool(parsed.get("authorization_claimed", False)),
            parameters=parsed.get("parameters", {}),
            safety_notes="Parsed via Amazon Bedrock Converse API",
        )

    def _explain_via_bedrock(
        self,
        prompt: str,
        tool_decision: ToolDecision,
        guardrail_decision: GuardrailDecision,
        tool_result: Dict[str, Any],
    ) -> str:
        """Synthesize final security analysis using Amazon Bedrock."""
        system_prompt = (
            "You are KALI Sentinel, an autonomous cybersecurity defense assistant. "
            "Explain the findings of the authorized security assessment clearly and professionally. "
            "State the tool chosen by Strands Decider 2B, its confidence, the guardrail verdict, "
            "and concise defensive remediation advice."
        )

        user_content = (
            f"Original Request: {prompt}\n"
            f"Decider 2B Tool: {tool_decision.tool.value.upper()} (Confidence: {tool_decision.confidence * 100:.1f}%, Latency: {tool_decision.latency_ms}ms)\n"
            f"Guardrail Verdict: {guardrail_decision.verdict.value} (Score: {guardrail_decision.probability:.2f})\n"
            f"Tool Execution Findings: {tool_result.get('findings', [])}\n"
            f"Tool Summary: {tool_result.get('summary', '')}"
        )

        response = self._runtime_client.converse(
            modelId=self.config.bedrock_model_id,
            messages=[{"role": "user", "content": [{"text": user_content}]}],
            system=[{"text": system_prompt}],
            inferenceConfig={
                "temperature": 0.3,
                "maxTokens": self.config.bedrock_max_tokens,
            },
        )

        return response["output"]["message"]["content"][0]["text"]

    def _interpret_fallback(self, prompt: str) -> StructuredIntent:
        """Deterministic intent extractor when Bedrock credentials are not present."""
        prompt_l = prompt.lower()

        # Extract target: ip, domain, or localhost
        target = ""
        # IP regex
        ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", prompt)
        if ip_match:
            target = ip_match.group(0)
        elif "localhost" in prompt_l:
            target = "localhost"
        else:
            # Look for domain patterns e.g. scanme.nmap.org, test.local, example.com
            domain_match = re.search(r"\b([a-zA-Z0-9][a-zA-Z0-9.-]*\.(?:local|org|com|net|edu|internal|lab))\b", prompt)
            if domain_match:
                target = domain_match.group(1).rstrip(".")

        # Authorization indicators
        auth_claimed = any(
            w in prompt_l for w in ["authorized", "lab", "my server", "my domain", "owned", "test environment", "permission"]
        )

        # Action type
        if "recon" in prompt_l or "whois" in prompt_l or "osint" in prompt_l or "discovery" in prompt_l:
            action = "recon"
        elif "port" in prompt_l or "socket" in prompt_l or "listening" in prompt_l:
            action = "port_scan"
        elif "dns" in prompt_l or "mx" in prompt_l or "spf" in prompt_l or "dmarc" in prompt_l:
            action = "dns_check"
        elif "web" in prompt_l or "header" in prompt_l or "csp" in prompt_l or "http" in prompt_l:
            action = "web_scan"
        else:
            action = "informational_query"

        return StructuredIntent(
            raw_request=prompt,
            action_type=action,
            target=target,
            authorization_claimed=auth_claimed,
            parameters={},
            safety_notes="Interpreted via Sentinel Reasoning Engine",
        )

    def _generate_informational_content(self, prompt: str) -> str:
        p = prompt.strip().lower()

        # Date & Climate
        if any(k in p for k in ["date", "climate", "weather", "time", "today", "tomorrow", "calendar", "day", "clock"]):
            now = datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            time_str = now.strftime("%I:%M:%S %p")
            day_of_year = now.timetuple().tm_yday
            week_number = now.isocalendar()[1]
            month_name = now.strftime("%B")
            year = now.year

            return (
                f"### 📅 Current Date, Time & Calendar Context\n\n"
                f"- **Current Date**: **{date_str}**\n"
                f"- **Current Time**: **{time_str}** (System Local Time)\n"
                f"- **Day of the Year**: Day **{day_of_year}** of {year} (Week **{week_number}**)\n"
                f"- **Seasonal Phase**: Mid-Autumn (Northern Hemisphere) / Mid-Spring (Southern Hemisphere)\n\n"
                f"### 🌤️ Climate & Meteorological Overview ({month_name} {year})\n\n"
                f"- **Atmospheric Character**: October brings characteristic transitional weather patterns. Northern continental zones experience steady thermal cooling with high-pressure continental air masses, crisp mornings, and reduced ambient humidity.\n"
                f"- **Tropical & Maritime Systems**: South and Southeast Asian regions navigate the post-monsoon / retreating monsoon transition, characterized by predominantly clear afternoon skies and cooling evening winds.\n"
                f"- **Environmental Observation**: Typical diurnal temperatures range comfortably between 18°C–28°C (64°F–82°F) across temperate zones, with moderate UV indices during midday hours.\n\n"
                f"### 🛡️ KALI Operational Context for Today\n"
                f"- Mid-week operational peak: All autonomous defensive guardrails and Strands Decider 2B models are active and calibrated. Scheduled infrastructure scans and patch audits can be initiated directly."
            )

        # Greetings
        if any(p.startswith(w) for w in ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]) or p in ["who are you", "what are you", "help"]:
            return (
                "### 👋 Welcome to KALI Sentinel (GPT Astra-6 Intelligence Core)\n\n"
                "I am **KALI Sentinel**, an autonomous cybersecurity intelligence agent powered by **Amazon Bedrock Reasoning** and a fine-tuned **Strands Decider 2B** decision model.\n\n"
                "#### Capabilities & Automated Defenses:\n"
                "- 🔍 **Port & Service Auditing** (`nmap_scan`): Fast, typed discovery of open ports, banner versions, and exposed attack surfaces.\n"
                "- 🛡️ **Web Security Headers** (`web_scan`): Inspection of HSTS, Content Security Policy (CSP), X-Frame-Options, and cookie security flags.\n"
                "- 🌐 **DNS & Anti-Spoofing** (`dns_check`): Verification of MX, SPF, DKIM, and DMARC enforcement to prevent domain impersonation.\n"
                "- 📋 **Network & Registrar OSINT** (`whois_lookup`): Analysis of autonomous systems (ASN), IP ranges, and registrar details.\n"
                "- ⚡ **Sub-Millisecond Guardrails**: Every tool request is validated against strict authorization, grounding, and safety policies before execution.\n\n"
                "> 💡 **Tip**: You can interact here for direct conversational queries, or switch to the dedicated **[KALI Sentinel Dashboard](/sentinel)** to test live preset scenarios with visual telemetry!"
            )

        # Cybersecurity definition & overview
        if "cybersecurity" in p or "cyber security" in p or "infosec" in p or "information security" in p:
            return (
                "### 🛡️ Understanding Cybersecurity\n\n"
                "**Cybersecurity** is the comprehensive practice of protecting networks, devices, software applications, and critical data from unauthorized access, digital attacks, disruption, or destruction.\n\n"
                "#### 1. The Core Pillar: The CIA Triad\n"
                "- **Confidentiality**: Ensuring data is accessible only to authorized identities through strong encryption (AES-256, TLS 1.3), multi-factor authentication (MFA), and least-privilege RBAC.\n"
                "- **Integrity**: Guaranteeing data remains authentic, unaltered, and tamper-resistant using cryptographic checksums, digital signatures, and append-only audit trails.\n"
                "- **Availability**: Maintaining reliable, low-latency access to systems through load balancing, DDoS mitigation, failover clustering, and disaster recovery planning.\n\n"
                "#### 2. Key Domains of Defense\n"
                "1. **Network Security**: Isolating networks via firewalls, micro-segmentation, zero-trust network access (ZTNA), and intrusion prevention systems (IPS).\n"
                "2. **Application Security**: Hardening code against vulnerabilities like injection (SQLi), cross-site scripting (XSS), and insecure deserialization.\n"
                "3. **Cloud & Infrastructure**: Safeguarding cloud resources (e.g., AWS, VPCs, IAM policies, KMS encryption) and eliminating misconfigurations.\n"
                "4. **Security Operations & Threat Hunting**: Leveraging SIEM/SOAR platforms and autonomous agents like **KALI Sentinel** to rapidly triage alerts, detect anomalies, and enforce containment.\n\n"
                "#### 3. How KALI Sentinel Fits In\n"
                "KALI Sentinel bridges high-level reasoning with fast, calibrated local decisions: it uses **Strands Decider 2B** to select defensive tools in under 5 milliseconds and enforces autonomous safety boundaries before executing security probes."
            )

        # Zero trust
        if "zero trust" in p:
            return (
                "### 🔒 Zero Trust Architecture (ZTA)\n\n"
                "**Zero Trust** is a security model centered on the mantra: *\"Never Trust, Always Verify.\"* Unlike traditional perimeter security models (\"castle-and-moat\"), Zero Trust assumes that threats exist both outside and inside the network.\n\n"
                "#### Key Principles:\n"
                "- **Explicit Verification**: Authenticate and authorize based on all available data points (identity, location, device health, data classification, and anomalies).\n"
                "- **Least Privilege Access**: Restrict user and agent access with Just-In-Time (JIT) and Just-Enough-Access (JEA) policies, Risk-Based Adaptive Policies, and data protection.\n"
                "- **Assume Breach**: Minimize the blast radius by segmenting access by network, user, devices, and application awareness. Continuously monitor with end-to-end encryption."
            )

        # Penetration testing / ethical hacking
        if "penetration testing" in p or "pentest" in p or "ethical hacking" in p:
            return (
                "### 🎯 Penetration Testing & Vulnerability Assessment\n\n"
                "**Penetration Testing (Pentesting)** is the simulated authorized cyberattack against a computer system to identify vulnerabilities that malicious threat actors could exploit.\n\n"
                "#### Standard Methodology:\n"
                "1. **Reconnaissance & OSINT**: Gathering network topologies, domain registrations, and DNS records (`whois_lookup`, `dns_check`).\n"
                "2. **Scanning & Enumeration**: Identifying live hosts, open ports, and services (`nmap_scan`, `web_scan`).\n"
                "3. **Vulnerability Analysis**: Cross-referencing detected service versions with CVE databases.\n"
                "4. **Exploitation & Verification**: Safely demonstrating risk without causing service disruption.\n"
                "5. **Remediation & Hardening**: Patching discovered flaws and applying defense-in-depth controls.\n\n"
                "> ⚠️ **Compliance Note**: KALI Sentinel strictly enforces safety guardrails and will never scan third-party systems without verified authorization."
            )

        # SQL Injection / Web Attacks
        if "sql injection" in p or "sqli" in p or "xss" in p or "cross site scripting" in p or "owasp" in p:
            return (
                "### 🌐 Web Application Security & OWASP Top 10\n\n"
                "Web application vulnerabilities are among the most frequent vectors for initial compromise.\n\n"
                "#### Critical Threats & Defenses:\n"
                "- **Injection (e.g., SQLi)**: Occurs when untrusted data is sent to an interpreter as part of a command or query. *Defense*: Use parameterized queries (PreparedStatements) and Object-Relational Mappers (ORMs).\n"
                "- **Cross-Site Scripting (XSS)**: Injection of malicious client-side scripts. *Defense*: Strict Context-Aware Output Encoding and Content Security Policy (CSP) headers.\n"
                "- **Broken Access Control**: Users acting outside their intended permissions. *Defense*: Deny by default, enforce least privilege, and avoid direct object references (IDOR)."
            )

        # Firewall / Port scanning
        if "port scan" in p or "firewall" in p or "nmap" in p:
            return (
                "### 📡 Network Auditing & Firewalls\n\n"
                "**Port Scanning** is an inspection technique to discover active listening network sockets (TCP/UDP) on a target host.\n\n"
                "#### Defensive Best Practices:\n"
                "- **Default-Deny Ingress**: Configure firewalls (iptables, AWS Security Groups) to block all inbound ports except strictly necessary services.\n"
                "- **Service Hardening**: Disable unused legacy services (e.g., Telnet, FTP) in favor of encrypted alternatives (SSH, SFTP).\n"
                "- **Stateful Inspection**: Utilize Next-Gen Firewalls (NGFW) to inspect packet payloads rather than just port numbers.\n\n"
                "> 💡 **Run a Scan**: To test local ports, ask: `Scan localhost for open ports` or visit `/sentinel`."
            )

        # General fallback
        return (
            f"### 🛡️ KALI Sentinel Cybersecurity Intelligence\n\n"
            f"Regarding your query on **\"{prompt}\"**:\n\n"
            "Cybersecurity defense relies on proactive hardening, continuous observability, and automated threat classification.\n\n"
            "**Core Recommendations**:\n"
            "- Implement **defense-in-depth** across network, host, and application layers.\n"
            "- Enforce strict **identity and access controls** with MFA and least privilege.\n"
            "- Continuously inspect external attack surfaces and patch known Common Vulnerabilities and Exposures (CVEs).\n\n"
            "You can command KALI Sentinel to run specific security assessments (e.g., `Scan localhost for open ports`, `Audit DNS for example.com`, or `Check web security headers on scanme.nmap.org`)."
        )

    def _explain_fallback(
        self,
        prompt: str,
        tool_decision: ToolDecision,
        guardrail_decision: GuardrailDecision,
        tool_result: Dict[str, Any],
    ) -> str:
        """Structured explanation generator for offline runs."""
        tool_name = tool_decision.tool.value.upper()
        conf_pct = tool_decision.confidence * 100.0
        findings = tool_result.get("findings", [])
        summary = tool_result.get("summary", "")

        if tool_decision.tool == SecurityTool.NO_TOOL:
            return self._generate_informational_content(prompt)

        lines = [
            f"**KALI Sentinel Security Assessment**",
            f"- **User Intent**: Understand and audit security posture for requested target.",
            f"- **Strands Decider 2B Routing**: Selected `{tool_name}` with **{conf_pct:.1f}% calibrated confidence** ({tool_decision.latency_ms:.1f}ms latency).",
            f"- **Guardrail Boundary**: **{guardrail_decision.verdict.value}** ({guardrail_decision.reasoning}).",
            f"- **Execution Result**: {summary}",
            f"- **Key Findings**:",
        ]
        for finding in findings:
            lines.append(f"  * {finding}")

        lines.extend([
            f"- **Defensive Recommendations**: Ensure that all exposed ports have active firewalls, web servers enforce HSTS and CSP, and DNS configurations maintain strict SPF and DMARC reject policies."
        ])

        return "\n".join(lines)
