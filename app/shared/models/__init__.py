"""
Modelos compartidos del sistema de permisos
"""
from .permission import Permission
from .permission_template import PermissionTemplate
from .permission_template_item import PermissionTemplateItem
from .user_permission import UserPermission
from .system_config import SystemConfig

__all__ = [
    "Permission",
    "PermissionTemplate",
    "PermissionTemplateItem",
    "UserPermission",
    "SystemConfig",
]