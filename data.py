from dataclasses import dataclass
from enum import Enum

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
