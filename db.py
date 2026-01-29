"""
Database models for water leak detection system.
Supports scalable monitoring for multiple clients.
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager
import os

DB_FILE = "water_leak_monitoring.db"


@contextmanager
def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database schema."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Meter readings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meter_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meter_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                volume_liters REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(meter_id, timestamp)
            )
        """)
        
        # Leak alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leak_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meter_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                volume_liters REAL NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Meter state table (for stateful tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meter_state (
                meter_id TEXT PRIMARY KEY,
                last_volume REAL,
                last_time TEXT,
                continuous_hours REAL DEFAULT 0,
                night_flow REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meter_readings_meter_id ON meter_readings(meter_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meter_readings_timestamp ON meter_readings(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leak_alerts_meter_id ON leak_alerts(meter_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leak_alerts_timestamp ON leak_alerts(timestamp)")
        
        conn.commit()


def insert_reading(meter_id, timestamp, volume):
    """Insert meter reading into database."""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO meter_readings (meter_id, timestamp, volume_liters)
                VALUES (?, ?, ?)
            """, (meter_id, timestamp, volume))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Duplicate reading
            return False


def insert_alert(meter_id, alert_type, volume, timestamp):
    """Insert leak alert into database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO leak_alerts (meter_id, alert_type, volume_liters, timestamp)
            VALUES (?, ?, ?, ?)
        """, (meter_id, alert_type, volume, timestamp))
        conn.commit()


def get_recent_readings(hours=2, limit=1000):
    """Get recent meter readings for visualization."""
    from datetime import timedelta
    recent_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT meter_id, timestamp, volume_liters
            FROM meter_readings
            WHERE timestamp > ?
            ORDER BY meter_id, timestamp DESC
            LIMIT ?
        """, (recent_time, limit))
        
        rows = cursor.fetchall()
        data_by_meter = {}
        
        for row in rows:
            meter_id = row['meter_id']
            if meter_id not in data_by_meter:
                data_by_meter[meter_id] = {"timestamps": [], "volumes": []}
            
            data_by_meter[meter_id]["timestamps"].insert(
                0, 
                datetime.fromisoformat(row['timestamp']).strftime("%H:%M:%S")
            )
            data_by_meter[meter_id]["volumes"].insert(0, row['volume_liters'])
        
        return data_by_meter


def get_recent_alerts(limit=50):
    """Get recent leak alerts."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT meter_id, alert_type, volume_liters, timestamp
            FROM leak_alerts
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]


def get_meter_state(meter_id):
    """Get meter state from database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM meter_state WHERE meter_id = ?
        """, (meter_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def update_meter_state(meter_id, last_volume, last_time, continuous_hours, night_flow):
    """Update meter state in database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO meter_state 
            (meter_id, last_volume, last_time, continuous_hours, night_flow, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (meter_id, last_volume, last_time, continuous_hours, night_flow))
        conn.commit()


def get_all_meter_stats():
    """Get statistics for all meters."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT meter_id, last_volume, last_time, continuous_hours, night_flow, updated_at
            FROM meter_state
            ORDER BY meter_id
        """)
        
        return {row['meter_id']: dict(row) for row in cursor.fetchall()}


def get_unprocessed_readings(last_processed_id=0):
    """Get readings that haven't been processed for leak detection yet."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, meter_id, timestamp, volume_liters
            FROM meter_readings
            WHERE id > ?
            ORDER BY id ASC
        """, (last_processed_id,))
        
        return [dict(row) for row in cursor.fetchall()]


def cleanup_old_readings(days=7):
    """Delete old readings to maintain database size."""
    from datetime import timedelta
    cutoff_time = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM meter_readings WHERE timestamp < ?
        """, (cutoff_time,))
        conn.commit()
        return cursor.rowcount
