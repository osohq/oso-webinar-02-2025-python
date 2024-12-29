actor User {}

resource Organization {
    roles = ["member", "warehouse", "sales", "admin"];
    permissions = ["create_order"];

    "member" if "warehouse";
    "member" if "sales";
    "member" if "admin";

    "create_order" if "sales";
    # TODO(6): Admins can create orders.
    "create_order" if "admin";
}

resource Order {
    permissions = ["view_order", "fulfill_order", "cancel_order", "delete_order"];
    relations = {
        sold_by: User,
        org: Organization
    };

    # Admins have all permissions
    permission if "admin" on "org";

    "view_order" if "member" on "org";

    "cancel_order" if "sold_by";

    # Warehouse members may fulfill orgs.
    "fulfill_order" if "warehouse" on "org";
}
