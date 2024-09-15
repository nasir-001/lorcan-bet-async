from typing import Any
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.config.database import SessionLocal
from app.utils.crud_util import CrudUtil
from app.product import models, schemas
import asyncio
from datetime import datetime


# Create a new category
def create_category(
    cu: CrudUtil,
    category_data: schemas.CategoryCreate
) -> models.Category:

    category: models.Category = cu.create_model(
        model_to_create=models.Category,
        create=category_data
    )

    return category


# List categories
def list_category(cu: CrudUtil, skip: int, limit: int) -> schemas.CategoryList:
    roles: dict[str, Any] = cu.list_model(
        model_to_list=models.Category,
        skip=skip,
        limit=limit
    )

    return schemas.CategoryList(**roles)


# Get category by UUID
def get_category_by_uuid(
    cu: CrudUtil,
    uuid: str,
) -> models.Category:

    category: models.Category = cu.get_model_or_404(
        model_to_get=models.Category,
        model_conditions={"uuid": uuid}
    )
    return category


# Update category by UUID
def update_category (
    cu: CrudUtil,
    uuid: str,
    update_data: schemas.CategoryUpdate,
) -> models.Category:
    category: models.Category = cu.update_model(
        model_to_update=models.Category,
        update=update_data,
        update_conditions={"uuid": uuid},
        autocommit=True,
    )

    cu.db.commit()
    cu.db.refresh(category)

    return category


# Delete category by UUID
def delete_category(cu: CrudUtil, uuid: str) -> dict[str, Any]:
    return cu.delete_model(
        model_to_delete=models.Category,
        delete_conditions={"uuid": uuid}
    )


# ================ [ Products ] ================

# Create a new product
def create_product(
    cu: CrudUtil,
    product_data: schemas.ProductCreate
) -> models.Product:
    # Step 1: First, create the product (without initial_quantity)
    product: models.Product = cu.create_model(
        model_to_create=models.Product,
        create=product_data,
    )

    # Now associate the product with the category
    add_product_to_category(
        cu=cu,
        product_uuid=product.uuid,
        category_uuid=product_data.category_uuid,
    )

    # Step 3: Initialize the inventory for the product
    initialize_inventory(
        cu=cu,
        product_uuid=product.uuid,
        initial_quantity=product_data.initial_quantity,
    )

    return product


# List products
def list_products(cu: CrudUtil, skip: int, limit: int) -> schemas.ProductList:
    products: dict[str, Any] = cu.list_model(
        model_to_list=models.Product,
        skip=skip,
        limit=limit
    )

    return schemas.ProductList(**products)


# Get product by UUID
def get_product_by_uuid(
    cu: CrudUtil,
    uuid: str,
) -> models.Product:

    product: models.Product = cu.get_model_or_404(
        model_to_get=models.Product,
        model_conditions={"uuid": uuid}
    )

    return product


# Update product by UUID
def update_product(
    cu: CrudUtil,
    uuid: str,
    update_data: schemas.ProductUpdate,
) -> models.Product:
    product: models.Product = cu.update_model(
        model_to_update=models.Product,
        update=update_data,
        update_conditions={"uuid": uuid},
        autocommit=True,
    )

    cu.db.commit()
    cu.db.refresh(product)

    return product


# Delete product by UUID
def delete_product(cu: CrudUtil, uuid: str) -> dict[str, Any]:
    return cu.delete_model(
        model_to_delete=models.Product,
        delete_conditions={"uuid": uuid}
    )


# ================ [ Utils ] ================

# Add product to catetory
def add_product_to_category(
    cu: CrudUtil,
    product_uuid: str,
    category_uuid: str
) -> models.Category:
    # Retrieve the product and category by their UUIDs
    product: models.Product = cu.get_model_or_404(
        model_to_get=models.Product,
        model_conditions={"uuid": product_uuid}
    )

    category: models.Category = cu.get_model_or_404(
        model_to_get=models.Category,
        model_conditions={"uuid": category_uuid}
    )

    # Add the product to the category's product list
    category.products.append(product)

    # Commit the transaction to save changes
    cu.db.commit()
    cu.db.refresh(category)

    return category


