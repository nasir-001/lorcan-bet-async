from pydantic import BaseModel
from app.mixins.commons import ListBase
from app.mixins.schemas import BaseUACSchemaMixin
from app.mixins.commons import OrderStatusEnum
from datetime import datetime

# ================ [ Products ] ================

class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    category_uuid: str
    initial_quantity: int # For inventory management, not part of the Product model


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None


class ProductSchema(BaseUACSchemaMixin):
    price: float


class ProductList(ListBase):
    items: list[ProductSchema]

# ================ [ Categories ] ================

class CategoryCreate(BaseModel):
    name: str
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CategorySchema(BaseUACSchemaMixin):
    products: list[ProductSchema] | None = None


class CategoryList(ListBase):
    items: list[CategorySchema]


# ================ [ Inventory ] ================


class InventoryCreate(BaseModel):
    product_id: str
    quantity: int


class InventorySchema(BaseModel):
    product_id: str
    quantity: int


class InventoryList(ListBase):
    items: list[InventorySchema]


# ================ [ Order ] ================


class OrderCreate(BaseModel):
    product_id: str
    quantity: int


class OrderSchema(BaseModel):
    id: int
    product_id: str
    quantity: int
    status: OrderStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True


class OrderList(ListBase):
    items: list[OrderSchema]


# ================ [ OrderLogs ] ================

class OrderLogSchema(BaseModel):
    uuid: str
    order_id: str
    status: OrderStatusEnum
    processed_at: datetime
    error_message: str = None

    order: OrderSchema | None = None


class OrderLogList(ListBase):
    items: list[OrderLogSchema]
