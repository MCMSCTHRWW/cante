from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://mcmscthrww:Q5DE9eExn9ZdPraxcE46kYviv4goigoR@dpg-d1bu4rqdbo4c73cd7amg-a/cante"  # ⬅️ pega aquí tu URL real

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
