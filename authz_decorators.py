from flask import jsonify, request
from functools import wraps
from data import User
from authz import has_permission, has_same_org, user_is_owner_if_in_sales
from order_service import OrderService

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