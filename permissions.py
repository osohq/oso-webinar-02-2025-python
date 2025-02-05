from enum import Enum

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

