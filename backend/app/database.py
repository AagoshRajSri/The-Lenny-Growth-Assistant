import os
import time
import uuid
import json
import logging
import httpx
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load root and local .env files
_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
if os.path.exists(_root_env):
    load_dotenv(_root_env)
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session as DBSession

# Lazy-import models so we can still start even without DB
def _get_db_session():
    url = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/dbname")
    engine = create_engine(url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/dbname")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
