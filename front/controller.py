from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from fastapi import APIRouter, Request

templates = Jinja2Templates(directory="templates")

app = APIRouter()

@app.get("/page/register")
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})