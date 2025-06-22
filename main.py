from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from database import Base, engine, SessionLocal
import models
from sqlalchemy.orm import Session

app = FastAPI()

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
@app.post("/login", response_model=Token)
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
