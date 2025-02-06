import React, { useState, useEffect } from "react";
import { Plus, Check, X, Trash } from "lucide-react";
import "./App.css";

const OrderManagement = () => {
  const [error, setError] = useState("");
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState({});
  const [currentUser, setCurrentUser] = useState("");
  const [selectedUser, setSelectedUser] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newOrder, setNewOrder] = useState({
    customer: "",
    items: "",
    org: "",
  });

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await fetch("http://localhost:5000/users");
        const data = await response.json();
        console.log("Fetched users data:", data);
        setUsers(data);
        if (Object.keys(data).length > 0) {
          const username = Object.keys(data)[0];
          setSelectedUser(username);
        }
      } catch (err) {
        setError("Failed to fetch users");
      }
    };

    fetchUsers();
  }, []);

  useEffect(() => {
    setCurrentUser({ username: selectedUser, ...users[selectedUser] });
  }, [users, selectedUser]);

  useEffect(() => {
    if (currentUser) {
      fetchOrders();
    }
  }, [currentUser]);

  const fetchOrders = async () => {
    setError(null);
    if (!currentUser?.role) {
      setError("User role not available");
      return;
    }

    try {
      const response = await fetch("http://localhost:5000/orders", {
        headers: {
          "Content-Type": "application/json",
          "X-User-Username": currentUser.username,
          "X-User-Role": currentUser.role,
          "X-User-Org": currentUser.org,
        },
      });
      const data = await response.json();
      setOrders(Array.isArray(data) ? data : []);
    } catch (err) {
      setError("Failed to fetch orders");
    }
  };

  const handleCreateOrder = async () => {
    setError(null);
    try {
      const response = await fetch("http://localhost:5000/orders", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Username": currentUser.username,
          "X-User-Role": currentUser.role,
          "X-User-Org": currentUser.org,
        },
        body: JSON.stringify({
          ...newOrder,
          items: newOrder.items.split(",").map((item) => item.trim()),
        }),
      });
      if (response.ok) {
        setShowCreateDialog(false);
        setNewOrder({ customer: "", items: "", org: currentUser.org });
        fetchOrders();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAction = async (orderId, action) => {
    setError(null);
    try {
      const response = await fetch(
        `http://localhost:5000/orders/${orderId}/${action}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-User-Username": currentUser.username,
            "X-User-Role": currentUser.role,
            "X-User-Org": currentUser.org,
          },
        }
      );
      if (response.ok) {
        fetchOrders();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (orderId) => {
    setError(null);
    try {
      const response = await fetch(`http://localhost:5000/orders/${orderId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-User-Username": currentUser.username,
          "X-User-Role": currentUser.role,
          "X-User-Org": currentUser.org,
        },
      });
      if (response.ok) {
        fetchOrders();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleReset = async () => {
    try {
      const response = await fetch("http://localhost:5000/reset", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Username": currentUser.username,
          "X-User-Role": currentUser.role,
          "X-User-Org": currentUser.org,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to reset orders");
      }

      fetchOrders();
    } catch (error) {
      setError(error.message);
    }
  };

  return (
    <div className="container">
      <div className="header">
        <div>
          <h1 className="title">Order Management</h1>

          {selectedUser && (
            <select
              className="user-select"
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
            >
              {Object.keys(users).map((user) => (
                <option key={user} value={user}>
                  {user}
                </option>
              ))}
            </select>
          )}

          <p className="user-info">
            Organization: {currentUser?.org} | Role: {currentUser?.role}
          </p>
        </div>
        <button
          className="new-order-button"
          onClick={() => setShowCreateDialog(true)}
        >
          <Plus className="button-icon" />
          New Order
        </button>
      </div>

      {showCreateDialog && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2 className="modal-title">Create New Order</h2>
            <div className="form-container">
              <div className="form-group">
                <label className="form-label">Customer</label>
                <input
                  type="text"
                  className="form-input"
                  value={newOrder.customer}
                  onChange={(e) =>
                    setNewOrder({ ...newOrder, customer: e.target.value })
                  }
                />
              </div>
              <div className="form-group">
                <label className="form-label">Items (comma-separated)</label>
                <input
                  type="text"
                  className="form-input"
                  value={newOrder.items}
                  onChange={(e) =>
                    setNewOrder({ ...newOrder, items: e.target.value })
                  }
                />
              </div>
              <div className="button-group">
                <button
                  className="cancel-button"
                  onClick={() => setShowCreateDialog(false)}
                >
                  Cancel
                </button>
                <button className="create-button" onClick={handleCreateOrder}>
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      <div className="table-container">
        <table className="table">
          <thead>
            <tr className="table-header">
              <th className="table-header-cell">Customer</th>
              <th className="table-header-cell">Items</th>
              <th className="table-header-cell">Status</th>
              <th className="table-header-cell">Sold By</th>
              <th className="table-header-cell">Actions</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.id} className="table-row">
                <td className="table-cell">{order.customer}</td>
                <td className="table-cell">{order.items.join(", ")}</td>
                <td className="table-cell">{order.status}</td>
                <td className="table-cell">{order.sold_by}</td>
                <td className="table-cell">
                  <div className="action-buttons">
                    <button
                      className="action-button fulfill-button"
                      onClick={() => handleAction(order.id, "fulfill")}
                      title="Fulfill Order"
                    >
                      <Check className="button-icon" />
                    </button>
                    <button
                      className="action-button cancel-action-button"
                      onClick={() => handleAction(order.id, "cancel")}
                      title="Cancel Order"
                    >
                      <X className="button-icon" />
                    </button>
                    <button
                      style={{
                        backgroundColor: "#EF4444",
                        color: "white",
                        padding: "0.75rem",
                        borderRadius: "0.25rem",
                        ":hover": { backgroundColor: "#DC2626" },
                      }}
                      onClick={() => handleDelete(order.id)}
                      title="Delete Order"
                    >
                      <Trash className="button-icon" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <button onClick={handleReset} className="reset-button">
          Reset Orders
        </button>
      </div>
    </div>
  );
};

export default OrderManagement;
