from typing import Annotated

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_db


async def db_dependency() -> AsyncIOMotorDatabase:
    return await get_db()


DbDep = Annotated[AsyncIOMotorDatabase, Depends(db_dependency)]
