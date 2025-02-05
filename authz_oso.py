from oso_cloud import Oso, Value, typed_var
from pathlib import Path
from typing import List, Tuple, Dict, Any
from order_service import OrderService
from data import USERS
from flask import jsonify, request
from functools import wraps

oso = Oso(
    url="http://localhost:8080",
     api_key="e_0123456789_12345_osotesttoken01xiIn",
)

policy_contents = Path("policy.polar").read_text()
oso.policy(policy_contents)

# Route decorators
def require_permission(action: str):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = Value("User", request.user.username)
            order_id = kwargs.get("order_id")
            order = Value("Order", order_id)

            if not oso.authorize(user, action, order, get_facts()):
                return jsonify({"error": f"Permission denied for {action}"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator

    
# This is just a convenience feature for the demo; in a real app you would
# use Oso's centralized or localized authorization data.
def get_facts() -> List[Tuple]:
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
