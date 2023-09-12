from sqlalchemy import MetaData, Integer, String, Boolean, create_engine, Column
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("postgresql://%(DB_USER)s:%(DB_PASS)s@%(DB_HOST)s:5432/%(DB_NAME)s")
SessionLocal = sessionmaker(engine, expire_on_commit=True)


Base = declarative_base()
metadata = MetaData()


class Todo(Base):
    __tablename__ = "todo"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    completed = Column(Boolean, default=False)


class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    count = Column(Integer, default=0)
