# from enum import Enum
# from flask import Flask, jsonify, request
# from flask_cors import CORS
# from functools import wraps
# import json
# from pathlib import Path
# from dataclasses import dataclass

# app = Flask(__name__)
# CORS(app)

# # Hardcoded users and their roles
# USERS = {
#     "Acme Warehouse": {"org": "Acme", "role": "warehouse"},
#     "Acme Sales 1": {"org": "Acme", "role": "sales"},
#     "Acme Sales 2": {"org": "Acme", "role": "sales"},
#     "Acme Admin": {"org": "Acme", "role": "admin"},
#     "Zombo Warehouse": {"org": "Zombo", "role": "warehouse"},
#     "Zombo Sales 1": {"org": "Zombo", "role": "sales"},
#     "Zombo Sales 2": {"org": "Zombo", "role": "sales"},
#     "Zombo Admin": {"org": "Zombo", "role": "admin"},
# }

# @dataclass
# class User:
#     username: str
#     org: str
#     role: str

# @dataclass
# class Order:
#     id: str
#     org: str
#     sold_by: str
#     customer: str
#     items: list
#     status: str

# class CompanyPermission(Enum):
#     """Represents the possible permissions a user can have."""
#     VIEW_ORDERS = "view_orders"
#     FULFILL_ORDER = "fulfill_order"
#     CREATE_ORDER = "create_order"
#     DELETE_ORDER = "delete_order"
#     CANCEL_ORDER = "cancel_order"

# # Role-based permissions
# PERMISSIONS = {
#     "warehouse": [CompanyPermission.VIEW_ORDERS, CompanyPermission.FULFILL_ORDER],
#     "sales": [CompanyPermission.VIEW_ORDERS, CompanyPermission.CREATE_ORDER, CompanyPermission.CANCEL_ORDER],
#     "admin": [CompanyPermission.VIEW_ORDERS, CompanyPermission.CREATE_ORDER, CompanyPermission.CANCEL_ORDER, CompanyPermission.DELETE_ORDER, CompanyPermission.FULFILL_ORDER]
# }

# def load_orders():
#     try:
#         with open('orders.json', 'r') as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return {}

# def load_backup_orders():
#     try:
#         with open('orders_backup.json', 'r') as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return {}

# def save_orders(orders):
#     with open('orders.json', 'w') as f:
#         json.dump(orders, f, indent=4)

# def get_user_from_headers():
#     return {
#         "username": request.headers.get('X-User-Username'),
#         "role": request.headers.get('X-User-Role'),
#         "org": request.headers.get('X-User-Org')
#     }

# # Modify the app to attach user to request
# @app.before_request
# def attach_user():
#     request.user = get_user_from_headers()

# def require_permission(permission):
#     def decorator(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             user_role = request.user["role"]
#             if user_role is None or user_role not in PERMISSIONS:
#                 return jsonify({
#                     "error": "Permission denied. User role is undefined or invalid."
#                 }), 403
#             if permission not in PERMISSIONS[user_role]:
#                 return jsonify({
#                     "error": f"Permission denied. Role '{user_role}' cannot {permission}"
#                 }), 403
#             return f(*args, **kwargs)
#         return decorated_function
#     return decorator

# def require_same_org():
#     def decorator(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             user_org = request.user["org"]
#             order_id = kwargs.get("order_id")
#             orders = load_orders()
#             if order_id not in orders:
#                 return jsonify({"error": "Order not found"}), 404
#             if orders[order_id]["org"] != user_org:
#                 return jsonify({"error": "Unauthorized to access order from another org"}), 403
#             return f(*args, **kwargs)
#         return decorated_function
#     return decorator

# @app.route("/orders", methods=["GET"])
# @require_permission(CompanyPermission.VIEW_ORDERS)
# def list_orders():
#     user_org = request.user["org"]
#     orders = load_orders()
#     filtered_orders = {order_id: order for order_id, order in orders.items() if order["org"] == user_org}
#     return jsonify(list(filtered_orders.values()))

# @app.route("/orders", methods=["POST"])
# @require_permission(CompanyPermission.CREATE_ORDER)
# def create_order():
#     orders = load_orders()
#     order = request.json
#     order_id = str(len(orders) + 1)
#     user_org = request.user["org"]
#     user_username = request.user["username"]
#     new_order = {
#         "id": order_id,
#         "org": user_org,
#         "sold_by": user_username,
#         "customer": order["customer"],
#         "items": order["items"],
#         "status": "pending"
#     }
#     orders[order_id] = new_order
#     save_orders(orders)
#     return jsonify(new_order), 201

# @app.route("/orders/<order_id>", methods=["DELETE"])
# @require_permission(CompanyPermission.DELETE_ORDER)
# @require_same_org()
# def delete_order(order_id):
#     orders = load_orders()
#     del orders[order_id]
#     save_orders(orders)
#     return "", 204

# @app.route("/orders/<order_id>/cancel", methods=["POST"])
# @require_permission(CompanyPermission.CANCEL_ORDER)
# @require_same_org()
# def cancel_order(order_id):
#     orders = load_orders()
#     user_username = request.user["username"]
#     order = orders[order_id]
#     if order["sold_by"] != user_username and request.user["role"] != "admin":
#         return jsonify({"error": "Unauthorized to cancel order"}), 403

#     order["status"] = "cancelled"
#     save_orders(orders)
#     return jsonify(order)

# @app.route("/orders/<order_id>/fulfill", methods=["POST"])
# @require_permission(CompanyPermission.FULFILL_ORDER)
# @require_same_org()
# def fulfill_order(order_id):
#     orders = load_orders()
#     orders[order_id]["status"] = "fulfilled"
#     save_orders(orders)
#     return jsonify(orders[order_id])

# def get_permissions_for_role(role):
#     return [p.value for p in PERMISSIONS[role]]

# @app.route("/users", methods=["GET"])
# def get_users():
#     # Return all users with their org, role and permissions
#     users_with_permissions = {
#         user_name: {
#             "org": user_data["org"],
#             "role": user_data["role"],
#             "permissions": get_permissions_for_role(user_data["role"])
#         }
#         for user_name, user_data in USERS.items()
#     }
#     return jsonify(users_with_permissions)

# @app.route("/reset", methods=["POST"])
# def reset_orders():
#     orders = load_backup_orders()
#     save_orders(orders)
#     return jsonify({"message": "Orders have been backed up to order_backup.json"}), 200

# if __name__ == "__main__":
#     app.run(debug=True)
