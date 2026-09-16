import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime

# Add backend to path to import models and db setup
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.append(backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv
_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(_root_env):
    load_dotenv(_root_env)

from models import Transcript, Chunk
import tiktoken
from sentence_transformers import SentenceTransformer

# Configure structured JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage()
        }
        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)
        return json.dumps(log_record)

logger = logging.getLogger("ingest")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/dbname")

# Chunking settings
CHUNK_SIZE = 600
CHUNK_OVERLAP = 90 # 15% of 600

def get_db_session():
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal()

def chunk_text(text, tokenizer, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    tokens = tokenizer.encode(text)
    chunks = []
    
    if not tokens:
        return chunks
        
    i = 0
    while i < len(tokens):
        end_idx = min(i + chunk_size, len(tokens))
        chunk_tokens = tokens[i:end_idx]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        
        if end_idx == len(tokens):
            break
        i += chunk_size - overlap
        
    return chunks

def ingest(refresh=False):
    start_time = time.time()
    
    # Init Models and DB
    engine, db = get_db_session()
    
    if refresh:
        logger.info("Refresh flag provided. Dropping tables and re-creating...", extra={"extra_data": {"action": "refresh"}})
        db.query(Chunk).delete()
        db.query(Transcript).delete()
        db.commit()
    
    tokenizer = tiktoken.get_encoding("cl100k_base")
    logger.info("Loading embedding model all-MiniLM-L6-v2...")
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    if not os.path.exists(DATA_DIR):
        logger.error("Data directory not found.", extra={"extra_data": {"path": DATA_DIR}})
        return
        
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    
    total_episodes = 0
    total_chunks = 0
    skipped_episodes = 0
    
    for file in files:
        filepath = os.path.join(DATA_DIR, file)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        url = data.get("url", "")
        title = data.get("title", "")
        
        # Check idempotency
        existing = db.query(Transcript).filter(Transcript.episode_url == url).first()
        if existing:
            skipped_episodes += 1
            logger.info(f"Skipping existing episode: {title}", extra={"extra_data": {"episode_url": url}})
            continue
            
        text = data.get("text", "")
        pub_date_str = data.get("published_at")
        pub_date = None
        if pub_date_str:
            try:
                pub_date = datetime.fromisoformat(pub_date_str)
            except ValueError:
                pass
                
        transcript = Transcript(
            episode_title=title,
            episode_url=url,
            published_at=pub_date
        )
        db.add(transcript)
        db.flush() # get ID
        
        text_chunks = chunk_text(text, tokenizer, CHUNK_SIZE, CHUNK_OVERLAP)
        
        # Batch embed chunks
        if text_chunks:
            embeddings = embed_model.encode(text_chunks)
            
            db_chunks = []
            for i, (chunk_txt, emb) in enumerate(zip(text_chunks, embeddings)):
                chunk = Chunk(
                    transcript_id=transcript.id,
                    content=chunk_txt,
                    chunk_index=i,
                    embedding=emb.tolist()
                )
                db_chunks.append(chunk)
                
            db.add_all(db_chunks)
            total_chunks += len(db_chunks)
            
        db.commit()
        total_episodes += 1
        
    elapsed = time.time() - start_time
    
    # Verification count
    db_transcript_count = db.query(Transcript).count()
    db_chunk_count = db.query(Chunk).count()
    
    logger.info("Ingestion complete.", extra={"extra_data": {
        "processed_episodes": total_episodes,
        "skipped_episodes": skipped_episodes,
        "inserted_chunks": total_chunks,
        "db_total_transcripts": db_transcript_count,
        "db_total_chunks": db_chunk_count,
        "elapsed_seconds": round(elapsed, 2)
    }})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest podcast transcripts.")
    parser.add_argument("--refresh", action="store_true", help="Clear existing data before ingesting")
    args = parser.parse_args()
    
    ingest(refresh=args.refresh)
