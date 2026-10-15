from sqlalchemy import String, DateTime, func, ForeignKey, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from OpenDEMON.database.base import Base, uuid_gen

class KaliTask(Base):
    __tablename__ = "kali_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    parent_task_id: Mapped[str] = mapped_column(String, ForeignKey("kali_tasks.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("kali_projects.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    
    objective: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Store lists as JSON
    dependencies: Mapped[list] = mapped_column(JSON, default=list)
    artifacts: Mapped[list] = mapped_column(JSON, default=list)
    
    assigned_agent: Mapped[str] = mapped_column(String, nullable=True)
    assigned_tool: Mapped[str] = mapped_column(String, nullable=True)
    
    input_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    errors: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=True)
