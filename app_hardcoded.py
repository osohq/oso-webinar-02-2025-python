from enum import Enum
from typing import Dict
from dataclasses import dataclass
import json
import logging
from functools import wraps

from flask import Flask, jsonify, request
from flask_cors import CORS
from rich.logging import RichHandler

# TODO(1): Scale the app to include Zombo users. You'll see their data is
# visible to Acme users and vice versa.

# Hardcoded users and their roles
USERS = {
    "AcmeWarehouse": {"org": "Acme", "role": "warehouse"},
    "AcmeSales1": {"org": "Acme", "role": "sales"},
    "AcmeSales2": {"org": "Acme", "role": "sales"},
    "AcmeAdmin": {"org": "Acme", "role": "admin"},
    # "ZomboWarehouse": {"org": "Zombo", "role": "warehouse"},
    # "ZomboSales1": {"org": "Zombo", "role": "sales"},
    # "ZomboSales2": {"org": "Zombo", "role": "sales"},
    # "ZomboAdmin": {"org": "Zombo", "role": "admin"},
}


# Type definitions
@dataclass
class User:
    username: str
    org: str
    role: str


@dataclass
class Order:
    id: str
    org: str
    sold_by: str
    customer: str
    items: list
    status: str


@dataclass
class OrderWithPermissions(Order):
    permissions: list


class OrderStatus(Enum):
    PENDING = "pending"
    CANCELLED = "cancelled"
    FULFILLED = "fulfilled"


# App configuration
def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    setup_logging()
    return app


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


