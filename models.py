from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    oposicion = Column(String, nullable=True)

class Tema(Base):
    __tablename__ = "temas"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, nullable=False)
    nombre = Column(String, nullable=False)
    oposicion = Column(String, nullable=False)
    ejercicio = Column(Integer, nullable=False)

class Cante(Base):
    __tablename__ = "cantes"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    tema = Column(String, nullable=False)
    duracion = Column(Integer, nullable=False)
    evaluacion = Column(String, nullable=True)  # bueno, regular, malo
    fecha = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", backref="cantes")
