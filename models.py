from sqlalchemy import Column, Integer, String
from database import Base

class Usuario(Base):
  __tablename__ = "usuarios"
  id = Column(Integer, primary_key=True, index=True)
  nombre = Column(String, nullable=False)
  email = Column(String, unique=True, index=True, nullable=False)
  hashed_password = Column(String, nullable=False)
  oposicion = Column(String, nullable=True)
