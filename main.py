from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from database import Base, engine, SessionLocal
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
import models

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

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

# Modelos de entrada
class RegistroUsuario(BaseModel):
  nombre: str
  email: str
  password: str
  oposicion: str

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

def insertar_temas_iniciales(db: Session):
  temas = [
    "La Constitución española de 1978: características y estructura. Derechos fundamentales y libertades públicas. La reforma constitucional.",
    "Políticas Sociales Públicas: los derechos de las personas con discapacidad; protección a los colectivos más desfavorecidos; la dependencia. Las políticas de igualdad y no discriminación. La lucha contra la violencia de género.",
    "La Hacienda Pública en la Constitución española. Los principios constitucionales del derecho financiero. Los derechos y garantías de los obligados tributarios. La financiación de las Haciendas territoriales.",
    "Las Cortes Generales: composición y funciones. Órganos parlamentarios. El procedimiento legislativo ordinario. La Corona. El Rey. El Defensor del Pueblo.",
    "El Gobierno: composición y funciones. El Consejo de Ministros y las Comisiones Delegadas del Gobierno.",
    "El Poder Judicial: funciones. El gobierno del Poder Judicial. El Ministerio Fiscal. El Tribunal Constitucional.",
    "La organización territorial del Estado: Comunidades y Ciudades Autónomas. Las Entidades Locales. Los Estatutos de Autonomía. Distribución de competencias.",
    "Las Instituciones de la Unión Europea: el Parlamento Europeo, el Consejo Europeo, la Comisión, el Tribunal de Justicia, el BCE y el Tribunal de Cuentas.",
    "El mercado interior: la libre circulación de mercancías, personas, servicios y capitales. Política agrícola y pesquera común. Política exterior y de seguridad común. El euro.",
    "El Derecho de la Unión Europea. Las fuentes del ordenamiento de la UE y su aplicación. Relación con los estados miembros."
  ]
  for nombre in temas:
    existe = db.query(Tema).filter_by(nombre=nombre, oposicion="Inspección de Hacienda", ejercicio=4).first()
    if not existe:
      db.add(Tema(nombre=nombre, oposicion="Inspección de Hacienda", ejercicio=4))
  db.commit()

with SessionLocal() as db:
  insertar_temas_iniciales(db)

@app.post("/registro")
def registrar_usuario(user: RegistroUsuario, db: Session = Depends(get_db)):
  usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == user.email).first()
  if usuario_existente:
    raise HTTPException(status_code=400, detail="Este correo ya está registrado.")
    
  hashed = pwd_context.hash(user.password)
  nuevo = models.Usuario(
    nombre=user.nombre,
    email=user.email,
    hashed_password=hashed,
    oposicion=user.oposicion
  )
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

@app.get("/perfil")
def perfil(usuario = Depends(get_usuario_actual)):
  return {
    "nombre": usuario.nombre,
    "email": usuario.email,
    "oposicion": usuario.oposicion
  }

@app.get("/login", response_class=HTMLResponse)
def login_html(request: Request):
  return templates.TemplateResponse("login.html", {"request": request})

@app.get("/registro", response_class=HTMLResponse)
def registro_html(request: Request):
  return templates.TemplateResponse("registro.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
  return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})
