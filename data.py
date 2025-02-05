from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

# Hardcoded users and their roles
# TODO(1): Scale the app to include Zombo users. You'll see their data is
# visible to Acme users and vice versa.
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