# The function to initialize the inventory for the product
def initialize_inventory(cu: CrudUtil, product_uuid: str, initial_quantity: int):
    # Create a new inventory entry using the InventoryCreate schema
    inventory_data = schemas.InventoryCreate(
        product_id=product_uuid,
        quantity=initial_quantity
    )
    return cu.create_model(
        model_to_create=models.Inventory,
        create=inventory_data
    )


# The function to retrieve all inventories
def get_inventory_list(
    cu: CrudUtil,
    skip: int,
    limit: int
) -> schemas.InventoryList:
    inventories_query = cu.db.query(models.Inventory).offset(skip).limit(limit).all()
    inventory_list = [
        schemas.InventorySchema(
            product_id=inventory.product_id,
            quantity=inventory.quantity
        )
        for inventory in inventories_query
    ]

    return inventory_list


# ================ [ Order ] ================

async def process_order(cu: CrudUtil, order_data: schemas.OrderCreate, max_retries: int = 3):
    try:
        # Start a new transaction
        with cu.db.begin() as transaction:
            # Check inventory with FOR UPDATE to acquire a lock
            inventory = cu.db.query(models.Inventory).filter(
                models.Inventory.product_id == order_data.product_id
            ).with_for_update().first()

            if not inventory or inventory.quantity < order_data.quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock")

            # Process the order
            new_order = models.Order(
                product_id=order_data.product_id,
                quantity=order_data.quantity,
                status=models.OrderStatus.pending
            )
            cu.db.add(new_order)
            cu.db.flush()

            # Log the order creation
            log_entry = models.OrderLog(
                order_id=new_order.uuid,
                status=models.OrderStatus.pending,
                processed_at=datetime.utcnow(),
                error_message=None
            )
            cu.db.add(log_entry)

            # Retry logic for payment
            payment_success = await retry_payment(max_retries)

            if payment_success:
                # Update inventory and order status within the same transaction
                inventory.quantity -= order_data.quantity
                new_order.status = models.OrderStatus.processed

                # Log the successful payment
                log_entry = models.OrderLog(
                    order_id=new_order.uuid,
                    status=models.OrderStatus.processed,
                    processed_at=datetime.utcnow(),
                    error_message=None
                )
                cu.db.add(log_entry)

            else:
                # Revert Order if payment fails within the same transaction
                new_order.status = models.OrderStatus.failed

                # Log the failed payment
                log_entry = models.OrderLog(
                    order_id=new_order.uuid,
                    status=models.OrderStatus.failed,
                    processed_at=datetime.utcnow(),
                    error_message="Payment failed after retries"
                )
                cu.db.add(log_entry)

            # Commit the transaction to save all changes
            cu.db.commit()

        # Fetch the order in a new session for validation
        with SessionLocal() as session:
            # Re-query the order to get it in the new session
            order_in_db = session.query(models.Order).filter_by(uuid=new_order.uuid).first()
            if not order_in_db:
                raise HTTPException(status_code=404, detail="Order not found")

            # Create OrderSchema instance using model_validate
            return schemas.OrderSchema.model_validate(order_in_db)

    except SQLAlchemyError as e:
        # Handle exceptions and rollback if necessary
        cu.db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error occurred: {e}") from e


async def retry_payment(max_retries: int):
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        print(f"Attempting payment, try {attempt} of {max_retries}")
        payment_success = await simulate_payment()

        if payment_success:
            return True

        # Exponential backoff: wait before retrying
        await asyncio.sleep(2 ** attempt)

    # After max retries, return failure
    return False


async def simulate_payment():
    await asyncio.sleep(1)  # Simulate external payment service
    # Simulate payment result, randomize success/failure for testing
    return True


def get_all_orders(cu: CrudUtil, skip: int, limit: int) -> schemas.OrderList:
    orders: dict[str, Any] = cu.list_model(
        model_to_list=models.Order,
        skip=skip,
        limit=limit
    )

    return schemas.OrderList(**orders)


# ================ [ OrderLog ] ================

def get_all_order_logs(cu) -> list[schemas.OrderLogSchema]:
    order_logs = cu.db.query(models.OrderLog).all()
    return order_logs