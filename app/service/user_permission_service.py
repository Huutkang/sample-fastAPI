from fastapi import HTTPException, status
from app.repository.user_permission_repository import UserPermissionRepository
from app.model.user_permission import UserPermission
from .user_service import UserService
from .permission_service import PermissionService

class UserPermissionService:
    def __init__(self):
        self.repository = UserPermissionRepository()
        self.user_service = UserService()
        self.permission_service = PermissionService()

    async def assign_permissions(self, data: dict) -> list:
        """
        Gán (assign) quyền cho người dùng.
        Dữ liệu đầu vào bao gồm:
          - user_id: int
          - permissions: dict, với key là permission name,
            value là dict chứa:
              'is_active' (mặc định True),
              'is_denied' (mặc định False),
              'target': nếu bằng "all" thì target_id = None, ngược lại target_id = giá trị target.
        """
        user = await self.user_service.get_user_by_id(data.get("user_id"))
        # Nếu user không tồn tại, UserService sẽ raise HTTPException

        assigned_permissions = []
        user_permissions_to_add = []

        for permission_key, permission_data in data.get("permissions", {}).items():
            permission = await self.permission_service.get_permission_by_name(permission_key)
            if not permission:
                continue  # Bỏ qua nếu không tìm thấy quyền

            # Yêu cầu trường 'target' phải có trong dữ liệu
            if "target" not in permission_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target not provided for permission: {permission_key}"
                )

            user_permission = UserPermission()
            user_permission.user = user
            user_permission.permission = permission
            user_permission.is_active = permission_data.get("is_active", True)
            user_permission.is_denied = permission_data.get("is_denied", False)
            user_permission.target_id = None if permission_data["target"] == "all" else permission_data["target"]

            user_permissions_to_add.append(user_permission)
            assigned_permissions.append({
                "permission": permission_key,
                "status": "assigned"
            })

        await self.repository.bulk_insert(user_permissions_to_add)
        return assigned_permissions

    async def set_permission(self, user, permissions: list) -> list:
        """
        Khởi tạo quyền cho người dùng (ví dụ: cho superadmin).
        Tham số permissions là danh sách các đối tượng Permission.
        """
        user_permissions = []
        user_permissions_to_add = []
        for permission in permissions:
            # Kiểm tra đối tượng permission phải có thuộc tính `id`
            if not hasattr(permission, "id"):
                raise ValueError("Each item in permissions array must be an instance of Permission.")

            user_permission = UserPermission()
            user_permission.user = user
            user_permission.permission = permission
            user_permission.is_active = True
            user_permission.is_denied = False
            user_permission.target_id = None

            user_permissions_to_add.append(user_permission)
            user_permissions.append(user_permission)

        await self.repository.bulk_insert(user_permissions_to_add)
        return user_permissions

    async def find_permissions_by_user(self, user) -> list:
        """
        Lấy danh sách các quyền (UserPermission) của người dùng.
        """
        return await self.repository.find_by_user_id(user.id)

    async def get_permissions_by_user(self, user) -> list:
        """
        Lấy danh sách tên quyền của người dùng.
        """
        user_permissions = await self.repository.find_by_user_id(user.id)
        return [up.permission.name for up in user_permissions]

    async def update_permission(self, data: dict) -> list:
        """
        Cập nhật quyền của người dùng.
        Dữ liệu đầu vào bao gồm:
          - user_id: int
          - permissions: dict với key là permission name,
            value là dict chứa:
              'is_active', 'is_denied', 'target'
        """
        user = await self.user_service.get_user_by_id(data.get("user_id"))
        updated_permissions = []

        for permission_key, permission_data in data.get("permissions", {}).items():
            permission = await self.permission_service.get_permission_by_name(permission_key)
            if not permission:
                continue  # Bỏ qua nếu không tìm thấy quyền

            user_permission = await self.repository.find_one_by_user_and_permission(user.id, permission.id)
            if not user_permission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Permission '{permission_key}' is not assigned to the user"
                )

            user_permission.is_active = permission_data.get("is_active", user_permission.is_active)
            user_permission.is_denied = permission_data.get("is_denied", user_permission.is_denied)
            if "target" not in permission_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target not provided for permission: {permission_key}"
                )
            user_permission.target_id = None if permission_data["target"] == "all" else permission_data["target"]

            await self.repository.update(user_permission)
            updated_permissions.append({
                "permission": permission_key,
                "status": "updated"
            })

        return updated_permissions

    async def has_permission(self, user_id: int, permission_name: str, target_id: int = None) -> int:
        """
        Kiểm tra quyền của người dùng.
        Trả về:
          1  : nếu có quyền (active và không bị deny)
         -1  : nếu quyền bị deny
          0  : nếu không tìm thấy quyền nào phù hợp
        """
        user_permissions = await self.repository.find_user_permission(user_id, permission_name)
        for up in user_permissions:
            if not up.is_active:
                continue
            if up.target_id is None:
                return -1 if up.is_denied else 1
            if up.target_id == target_id:
                return -1 if up.is_denied else 1
        return 0

    async def delete_permissions(self, data: dict) -> None:
        """
        Xóa quyền của người dùng.
        Dữ liệu đầu vào bao gồm:
          - user_id: int
          - permissions: list các permission name cần xóa.
        """
        user = await self.user_service.get_user_by_id(data.get("user_id"))
        user_permissions_to_delete = []
        for permission_name in data.get("permissions", []):
            permission = await self.permission_service.get_permission_by_name(permission_name)
            if not permission:
                continue  # Bỏ qua nếu không tìm thấy quyền

            user_permission = await self.repository.find_one_by_user_and_permission(user.id, permission.id)
            if user_permission:
                user_permissions_to_delete.append(user_permission)

        await self.repository.bulk_delete(user_permissions_to_delete)