# Order management
class OrderService:
    @staticmethod
    def load_orders() -> Dict[str, Order]:
        try:
            with open("orders.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning("orders.json not found, returning empty orders")
            return {}

    @staticmethod
    def save_orders(orders: Dict[str, dict]) -> None:
        with open("orders.json", "w") as f:
            json.dump(orders, f, indent=4)

    @staticmethod
    def reset_orders():
        try:
            with open("orders_backup.json", "r") as f:
                orders_dict = json.load(f)
                OrderService.save_orders(orders_dict)
        except FileNotFoundError:
            return {}

    @staticmethod
    def update_order_status(order_id: str, status: OrderStatus) -> None:
        orders = OrderService.load_orders()
        if order_id in orders:
            orders[order_id]["status"] = status.value
            OrderService.save_orders(orders)
        else:
            logging.error("Order ID %s not found", order_id)


# Initialize services
app = create_app()


# Request hooks
@app.before_request
def attach_user():
    request.user = User(
        username=request.headers.get("X-User-Username"),
        role=request.headers.get("X-User-Role"),
        org=request.headers.get("X-User-Org"),
    )


class RBACPermission(Enum):
    """Represents the possible permissions a user can have."""

    VIEW_ORDERS = "view_orders"
    FULFILL_ORDER = "fulfill_order"
    CREATE_ORDER = "create_order"
    DELETE_ORDER = "delete_order"
    CANCEL_ORDER = "cancel_order"


# Role-based permissions
RBAC = {
    "warehouse": [RBACPermission.VIEW_ORDERS, RBACPermission.FULFILL_ORDER],
    "sales": [
        RBACPermission.VIEW_ORDERS,
        RBACPermission.CREATE_ORDER,
        RBACPermission.CANCEL_ORDER,
    ],
    "admin": [
        RBACPermission.VIEW_ORDERS,
        RBACPermission.CANCEL_ORDER,
        RBACPermission.DELETE_ORDER,
        RBACPermission.FULFILL_ORDER,
    ],
}


# Route decorators
def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = request.user["role"]
            if user_role is None or user_role not in RBAC:
                return (
                    jsonify(
                        {
                            "error": "Permission denied. User role is undefined or invalid."
                        }
                    ),
                    403,
                )
            if permission not in RBAC[user_role]:
                return (
                    jsonify(
                        {
                            "error": f"Permission denied. Role '{user_role}' cannot {permission}"
                        }
                    ),
                    403,
                )
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# TODO(3): We also need to add authorization to our API endpoints.

# def require_same_org():
#     def decorator(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             user_org = request.user["org"]
#             order_id = kwargs.get("order_id")
#             orders = orders = OrderService.load_orders()
#             if order_id not in orders:
#                 return jsonify({"error": "Order not found"}), 404
#             if orders[order_id]["org"] != user_org:
#                 return (
#                     jsonify({"error": "Unauthorized to access order from another org"}),
#                     403,
#                 )
#             return f(*args, **kwargs)

#         return decorated_function

#     return decorator


# Routes
@app.route("/orders", methods=["GET"])
def list_orders():
    orders = OrderService.load_orders()
    user_role = request.user.role
    user_org = request.user.org

    orders_w_permissions = []
    for order in orders.values():
        # TODO(2): Skip orders from other organizations. You'll now see that
        # each user can only see their own org's orders.

        # if order["org"] != user_org:
        #     continue

        order_permissions = [p.value for p in RBAC[user_role]]

        # TODO(5): We can prevent the button for canceling an order from even
        # displaying.

        # order_permissions = []
        # for p in RBAC[user_role]:
        #     if p == RBACPermission.CANCEL_ORDER and user_role == "sales":
        #         if order["sold_by"] == request.user.username:
        #             order_permissions.append(p.value)
        #     else:
        #         order_permissions.append(p.value)
        orders_w_permissions.append(
            OrderWithPermissions(**order, permissions=order_permissions)
        )

    return jsonify(orders_w_permissions)


@app.route("/orders", methods=["POST"])
@require_permission("create_order")
def create_order():
    orders = OrderService.load_orders()
    order_data = request.json

    order_id = (
        str(max(int(order_id) for order_id in orders.keys()) + 1) if orders else "1"
    )

    new_order = Order(
        id=order_id,
        org=request.user.org,
        sold_by=request.user.username,
        customer=order_data["customer"],
        items=order_data["items"],
        status=OrderStatus.PENDING.value,
    )

    orders[order_id] = vars(new_order)
    OrderService.save_orders(orders)
    return jsonify(vars(new_order)), 201


@app.route("/orders/<order_id>", methods=["DELETE"])
# TODO(3): Don't let users from other orgs interact with each other's orders.
# @require_same_org()
@require_permission("delete_order")
def delete_order(order_id: str):
    orders = OrderService.load_orders()
    del orders[order_id]
    OrderService.save_orders(orders)
    return "", 204


@app.route("/orders/<order_id>/cancel", methods=["POST"])
# TODO(3): Don't let users from other orgs interact with each other's orders.
# @require_same_org()
@require_permission("cancel_order")
def cancel_order(order_id: str):
    orders = OrderService.load_orders()
    order = orders[order_id]

    # TODO(4): We then discover that sales members can cancel other sales
    # members' orders. Prevent that from happening.

    # if request.user.role == "sales" and order["sold_by"] != request.user.username:
    #     return jsonify({"error": "Sales users can only cancel their own orders"}), 403

    order = OrderService.update_order_status(order_id, OrderStatus.CANCELLED)
    return jsonify(order)


@app.route("/orders/<order_id>/fulfill", methods=["POST"])
# TODO(3): Don't let users from other orgs interact with each other's orders.
# @require_same_org()
@require_permission("fulfill_order")
def fulfill_order(order_id: str):
    order = OrderService.update_order_status(order_id, OrderStatus.FULFILLED)
    return jsonify(order)


@app.route("/users", methods=["GET"])
def get_users():
    users_with_permissions = {
        user_name: {
            "org": user_data["org"],
            "role": user_data["role"],
            "orgPermissions": [p.value for p in RBAC[user_data["role"]]],
        }
        for user_name, user_data in USERS.items()
    }
    return jsonify(users_with_permissions)


# Not an "in-demo" endpoint; just a convenience feature for presenters.
@app.route("/reset", methods=["POST"])
def reset_orders():
    OrderService.reset_orders()
    return jsonify({"message": "Orders have been backed up to order_backup.json"}), 200


if __name__ == "__main__":
    app.run(debug=True)
