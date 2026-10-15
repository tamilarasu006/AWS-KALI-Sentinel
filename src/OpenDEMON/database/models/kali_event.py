from sqlalchemy import String, DateTime, func, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from OpenDEMON.database.base import Base, uuid_gen

class KaliRuntimeEvent(Base):
    __tablename__ = "kali_runtime_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    task_id: Mapped[str] = mapped_column(String, ForeignKey("kali_tasks.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String, index=True)
    summary: Mapped[str] = mapped_column(Text)
    metadata_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
