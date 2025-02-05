from typing import Dict
from data import User, Order, OrderWithPermissions, OrderStatus
from permissions import RBAC, RBACPermission
# Abstracted authorization logic

def has_permission(user: User, permission: str):
    user_role = user.role
    permissions = [p.value for p in RBAC[user_role]]

    return permission in permissions

def has_same_org(user: User, order: Dict):
    return user.org == order["org"]

def user_is_owner_if_in_sales(user: User, order: Dict):
    if user.role == "sales" and order["sold_by"] != user.username:
        return False
    
    # Note: This assumes we don't enter this function with a user
    # who has an invalid role for the action 
    return True
