from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from api.controller import router
from database import init_db

app = FastAPI()

app.include_router(router)

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url='/docs')

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)