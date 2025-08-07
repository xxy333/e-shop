from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import Product
from database import SessionLocal, engine, Base

app = FastAPI()

# Připojení složek
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Vytvoření databázových tabulek
Base.metadata.create_all(bind=engine)

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    db = SessionLocal()
    products = db.query(Product).all()
    return templates.TemplateResponse("index.html", {"request": request, "products": products})

@app.post("/add", response_class=HTMLResponse)
def add_product(name: str = Form(...), price: float = Form(...)):
    db = SessionLocal()
    product = Product(name=name, price=price)
    db.add(product)
    db.commit()
    return RedirectResponse("/", status_code=303)
