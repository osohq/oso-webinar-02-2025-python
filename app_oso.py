from enum import Enum
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import json
import logging
from functools import wraps

from flask import Flask, jsonify, request
from flask_cors import CORS
from oso_cloud import Oso, Value, typed_var
from rich.logging import RichHandler

# Hardcoded users and their roles
USERS = {
    "AcmeWarehouse": {"org": "Acme", "role": "warehouse"},
    "AcmeSales1": {"org": "Acme", "role": "sales"},
    "AcmeSales2": {"org": "Acme", "role": "sales"},
    "AcmeAdmin": {"org": "Acme", "role": "admin"},
    "ZomboWarehouse": {"org": "Zombo", "role": "warehouse"},
    "ZomboSales1": {"org": "Zombo", "role": "sales"},
    "ZomboSales2": {"org": "Zombo", "role": "sales"},
    "ZomboAdmin": {"org": "Zombo", "role": "admin"},
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


# Authorization
class AuthService:
    def __init__(self):
        self.oso = Oso(
            url="https://cloud.osohq.com",
            api_key="e_7OVkT6IxPvzOO13TbNhMxp_6RxEAMYiZO3_1R1am94nZcjoxzBCz8TZ5723LWtW",
        )
        self._load_policy()

    def _load_policy(self):
        policy_contents = Path("policy.polar").read_text()
        self.oso.policy(policy_contents)

    # This is just a convenience feature for the demo; in a real app you would
    # use Oso's centralized or localized authorization data.
    def get_facts(self) -> List[Tuple]:
        org_facts = [
            (
                "has_role",
                Value("User", key),
                data["role"],
                Value("Organization", data["org"]),
            )
            for key, data in USERS.items()
        ]

        orders = OrderService.load_orders()

        order_facts = [
            (relation, Value("Order", data["id"]), field, Value(type, data[field]))
            for _, data in orders.items()
            for relation, field, type in [
                ("has_relation", "org", "Organization"),
                ("has_relation", "sold_by", "User"),
            ]
        ]

        return org_facts + order_facts

    def authorize(self, user: Value, action: str, resource: Value) -> bool:
        try:
            self.oso.authorize(user, action, resource, self.get_facts())
            return True
        except Exception:
            return False


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


# Route decorators
def require_permission(action: str):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = Value("User", request.user.username)
            order_id = kwargs.get("order_id")

            if order_id:
                resource = Value("Order", order_id)
            else:
                resource = Value("Organization", request.user.org)

            if not auth_service.authorize(user, action, resource):
                return jsonify({"error": f"Permission denied for {action}"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Initialize services
app = create_app()
auth_service = AuthService()


# Request hooks
@app.before_request
def attach_user():
    request.user = User(
        username=request.headers.get("X-User-Username"),
        role=request.headers.get("X-User-Role"),
        org=request.headers.get("X-User-Org"),
    )


# Routes
@app.route("/orders", methods=["GET"])
def list_orders():
    action = typed_var("String")
    order = typed_var("Order")

    order_actions = (
        auth_service.oso.build_query(
            ("allow", Value("User", request.user.username), action, order)
        )
        .with_context_facts(auth_service.get_facts())
        .evaluate((order, action))
    )

    order_permission_map = {}
    for order_id, action in order_actions:
        order_permission_map.setdefault(order_id, []).append(action)

    orders = OrderService.load_orders()
    orders_w_permissions = [
        OrderWithPermissions(**order, permissions=order_permission_map[order_id])
        for order_id, order in orders.items()
        if order_id in order_permission_map
        and any(perm in ("*", "view_order") for perm in order_permission_map[order_id])
    ]

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
@require_permission("delete_order")
def delete_order(order_id: str):
    orders = OrderService.load_orders()
    del orders[order_id]
    OrderService.save_orders(orders)
    return "", 204


@app.route("/orders/<order_id>/cancel", methods=["POST"])
@require_permission("cancel_order")
def cancel_order(order_id: str):
    order = OrderService.update_order_status(order_id, OrderStatus.CANCELLED)
    return jsonify(order)


@app.route("/orders/<order_id>/fulfill", methods=["POST"])
@require_permission("fulfill_order")
def fulfill_order(order_id: str):
    order = OrderService.update_order_status(order_id, OrderStatus.FULFILLED)
    return jsonify(order)


@app.route("/users", methods=["GET"])
def get_users():
    facts = auth_service.get_facts()
    users_with_permissions = {
        user_name: {
            "org": user_data["org"],
            "role": user_data["role"],
            "orgPermissions": auth_service.oso.actions(
                Value("User", user_name), Value("Organization", user_data["org"]), facts
            ),
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
