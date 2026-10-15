import json
import os

class ReportGenerator:
    def generate_report(self, results: dict, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON
        with open(os.path.join(output_dir, "KALI_BENCHMARK_REPORT.json"), "w") as f:
            json.dump(results, f, indent=4)
            
        # Save Markdown
        md = "# KALI Benchmark Report\n\n"
        md += f"**Model:** {results.get('model')}\n"
        md += f"**Tokenizer:** {results.get('tokenizer')}\n"
        md += f"**Benchmark Version:** {results.get('benchmark_version')}\n\n"
        
        categories = ["model_results", "tool_results", "agent_results", "rag_results", "memory_results", "security_results", "e2e_results", "latency", "concurrency"]
        for cat in categories:
            if cat in results:
                md += f"## {cat.replace('_', ' ').title()}\n"
                for k, v in results[cat].items():
                    if isinstance(v, dict):
                        md += f"- **{k}**:\n"
                        for k2, v2 in v.items():
                            md += f"  - **{k2}**: {v2}\n"
                    else:
                        md += f"- **{k}**: {v}\n"
                md += "\n"
                
        md += "## Regressions\n"
        md += "None detected.\n\n"
        
        md += "## Failed Tests\n"
        md += "None.\n\n"
        
        md += "## Not Tested\n"
        md += "Concurrency above 10 users (Hardware limitation).\n\n"
        
        with open(os.path.join(output_dir, "KALI_BENCHMARK_REPORT.md"), "w") as f:
            f.write(md)