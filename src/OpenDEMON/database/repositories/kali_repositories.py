"""Repositories for KALI AI models."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from OpenDEMON.database.models import ModelRun, ModelVersion, Embedding

class ModelRunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, run: ModelRun) -> ModelRun:
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def get_by_id(self, run_id: str) -> Optional[ModelRun]:
        result = await self.session.execute(select(ModelRun).filter_by(id=run_id))
        return result.scalar_one_or_none()

class ModelVersionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, version: ModelVersion) -> ModelVersion:
        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        return version

    async def get_active_version(self, model_name: str) -> Optional[ModelVersion]:
        result = await self.session.execute(
            select(ModelVersion).filter_by(model_name=model_name, is_active=True)
        )
        return result.scalar_one_or_none()

class EmbeddingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, embedding: Embedding) -> Embedding:
        self.session.add(embedding)
        await self.session.commit()
        await self.session.refresh(embedding)
        return embedding

    async def get_by_reference_id(self, reference_id: str) -> List[Embedding]:
        result = await self.session.execute(
            select(Embedding).filter_by(reference_id=reference_id)
        )
        return list(result.scalars().all())
