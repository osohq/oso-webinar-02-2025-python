# Walkthrough

## Pre-setup

1. Produce the diff between `app_hardcoded.py` and `app_oso.py`.

   ```bash
   git diff app_hardcoded_final.py app_oso.py
   ```

   This diff lets us show what we changed to get from from the hardcoded app to
   the Oso-backed app, like this:

   ```diff
   diff --git a/app_hardcoded_final.py b/app_oso.py
         --- a/app_hardcoded_final.py
      +++ b/app_oso.py
      @@ -1,12 +1,14 @@
    from enum import Enum
   -from typing import Dict
   +from typing import List, Tuple, Dict, Any
    from dataclasses import dataclass
   +from pathlib import Path
    import json
    import logging
    from functools import wraps

    from flask import Flask, jsonify, request
    from flask_cors import CORS
   +from oso_cloud import Oso, Value, typed_var
    from rich.logging import RichHandler

    # Hardcoded users and their roles
   @@ -67,6 +69,53 @@ def setup_logging() -> None:
        )
   ```

   This diff should make it easy to walk through, in the demo, what we changed
   to integrate Oso with the app.

## Setup

### Run backend

```bash
source venv/bin/activate
python app_hardcoded.py
```

### Run frontend

```bash
cd order-management
npm run dev
```

Then navigate to `http://localhost:5173/` in your browser.

## Run the hardcoded demo

1. **Scale the app to include Zombo users**:

   - The application currently has hardcoded users only for the "Acme"
     organization. There is a need to add users for the "Zombo" organization,
     ensuring that their data is not visible to "Acme" users and vice versa.

     This is `TODO(1)`.

2. **Skip orders from other organizations**:

   - Modify the logic in the `list_orders` route to ensure that users can only
     see orders from their own organization. This will enhance data privacy and
     security.

     This is `TODO(2)`.

3. **Add authorization to API endpoints**:

   - Implement authorization checks to prevent users from different
     organizations from interacting with each other's orders. This is crucial
     for maintaining data integrity and security.

     This is `TODO(3)`.

4. **Prevent sales members from canceling other sales members' orders**:

   - Update the logic in the `cancel_order` route to ensure that sales users can
     only cancel their own orders. This will prevent unauthorized cancellations
     and maintain accountability.

     This is `TODO(4)`.

5. **Prevent the button for canceling an order from displaying**:

   - Adjust the permissions logic in the `list_orders` route to ensure that the
     cancel button is not displayed for users who do not have the permission to
     cancel orders, particularly for sales users.

     This is `TODO(5)`.

At this point, our simple hardcoded RBAC app has become very complex and is no
longer truly RBAC. To fulfill our needs, we've had to introduce
relationship-based authorization decisions, such as associating users with
specific organizations, as well as orders with the user who sold them.

We can instead use Oso

## Run the Oso-backed app

1. Stop the running backend server.
1. Run the Oso-backed server:

   ```bash
   source venv/bin/activate
   python app_oso.py
   ```

1. Allow admins to create orders and re-deploy the policy either in the UI.

   This shows that you can change your authorization logic without re-deploying
   your application or writing any imperative code.

   This is `TODO(6)`.
