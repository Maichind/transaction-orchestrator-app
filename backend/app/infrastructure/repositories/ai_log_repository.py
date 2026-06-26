"""AILog repository — write-mostly audit log."""
from __future__ import annotations
from sqlalchemy import func, select
from app.infrastructure.database.models.ai_log import AILog
from app.infrastructure.repositories.base import BaseRepository


class AILogRepository(BaseRepository[AILog]):
    model = AILog


    async def get_total_tokens_today(self) -> int:
        """Aggregate tokens used today — supports cost monitoring dashboards."""
        from datetime import date
        from sqlalchemy import cast, Date
 
        result = await self.session.execute(
            select(func.coalesce(func.sum(AILog.tokens_used), 0)).where(
                cast(AILog.created_at, Date) == date.today()
            )
        )
        return int(result.scalar_one())
