from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schema.group_member_schema import GroupMemberCreate
from app.service.group_member_service import GroupMemberService
from app.configuration.database import get_db

group_member_service = GroupMemberService()
router = APIRouter(prefix="/group-members", tags=["Group Members"])

@router.post("/", status_code=201)
async def add_member(group_member: GroupMemberCreate, db: AsyncSession = Depends(get_db)):
    return await group_member_service.add_user_to_group(db, group_member)
