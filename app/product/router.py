from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from app.product import cruds, schemas
from app.utils.crud_util import CrudUtil
from sqlalchemy.orm import Session

category_router = APIRouter(prefix="/category", tags=["Category"])
product_router = APIRouter(prefix="/product", tags=["Product"])
inventory_router = APIRouter(prefix="/inventory", tags=["Inventory"])
order_router = APIRouter(prefix="/order", tags=["Order"])
order_log_router = APIRouter(prefix="/order-log", tags=["Order Logs"])

# ================ [ Categories ] ================

@category_router.post(
"", status_code=201
)
def create_category(
    category_data: schemas.CategoryCreate,
    cu: CrudUtil = Depends(CrudUtil),
) -> schemas.CategorySchema:
    return cruds.create_category(cu, category_data)


@category_router.get("")
def list_categories(
    cu: CrudUtil = Depends(CrudUtil),
    skip: int = 0,
    limit: int = 100,
) -> schemas.CategoryList:
    return cruds.list_category(cu, skip, limit)

#
@category_router.get(
    "/{uuid}"
)
def category_detail(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    uuid: str,
) -> schemas.CategorySchema:
    return cruds.get_category_by_uuid(cu, uuid)


@category_router.put(
    "/{uuid}"
)
def update_category(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    uuid: str,
    update_data: schemas.CategoryUpdate,
) -> schemas.CategorySchema:
    return cruds.update_category(cu, uuid, update_data)


@category_router.delete(
    "/{uuid}"
)
def delete_category(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    uuid: str,
) -> dict[str, Any]:
    return cruds.delete_category(cu, uuid)


# ================ [ Products ] ================

@product_router.post(
"", status_code=201
)
def create_product(
    product_data: schemas.ProductCreate,
    cu: CrudUtil = Depends(CrudUtil),
) -> schemas.ProductSchema:
    return cruds.create_product(cu, product_data)


@product_router.get("")
def list_products(
    cu: CrudUtil = Depends(CrudUtil),
    skip: int = 0,
    limit: int = 100,
) -> schemas.ProductList:
    return cruds.list_products(cu, skip, limit)


@product_router.get(
    "/{uuid}"
)
def product_detail(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    uuid: str,
) -> schemas.ProductSchema:
    return cruds.get_product_by_uuid(cu, uuid)


@product_router.put(
    "/{uuid}"
)
def update_product(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    uuid: str,
    update_data: schemas.ProductUpdate,
) -> schemas.CategorySchema:
    return cruds.update_product(cu, uuid, update_data)


@product_router.delete(
    "/{uuid}"
)
def delete_product(
    *,
    cu: CrudUtil = Depends(CrudUtil),
    uuid: str,
) -> dict[str, Any]:
    return cruds.delete_product(cu, uuid)


@inventory_router.get("")
def list_inventories(
    cu: CrudUtil = Depends(CrudUtil),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    return cruds.get_inventory_list(cu, skip, limit)


# ================ [ Order ] ================

@order_router.post("", response_model=schemas.OrderSchema)
async def create_order(order: schemas.OrderCreate, cu: CrudUtil = Depends(CrudUtil)):
    try:
        return await cruds.process_order(cu, order)
    except HTTPException as e:
        raise e

@order_router.get("")
async def read_orders(
    cu: CrudUtil = Depends(CrudUtil),
    skip: int = 0,
    limit: int = 100,
):
    try:
        orders = cruds.get_all_orders(cu, skip, limit)
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


# ================ [ OrderLogs ] ================
@order_log_router.get("")
async def read_order_logs(
    cu: CrudUtil = Depends(CrudUtil)
):
    try:
        order_logs = cruds.get_all_order_logs(cu)
        return order_logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
