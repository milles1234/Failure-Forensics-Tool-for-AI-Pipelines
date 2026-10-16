# tracing/storage.py
import json
import os
import sqlite3
from schemas import Trace

TRACE_DIR = "data/traces"
DB_PATH = "data/traces.db"
os.makedirs(TRACE_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traces (
            trace_id TEXT PRIMARY KEY,
            timestamp TEXT,
            status TEXT,
            final_score INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save_trace(trace: Trace):
    """Saves the completed trace to a JSON file."""
    file_path = os.path.join(TRACE_DIR, f"{trace.trace_id}.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        # Use Pydantic's model_dump_json for clean serialization
        f.write(trace.model_dump_json(indent=4))
    
    print(f"✅ Trace saved: {file_path}")