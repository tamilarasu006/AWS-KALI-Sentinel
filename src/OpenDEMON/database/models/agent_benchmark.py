
from sqlalchemy import String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from OpenDEMON.database.base import Base, uuid_gen

class AgentBenchmarkRun(Base):
    __tablename__ = "agent_benchmark_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    model: Mapped[str] = mapped_column(String)
    
class AgentBenchmarkResult(Base):
    __tablename__ = "agent_benchmark_results"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("agent_benchmark_runs.id"))
    task_id: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    metrics: Mapped[dict] = mapped_column(JSON)
