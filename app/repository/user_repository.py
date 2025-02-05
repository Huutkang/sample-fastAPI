from sqlalchemy.future import select
from app.model.user import User
from app.configuration.database import AsyncSessionLocal



class UserRepository:

    async def create_user(self, new_user: User):
        """ Tạo mới người dùng """
        async with AsyncSessionLocal() as session:
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user

    async def update_user(self, user: User):
        """ Cập nhật thông tin người dùng """
        async with AsyncSessionLocal() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def delete_user(self, user: User):
        """ Xóa người dùng """
        async with AsyncSessionLocal() as session:
            await session.delete(user)
            await session.commit()

    async def get_active_users_paginated(self, page: int, limit: int):
        """ Lấy danh sách user đang hoạt động (is_active=True) với phân trang """
        offset = (page - 1) * limit
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User)
                .where(User.is_active == True)
                .order_by(User.id.asc())
                .offset(offset)
                .limit(limit)
            )
            return result.scalars().all()

    async def get_user_by_id(self, user_id: int):
        """ Tìm user theo ID """
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str):
        """ Tìm user theo username """
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.username == username))
            return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str):
        """ Tìm user theo email """
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
