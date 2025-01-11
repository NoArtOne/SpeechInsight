import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from api.controller import router
from database import init_db
from rabbit_mq.consumer_rabbit import start_consume

app = FastAPI()

app.include_router(router)

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url='/docs')

@app.on_event("startup")
async def startup_event():
    init_db()
    asyncio.create_task(start_consume())

if __name__ == "__main__":
    import uvicorn
    print("Запуск uvicorn...")
    uvicorn.run(app, host="localhost", port=8000)