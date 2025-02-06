import logging

from flask import Flask, jsonify, request
from flask_cors import CORS
from rich.logging import RichHandler

# Fake databasey stuff
from data import USERS, User, Order, OrderWithPermissions, OrderStatus
from permissions import RBAC

# Fake orders service
from order_service import OrderService

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
def create_order():
    # Get the user's permissions based on their role
    user_role = request.user.role
    permissions = [p.value for p in RBAC[user_role]]
    # Verify that the user has the "create_order" permission
    if not "create_order" in permissions:
        return (
            jsonify({"error": f"Permission denied. Role '{user_role}' cannot create orders"}),
            403,
        )
 
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
def delete_order(order_id: str):
    # Get the user's permissions based on their role
    user_role = request.user.role
    permissions = [p.value for p in RBAC[user_role]]
    # Verify that the user has the "delete_order" permission
    if not "delete_order" in permissions:
        return (
            jsonify({"error": f"Permission denied. Role '{user_role}' cannot delete orders"}),
            403,
        )

    # Users can only delete orders in their own org.
    user_org = request.user.org
    orders = OrderService.load_orders()
    order_org = orders[order_id]["org"]

#    if user_org != order_org:
#        return (
#            jsonify({"error": f"Permission denied. User org ({user_org}) does not match order org ({order_org})"}),
#            403,
#        )

    del orders[order_id]
    OrderService.save_orders(orders)
    return "", 204


@app.route("/orders/<order_id>/fulfill", methods=["POST"])
def fulfill_order(order_id: str):
    # Get the user's permissions based on their role
    user_role = request.user.role
    permissions = [p.value for p in RBAC[user_role]]
    # Verify that the user has the "fulfill_order" permission
    if not "fulfill_order" in permissions:
        return (
            jsonify({"error": f"Permission denied. Role '{user_role}' cannot cancel orders"}),
            403,
        )

    # Get order info
    orders = OrderService.load_orders()
    order = orders[order_id]

    # Users can only fulfill orders in their own org.
    user_org = request.user.org
    order_org = order["org"]
    if user_org != order_org:
        return (
            jsonify({"error": f"Permission denied. User org ({user_org}) does not match order org ({order_org})"}),
            403,
        )

    order = OrderService.update_order_status(order_id, OrderStatus.FULFILLED)
    return jsonify(order)


@app.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id: str):
    # Get the user's permissions based on their role
    user_role = request.user.role
    permissions = [p.value for p in RBAC[user_role]]
    # Verify that the user has the "cancel_order" permission
    if not "cancel_order" in permissions:
        return (
            jsonify({"error": f"Permission denied. Role '{user_role}' cannot cancel orders"}),
            403,
        )

    # Get order info
    orders = OrderService.load_orders()
    order = orders[order_id]

    # Users can only cancel orders in their own org.
    user_org = request.user.org
    order_org = order["org"]
    if user_org != order_org:
        return (
            jsonify({"error": f"Permission denied. User org ({user_org}) does not match order org ({order_org})"}),
            403,
        )

    # Salespeople should only be able to cancel their own orders
    if request.user.role == "sales" and order["sold_by"] != request.user.username:
        return jsonify({"error": "Sales users can only cancel their own orders"}), 403

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
