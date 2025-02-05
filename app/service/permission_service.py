from app.repository.permission_repository import PermissionRepository
from app.model.permission import Permission
from app.configuration.database import AsyncSessionLocal
from app.exceptions import AppException  # Giả sử bạn có định nghĩa ngoại lệ riêng

class PermissionService:
    def __init__(self, entity_manager, permission_repository: PermissionRepository):
        self.entity_manager = entity_manager  # entity_manager có thể là AsyncSessionLocal
        self.permission_repository = permission_repository

    async def sync_permissions(self) -> None:
        """
        Đồng bộ danh sách quyền giữa cơ sở dữ liệu và danh sách quyền định nghĩa sẵn.
        Danh sách quyền tĩnh được định nghĩa dưới dạng dictionary:
            key   : tên quyền (str)
            value : tuple (mô tả, defaultGranted)
        """
        # Danh sách quyền tĩnh định nghĩa kèm trạng thái mặc định
        permissions = {
            # Quản lý người dùng
            'view_users': ('Xem danh sách người dùng', False),
            'view_user_details': ('Xem chi tiết người dùng', False),
            'create_user': ('Tạo người dùng mới', False),
            'edit_user': ('Chỉnh sửa thông tin người dùng', False),
            'delete_user': ('Xóa người dùng', False),
            'activate_deactivate_user': ('Kích hoạt/khóa người dùng', False),
            'manage_user_permissions': ('Quản lý phân quyền cá nhân', False),

            # Quản lý nhóm
            'view_groups': ('Xem danh sách nhóm', False),
            'view_group_details': ('Xem chi tiết nhóm', False),
            'create_group': ('Tạo nhóm mới', False),
            'edit_group': ('Chỉnh sửa thông tin nhóm', False),
            'delete_group': ('Xóa nhóm', False),
            'manage_group_members': ('Quản lý thành viên nhóm', False),
            'manage_group_permissions': ('Quản lý phân quyền nhóm', False),

            # Quản lý quyền
            'view_permissions': ('Xem danh sách quyền', False),
            'create_permission': ('Tạo quyền mới', False),
            'edit_permission': ('Chỉnh sửa quyền', False),
            'delete_permission': ('Xóa quyền', False),

            # Quản lý sản phẩm
            'view_products': ('Xem danh sách sản phẩm', True),
            'view_product_details': ('Xem chi tiết sản phẩm', True),
            'create_product': ('Tạo sản phẩm mới', False),
            'edit_product': ('Chỉnh sửa thông tin sản phẩm', False),
            'delete_product': ('Xóa sản phẩm', False),
            'manage_featured_products': ('Quản lý sản phẩm nổi bật', False),
            'manage_product_stock': ('Quản lý số lượng tồn kho', False),

            # Quản lý danh mục
            'view_categories': ('Xem danh sách danh mục', True),
            'create_category': ('Tạo danh mục mới', False),
            'edit_category': ('Chỉnh sửa danh mục', False),
            'delete_category': ('Xóa danh mục', False),

            # Quản lý giỏ hàng
            'create_cart': ('Thêm sản phẩm vào giỏ hàng', True),
            'view_carts': ('Xem giỏ hàng của người dùng', False),
            'edit_carts': ('Chỉnh sửa giỏ hàng của người dùng', False),
            'delete_carts': ('Xóa giỏ hàng của người dùng', False),

            # Quản lý danh sách yêu thích
            'view_wishlists': ('Xem danh sách yêu thích của người dùng', False),
            'edit_wishlists': ('Chỉnh sửa danh sách yêu thích của người dùng', False),
            'delete_wishlists': ('Xóa sản phẩm khỏi danh sách yêu thích', False),

            # Quản lý mã giảm giá
            'view_coupons': ('Xem danh sách mã giảm giá', False),
            'create_coupon': ('Tạo mã giảm giá mới', False),
            'edit_coupon': ('Chỉnh sửa mã giảm giá', False),
            'delete_coupon': ('Xóa mã giảm giá', False),
            'activate_deactivate_coupon': ('Kích hoạt/Vô hiệu hóa mã giảm giá', False),

            # Quản lý đơn hàng
            'view_orders': ('Xem danh sách đơn hàng', False),
            'view_order_details': ('Xem chi tiết đơn hàng', False),
            'update_shipping_status': ('Cập nhật trạng thái vận chuyển', False),
            'update_payment_status': ('Cập nhật trạng thái thanh toán', False),
            'delete_order': ('Xóa đơn hàng', False),

            # Quản lý đánh giá sản phẩm
            'view_reviews': ('Xem danh sách đánh giá', True),
            'approve_disapprove_review': ('Duyệt/Không duyệt đánh giá', False),
            'delete_review': ('Xóa đánh giá', False),

            # Quản lý toàn hệ thống
            'access_admin_dashboard': ('Truy cập Dashboard quản trị', False),
            'manage_system_settings': ('Quản lý cấu hình hệ thống', False),
            'view_system_logs': ('Quản lý nhật ký hệ thống', False),
        }

        # Lấy danh sách quyền hiện có trong cơ sở dữ liệu
        existing_permissions = await self.permission_repository.find_all()
        existing_names = [perm.name for perm in existing_permissions]

        async with AsyncSessionLocal() as session:
            # Thêm các quyền mới chưa có trong cơ sở dữ liệu
            for name, (description, default_granted) in permissions.items():
                if name not in existing_names:
                    permission = Permission()
                    permission.name = name
                    permission.description = description
                    permission.default = default_granted
                    session.add(permission)
            # Xóa các quyền thừa không có trong danh sách tĩnh
            for perm in existing_permissions:
                if perm.name not in permissions:
                    await session.delete(perm)
            await session.commit()

    async def get_all_permissions(self) -> list:
        """Trả về danh sách tất cả các quyền (Permission)."""
        return await self.permission_repository.find_all()

    async def view_all_permissions(self) -> list:
        """
        Lấy danh sách tên các quyền từ cơ sở dữ liệu.
        Trả về danh sách tên quyền.
        """
        permissions = await self.permission_repository.find_all()
        return [perm.name for perm in permissions]

    async def get_permission_by_id(self, id: int) -> Permission:
        """Lấy quyền theo ID."""
        return await self.permission_repository.find(id)

    async def get_permission_by_name(self, name: str) -> Permission:
        """Lấy quyền theo tên."""
        return await self.permission_repository.find_one_by({"name": name})

    async def create_permission(self, name: str, description: str = None) -> Permission:
        """
        Tạo mới một quyền.
        Nếu quyền đã tồn tại (theo tên) sẽ ném ngoại lệ.
        """
        existing = await self.get_permission_by_name(name)
        if existing:
            raise AppException("E2001", f"Permission with name '{name}' already exists.")
        permission = Permission()
        permission.name = name
        permission.description = description
        async with AsyncSessionLocal() as session:
            session.add(permission)
            await session.commit()
            await session.refresh(permission)
        return permission

    async def update_permission(self, id: int, data: dict) -> Permission:
        """
        Cập nhật thông tin của quyền.
        data có thể bao gồm các trường: name, description.
        """
        permission = await self.get_permission_by_id(id)
        if not permission:
            raise AppException("E2002", "Permission not found.")
        if "name" in data:
            # Kiểm tra xem nếu đổi tên thì không trùng với quyền khác
            existing = await self.get_permission_by_name(data["name"])
            if existing and existing.id != id:
                raise AppException("E2003", f"Permission with name '{data['name']}' already exists.")
            permission.name = data["name"]
        if "description" in data:
            permission.description = data["description"]
        async with AsyncSessionLocal() as session:
            session.add(permission)
            await session.commit()
            await session.refresh(permission)
        return permission

    async def delete_permission(self, id: int) -> None:
        """Xóa quyền theo ID."""
        permission = await self.get_permission_by_id(id)
        if not permission:
            raise AppException("E2004", "Permission not found.")
        async with AsyncSessionLocal() as session:
            await session.delete(permission)
            await session.commit()
