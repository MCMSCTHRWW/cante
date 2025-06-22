from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta

app = FastAPI()

# Seguridad
SECRET_KEY = "mcmscthrww"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simulación de DB (Reemplazar por SQLAlchemy)
fake_users_db {
  "test@correo.com":{
    "email": "test@correo.com",
    "hashed_password": pwd_context.hash("1234"),
    "oposicion": "judicatura"
  }
}

class LoginForm(BaseModel):
  email: str
  password: str

class Token(BaseModel):
  access_token: str
  token_type: str

def verificar_password(password, hashed):
  return pwd_context.verify(password, hashed)

def autenticar_usuario(email, password):
  user = fake_users_db.get(email)
  if not user:
    return False
  if not everificar_password(password, user["hashed_password"]):
    return False
  return user

def crear_token(datos: dict, minutos_expira: int = 60):
  datos_a_codificar = datos.copy()
  expire = datetime.utcnow() + timedelta(minutes=minutos_expira)
  datos_a_codificar.update({"exp": expire})
  return jwt.encode(datos_a_codificar, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/login", response_model=Token)
def login(form: LoginForm):
  user = autenticar_usuario(form.email, form.password)
  if not user:
    raise HTTPException(status_code=400, detail="Credenciales incorrectas")
  token = crear_token({"sub": user["email"]})
  return {"access_token": token, "token_type": "bearer"}

@app.get("/")
def read_root():
  return {"message": "!Funciona Render con FastAPI!"}
