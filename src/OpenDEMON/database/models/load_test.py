
from sqlalchemy import String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from OpenDEMON.database.base import Base, uuid_gen

class LoadTestRun(Base):
    __tablename__ = "load_test_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    concurrency: Mapped[int] = mapped_column(Integer)
    metrics: Mapped[dict] = mapped_column(JSON)
