import logging

from flask import Flask, jsonify, request
from flask_cors import CORS
from rich.logging import RichHandler

# Fake databasey stuff
from data import USERS, User, Order, OrderWithPermissions, OrderStatus
from permissions import RBAC

# Fake orders service
from order_service import OrderService

# authz functions (decorators)
from authz_decorators import require_permission, require_same_org, require_user_is_owner_if_sales

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
        #    continue

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
@require_permission("delete_order")
@require_same_org()
def delete_order(order_id: str):
    orders = OrderService.load_orders()
    del orders[order_id]
    OrderService.save_orders(orders)
    return "", 204


@app.route("/orders/<order_id>/fulfill", methods=["POST"])
@require_permission("fulfill_order")
@require_same_org()
def fulfill_order(order_id: str):
    order = OrderService.update_order_status(order_id, OrderStatus.FULFILLED)
    return jsonify(order)


@app.route("/orders/<order_id>/cancel", methods=["POST"])
@require_permission("cancel_order")
@require_same_org()
@require_user_is_owner_if_sales()
def cancel_order(order_id: str):
    orders = OrderService.get_order(order_id)
    order = OrderService.update_order_status(order_id, OrderStatus.CANCELLED)
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
