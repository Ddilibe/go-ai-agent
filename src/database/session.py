#!/usr/bin/env python3
from decouple import config
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = str(
    config(
        "DB_URL",
        cast=str,
    )
    if config("DEBUG") == "True"
    else ""
)
engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
