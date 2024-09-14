from sqlalchemy import Column, ForeignKey, Table, Integer, String, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.sql import func
from app.config.database import Base
from app.mixins.columns import BaseMixin
from typing import Any
from enum import Enum as PyEnum


class OrderStatus(PyEnum):
    pending = "pending"
    processed = "processed"
    failed = "failed"


# Many-to-Many association table between Products and Categories
product_category = Table('product_category', Base.metadata,
    Column('product_id', String(length=50), ForeignKey('products.uuid')),
    Column('category_id', String(length=50), ForeignKey('categories.uuid'))
)


class Product(BaseMixin, Base):
    name = Column(String(255), nullable=False)
    description = Column(String(255))
    price = Column(Float, nullable=False)

    inventory = relationship("Inventory", back_populates="product")
    orders = relationship("Order", back_populates="product")


class Category(BaseMixin, Base):
    name = Column(String(255), nullable=False)
    description = Column(String(255))
    products: Any = relationship("Product", secondary=product_category)


class Inventory(BaseMixin, Base):
    product_id = Column(String(length=50), ForeignKey('products.uuid'), nullable=False)
    quantity = Column(Integer, nullable=False)
    product = relationship("Product", back_populates="inventory")


class Order(BaseMixin, Base):
    product_id = Column(String(length=50), ForeignKey('products.uuid'), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending, nullable=False)
    product = relationship("Product", back_populates="orders")
    order_logs = relationship("OrderLog", back_populates="order")


class OrderLog(BaseMixin, Base):
    order_id = Column(String(length=50), ForeignKey('orders.uuid'), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    error_message = Column(String(255), nullable=True)
    order = relationship("Order", back_populates="order_logs")