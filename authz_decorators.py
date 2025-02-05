from typing import Dict
from data import User
from permissions import RBAC
from flask import jsonify, request
from functools import wraps
from data import User
from order_service import OrderService

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

def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user: User  = request.user
            if not has_permission(user, permission):
                return (
                    jsonify({"error": f"Permission denied. Role '{user.role}' cannot {permission}"}),
                    403,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_same_org():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user: User = request.user
            order_id = kwargs.get("order_id")
            orders = OrderService.load_orders()
            order = orders[order_id]

            if not has_same_org(user, order):
                return (
                    jsonify({"error": "Unauthorized to access order from another org"}),
                    403,
                )
            return f(*args, **kwargs)

        return decorated_function

    return decorator

def require_user_is_owner_if_sales():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user: User = request.user
            order_id = kwargs.get("order_id")
            order = OrderService.get_order(order_id)

            if not user_is_owner_if_in_sales(user, order):
                return (
                    jsonify({"error": "Sales users can only cancel their own orders"}),
                    403,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator
