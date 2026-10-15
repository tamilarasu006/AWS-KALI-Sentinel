from typing import List
from .registry import CapabilityRegistry
from .capability import Capability
import re

class CapabilityResolver:
    """
    Resolves natural language task descriptions into a list of required Capabilities.
    Currently uses heuristic keyword matching, to be upgraded to semantic search (pgvector).
    """
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        
    def resolve(self, task_description: str) -> List[Capability]:
        desc_lower = task_description.lower()
        resolved = {}
        
        # Keyword mapping heuristics
        mapping = {
            # SOFTWARE
            "PYTHON_DEVELOPMENT": ["python", "django", "flask", "fastapi", "pip"],
            "JAVASCRIPT_DEVELOPMENT": ["javascript", "js", "vanilla", "es6"],
            "TYPESCRIPT_DEVELOPMENT": ["typescript", "ts"],
            "REACT_DEVELOPMENT": ["react", "jsx", "tsx", "next.js"],
            "NODEJS_DEVELOPMENT": ["node.js", "node", "express"],
            "JAVA_DEVELOPMENT": ["java", "spring", "maven", "gradle"],
            "CPP_DEVELOPMENT": ["c/c++", "c++", "cpp", "c", "cmake"],
            "RUST_DEVELOPMENT": ["rust", "cargo", "rs"],
            "SQL_DEVELOPMENT": ["sql", "query", "database development"],
            "API_DEVELOPMENT": ["api development", "rest", "graphql", "endpoints"],
            "FULL_STACK_DEVELOPMENT": ["react", "node", "full-stack", "app", "application", "backend", "frontend"],

            # DATA
            "CSV_ANALYSIS": ["csv"],
            "EXCEL_ANALYSIS": ["excel", "xlsx"],
            "SQL_ANALYSIS": ["sql analysis"],
            "PANDAS_ANALYSIS": ["pandas", "dataframe"],
            "NUMPY_ANALYSIS": ["numpy", "ndarray"],
            "STATISTICS": ["statistics", "mean", "variance", "distribution"],
            "VISUALIZATION": ["visualization", "plot", "graph", "matplotlib", "seaborn"],
            "MACHINE_LEARNING_DATA": ["machine learning"],
            "DATA_ANALYSIS": ["data analysis", "analyze"],

            # WEB
            "WEB_SEARCH": ["search"],
            "BROWSER_INTERACTION": ["browser"],
            "HTTP_REQUESTS": ["http", "requests", "curl"],
            "WEB_APIS": ["apis"],
            "WEBPAGE_ANALYSIS": ["webpage analysis", "scrape", "dom"],

            # DOCUMENTS
            "PDF_PROCESSING": ["pdf"],
            "DOCX_PROCESSING": ["docx", "word document"],
            "XLSX_PROCESSING": ["xlsx processing"],
            "CSV_PROCESSING": ["csv processing"],
            "MARKDOWN_PROCESSING": ["markdown", "md"],

            # DEVOPS
            "GIT_OPERATIONS": ["git", "commit", "push", "pull", "repo"],
            "DOCKER_MANAGEMENT": ["docker", "container", "image", "docker-compose"],
            "BUILD_SYSTEMS": ["build"],
            "TESTING_SYSTEMS": ["testing", "pytest", "jest", "unittest"],
            "CI_CD_PIPELINE": ["deploy", "ci/cd", "pipeline", "github actions", "gitlab ci"],
            "DEPLOYMENT": ["deployment"],

            # GAME
            "GAME_ARCHITECTURE": ["game architecture", "unreal", "unity", "godot"],
            "GAMEPLAY_ENGINEERING": ["gameplay"],
            "PHYSICS_ENGINEERING": ["physics"],
            "GAME_UI": ["ui", "hud"],
            "GAME_PERFORMANCE": ["performance"],

            # CYBERSECURITY
            "AUTHORIZED_RECONNAISSANCE": ["authorized reconnaissance", "recon"],
            "DNS_ANALYSIS": ["dns analysis", "dig", "nslookup"],
            "PORT_SERVICE_DISCOVERY": ["port", "service discovery"],
            "VULNERABILITY_ASSESSMENT": ["vulnerability assessment", "cve"],
            "WEB_SECURITY_TESTING": ["web security testing", "xss", "sqli"],
            "CONFIGURATION_AUDITING": ["configuration auditing"],
            "SECURITY_REPORTING": ["reporting"],
            "CYBERSECURITY_ASSESSMENT": ["assess", "authorized", "security", "lab", "server", "vulnerability", "nmap"],

            # AI_ML
            "DATASET_PREPARATION": ["dataset preparation", "cleaning"],
            "MODEL_TRAINING": ["train", "model", "training"],
            "MODEL_FINETUNING": ["fine-tuning", "lora", "qlora"],
            "MODEL_EVALUATION": ["evaluation", "metrics", "benchmark"],
            "MODEL_INFERENCE": ["inference", "generation", "predict"]
        }
        
        for cap_name, keywords in mapping.items():
            for kw in keywords:
                # Use word boundaries to avoid partial matches
                if re.search(r'\b' + re.escape(kw) + r'\b', desc_lower):
                    capability = self.registry.get(cap_name)
                    if capability:
                        resolved[capability.name] = capability
                    break
                    
        # Always add reasoning & planning as baseline capabilities for any complex task
        if resolved:
            reasoning = self.registry.get("REASONING")
            planning = self.registry.get("PLANNING")
            if reasoning: resolved[reasoning.name] = reasoning
            if planning: resolved[planning.name] = planning
            
        return list(resolved.values())
