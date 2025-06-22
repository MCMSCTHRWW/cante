from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from database import Base, engine, SessionLocal
import models
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")

# Seguridad
SECRET_KEY = "mcmscthrww"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Crear las tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

# Dependencia para la DB
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")

# Modelos de entrada
class RegistroUsuario(BaseModel):
  email: str
  password: str
  oposicion: str = None

class LoginForm(BaseModel):
  email: str
  password: str

class Token(BaseModel):
  access_token: str
  token_type: str

# Funciones auxiliares
def verificar_password(password, hashed):
  return pwd_context.verify(password, hashed)

def crear_token(datos: dict, minutos_expira: int = 60):
  datos_a_codificar = datos.copy()
  expire = datetime.utcnow() + timedelta(minutes=minutos_expira)
  datos_a_codificar.update({"exp": expire})
  return jwt.encode(datos_a_codificar, SECRET_KEY, algorithm=ALGORITHM)

def get_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
  credenciales_invalidas = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token inválido o expirado",
    headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email = payload.get("sub")
    if email is None:
      raise credenciales_invalidas
  except JWTError:
    raise credenciales_invalidas

  user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
  if user is None:
    raise credenciales_invalidas
  return user

# Endpoint: registro
@app.post("/registro")
def registrar_usuario(user: RegistroUsuario, db: Session = Depends(get_db)):
  usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == user.email).first()
  if usuario_existente:
    raise HTTPException(status_code=400, detail="Este correo ya está registrado.")
    
  hashed = pwd_context.hash(user.password)
  nuevo = models.Usuario(email=user.email, hashed_password=hashed, oposicion=user.oposicion)
  db.add(nuevo)
  db.commit()
  db.refresh(nuevo)
  return {"id": nuevo.id, "email": nuevo.email}

# Endpoint: login con consulta real a la base de datos
@app.post("/api/login", response_model=Token)
def login(form: LoginForm, db: Session = Depends(get_db)):
  user = db.query(models.Usuario).filter(models.Usuario.email == form.email).first()
  if not user or not verificar_password(form.password, user.hashed_password):
    raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    
  token = crear_token({"sub": user.email})
  return {"access_token": token, "token_type": "bearer"}

# Test
@app.get("/")
def read_root():
  return {"message": "¡Funciona Render con FastAPI!"}

@app.get("/perfil")
def perfil(usuario = Depends(get_usuario_actual)):
  return {
    "email": usuario.email,
    "oposicion": usuario.oposicion
  }

@app.get("/login", response_class=HTMLResponse)
def login_html(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
