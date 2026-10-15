import json
from typing import Dict, Any, List, Optional
from OpenDEMON.kali.agents.base_agent import AgentBase
from OpenDEMON.kali.agents.models import AgentContext, AgentResult, AgentCapabilities
from OpenDEMON.kali.permissions.risk import RiskLevel

class DataAgent(AgentBase):
    """Specialized agent for data science, analytics, and SQL tasks."""
    
    def __init__(self):
        self._name = "DataAgent"
        self._description = "Agent for handling data analytics, pandas processing, SQL, and machine learning."
        self._capabilities = AgentCapabilities(
            primary_domain="data_analysis",
            supported_tasks=[
                "data_profiling", 
                "data_cleaning", 
                "statistical_analysis", 
                "visualization",
                "basic_ml",
                "report_generation"
            ],
            restricted=False
        )
        self.keywords = ["data", "pandas", "sql", "ml", "ai", "visualization", "plot", "graph", "dataset", "analyze", "query", "csv", "excel"]

    @property
    def name(self) -> str:
        return self._name
        
    @property
    def description(self) -> str:
        return self._description
        
    @property
    def capabilities(self) -> AgentCapabilities:
        return self._capabilities
        
    @property
    def allowed_tools(self) -> List[str]:
        # Allows access to sandbox code execution and file generation
        return ["sandbox_execute", "workspace_write", "workspace_read"]
        
    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.MEDIUM
        
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "dataset_path": {"type": "string"},
                "analysis_goal": {"type": "string"}
            },
            "required": ["dataset_path", "analysis_goal"]
        }
        
    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "report": {"type": "string"},
                "artifacts": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }

    def _generate_profiling_code(self, dataset_path: str) -> str:
        return f"""import pandas as pd
try:
    df = pd.read_csv('{dataset_path}')
except Exception:
    try:
        df = pd.read_json('{dataset_path}')
    except Exception:
        print("Failed to load dataset")
        exit(1)
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Missing:\\n", df.isnull().sum().to_dict())
"""

    def _generate_cleaning_code(self, dataset_path: str, output_path: str) -> str:
        return f"""import pandas as pd
df = pd.read_csv('{dataset_path}')
df = df.drop_duplicates()
df = df.fillna(method='ffill').fillna(method='bfill')
df.to_csv('{output_path}', index=False)
print("Cleaned data saved to {output_path}")
"""

    def _generate_visualization_code(self, dataset_path: str, output_chart: str) -> str:
        return f"""import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
df = pd.read_csv('{dataset_path}')
plt.figure(figsize=(10,6))
numeric_cols = df.select_dtypes(include='number').columns
if len(numeric_cols) >= 2:
    sns.scatterplot(data=df, x=numeric_cols[0], y=numeric_cols[1])
    plt.title('Basic Analysis')
    plt.savefig('{output_chart}')
    print("Chart saved to {output_chart}")
else:
    print("Not enough numeric columns for scatter plot.")
"""

    async def execute(self, prompt: str, context: AgentContext, executor: Any = None) -> AgentResult:
        if not context.user_id or not context.project_id or not context.task_id:
            return AgentResult(
                agent_id=self.name,
                success=False,
                output="",
                error="Missing required context: user_id, project_id, and task_id must be provided."
            )

        # Parse inputs
        dataset_path = None
        if "dataset_path=" in prompt:
            dataset_path = prompt.split("dataset_path=")[1].split()[0].strip()
        else:
            return AgentResult(
                agent_id=self.name,
                success=False,
                output="",
                error="Missing dataset_path in prompt."
            )

        # Mocking the pipeline stages
        artifacts = []
        report_sections = []
        
        # 1. Inspect / Profile
        report_sections.append("## 1. Inspection & Profiling")
        if executor:
            # Note: The agent generates code for the sandbox, never executes uploaded user code directly
            code = self._generate_profiling_code(dataset_path)
            profile_res = await executor.execute("sandbox_run_python", {"code": code})
            report_sections.append(f"```text\\n{profile_res.get('output', 'Mock Profile Output: 100 rows, 5 cols')}\\n```")
        else:
            report_sections.append("Simulated Profiling: Dataset loaded successfully.")

        # 2. Clean
        cleaned_path = f"cleaned_{dataset_path.split('/')[-1]}"
        artifacts.append(cleaned_path)
        report_sections.append("## 2. Data Cleaning")
        if executor:
            code = self._generate_cleaning_code(dataset_path, cleaned_path)
            await executor.execute("sandbox_run_python", {"code": code})
            report_sections.append(f"Handled missing values and duplicates. Saved to {cleaned_path}.")
        else:
            report_sections.append(f"Simulated Cleaning: Removed duplicates and filled missing values. Saved to {cleaned_path}.")

        # 3. Analyze & Visualize
        chart_path = f"chart_{context.task_id}.png"
        artifacts.append(chart_path)
        report_sections.append("## 3. Analysis & Visualization")
        if executor:
            code = self._generate_visualization_code(cleaned_path, chart_path)
            await executor.execute("sandbox_run_python", {"code": code})
            report_sections.append(f"Generated visualization artifact: {chart_path}.")
        else:
            report_sections.append(f"Simulated Visualization: Generated scatter plot at {chart_path}.")

        # 4. Explain / Generate Report
        report_sections.insert(0, "# Data Analysis Report")
        final_report = "\\n\\n".join(report_sections)

        return AgentResult(
            agent_id=self.name,
            success=True,
            output=final_report,
            data={
                "artifacts": artifacts,
                "original_dataset": dataset_path,
                "cleaned_dataset": cleaned_path
            }
        )
