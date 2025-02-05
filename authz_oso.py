from flask import jsonify, request
from functools import wraps
from pathlib import Path
from data import get_facts
from oso_cloud import Oso, Value

# Instantiate the Oso Cloud client
oso = Oso(
    url="http://localhost:8080",
     api_key="e_0123456789_12345_osotesttoken01xiIn",
)

# Load the policy
policy_contents = Path("policy.polar").read_text()
oso.policy(policy_contents)

# Route decorator
def authorize_order_action(action: str):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get the user and order objects to authorize the action against.
            user = Value("User", request.user.username)
            order = Value("Order", kwargs.get("order_id"))

            if not oso.authorize(user, action, order, get_facts()):
                return jsonify({"error": f"Permission denied for {action}"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
