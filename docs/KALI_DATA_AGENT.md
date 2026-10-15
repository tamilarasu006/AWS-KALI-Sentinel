# KALI Data Analyst Agent (STEP 35)

## Overview
The `DataAgent` is a specialized KALI Agent built to manage data science pipelines. It ingests CSV/JSON structures, identifies columns, handles missing values, and generates statistical visualizations.

## Safety and Security
The agent operates under the strict assumption that **uploaded code/data must never execute automatically in the host environment.**
- Data cleaning, profiling, and visualization logic is dynamically written as a Python script by the Agent.
- The script is shipped to the `KALIExecutor`, which invokes it in the `sandbox_execute` isolated context.
- Artifacts produced by these sandbox environments (e.g. `.png` charts, cleaned datasets) are safely routed back to the host via the `WorkspaceManager`.

## Lifecycle
1. **Upload Dataset**: Handled by the generic KALI frontend, placing the file in the workspace.
2. **Inspect**: Python code is generated to read rows, columns, data types, and check for null fields (`DataProfiler`).
3. **Clean**: Generates a script to `drop_duplicates` and standard-fill nulls (`DataCleaner`).
4. **Visualize**: Identifies numeric columns and dynamically runs `matplotlib`/`seaborn` to output scatter plots or charts.
5. **Report Generation**: Aggregates the standard outputs from the sandbox executions into a cohesive Markdown summary, returning it alongside the generated artifacts.

## Outputs
- **Markdown Report**: Explains what was discovered and cleaned.
- **Artifacts Array**: Contains strings referencing the new files (e.g., `cleaned_sales.csv`, `chart_task_123.png`).
