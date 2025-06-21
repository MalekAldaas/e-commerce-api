from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


def is_in_group(user, group_name):
    return user.group.filter(name=group_name).exists()

class RolePermission(BasePermission):

    def has_permission(self, request, view):
        if not hasattr(view, 'permission_map'):
            return True

        allowed_roles = [role.lower() for role in view.permission_map.get(request.method, [])]
        
        if 'any' in allowed_roles:
            return True

        if request.user.is_authenticated:
            user_groups = [g.name.lower() for g in request.user.groups.all()]

            if not user_groups:
                user_groups = ['customer']

            if any(role in allowed_roles for role in user_groups):
                return True

        return False