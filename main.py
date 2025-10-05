from fastapi import FastAPI, Request, Depends, Form, HTTPException, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import Product, User
from database import SessionLocal, engine, Base
from sqlalchemy.orm import Session
from auth import decode_access_token, verify_password, get_password_hash, create_access_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth import auth_router


app = FastAPI()

app.include_router(auth_router)

# Připojení složek
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Vytvoření databázových tabulek
Base.metadata.create_all(bind=engine)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme)):
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.get("/secure-data")
def get_secure_data(token: str = Depends(oauth2_scheme)):
    # ověření tokenu a jeho dekódování
    user = decode_access_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"msg": "Secure data", "user": user}

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


@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    hashed_pw = get_password_hash(password)
    user = User(username=username, hashed_password=hashed_pw)
    db.add(user)
    db.commit()
    return {"msg": "User created"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/profile")
def read_user_profile(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username}

def get_current_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only")
    return current_user
