from sqlmodel import SQLModel
from app.db import engine

SQLModel.metadata.drop_all(engine)
print("Database tables dropped successfully.")
