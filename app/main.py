from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import settings
from app.product import router as product_router

app = FastAPI(
    title="Lorcan Bet Async"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(product_router.category_router)
app.include_router(product_router.product_router)
app.include_router(product_router.inventory_router)
app.include_router(product_router.order_router)
app.include_router(product_router.order_log_router)