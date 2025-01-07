from fastapi import FastAPI
from app.database import engine, Base
from app.routes import router

app = FastAPI()

app.include_router(router)

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)

@app.on_event("shutdown")
async def shutdown():
    pass
