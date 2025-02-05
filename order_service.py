import json
from typing import Dict
import logging
from data import Order, OrderStatus

# Order management
class OrderService:
    @staticmethod
    def load_orders() -> Dict[str, Order]:
        try:
            with open("orders.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning("orders.json not found, returning empty orders")
            return {}

    @staticmethod
    def get_order(order_id: int):
        orders = OrderService.load_orders()
        return orders[order_id]

    @staticmethod
    def save_orders(orders: Dict[str, dict]) -> None:
        with open("orders.json", "w") as f:
            json.dump(orders, f, indent=4)

    @staticmethod
    def reset_orders():
        try:
            with open("orders_backup.json", "r") as f:
                orders_dict = json.load(f)
                OrderService.save_orders(orders_dict)
        except FileNotFoundError:
            return {}

    @staticmethod
    def update_order_status(order_id: str, status: OrderStatus) -> None:
        orders = OrderService.load_orders()
        if order_id in orders:
            orders[order_id]["status"] = status.value
            OrderService.save_orders(orders)
        else:
            logging.error("Order ID %s not found", order_id)

