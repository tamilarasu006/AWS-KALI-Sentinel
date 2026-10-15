from typing import Any, Dict
from sqlalchemy import String, DateTime, Float, func, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from OpenDEMON.database.base import Base, uuid_gen

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    model_version_id: Mapped[str] = mapped_column(String, ForeignKey("model_versions.id"), index=True)
    benchmark: Mapped[str] = mapped_column(String, index=True)
    metric: Mapped[str] = mapped_column(String, index=True)
    score: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    hardware: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    configuration: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
