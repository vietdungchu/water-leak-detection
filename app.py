"""
Flask web application for water leak detection monitoring dashboard.
Scalable for 50,000+ clients using SQLite database.
"""

from flask import Flask, render_template, jsonify
from db import (
    init_db, insert_reading, get_recent_readings, get_recent_alerts,
    get_all_meter_stats, get_unprocessed_readings, cleanup_old_readings
)
from leak_detector_scalable import process_reading_scalable, sync_from_csv
from datetime import datetime
import threading
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Track last processed reading for efficiency
last_processed_id = 0


def monitor_new_readings():
    """Background thread to monitor new readings and detect leaks."""
    global last_processed_id
    
    while True:
        try:
            # Get unprocessed readings from database
            readings = get_unprocessed_readings(last_processed_id)
            
            if readings:
                logger.info(f"Processing {len(readings)} new readings...")
                
                for reading in readings:
                    leak = process_reading_scalable(
                        reading['meter_id'],
                        reading['timestamp'],
                        reading['volume_liters']
                    )
                    
                    if leak:
                        logger.warning(
                            f"🚨 ALERT: {leak} on meter {reading['meter_id']}"
                        )
                    
                    last_processed_id = reading['id']
            
            time.sleep(2)  # Check every 2 seconds
            
            # Cleanup old data weekly
            if int(time.time()) % (7 * 24 * 3600) == 0:
                deleted = cleanup_old_readings(days=7)
                logger.info(f"Cleaned up {deleted} old readings")
                
        except Exception as e:
            logger.error(f"Error in monitoring thread: {e}")
            time.sleep(5)


@app.route("/")
def dashboard():
    """Render main dashboard."""
    return render_template("dashboard.html")


@app.route("/api/readings")
def get_readings():
    """Return recent readings as JSON."""
    try:
        readings = get_recent_readings(hours=2)
        return jsonify(readings)
    except Exception as e:
        logger.error(f"Error getting readings: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/alerts")
def get_alerts():
    """Return recent alerts."""
    try:
        alerts = get_recent_alerts(limit=50)
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/meter-stats")
def get_meter_stats():
    """Return meter statistics."""
    try:
        stats = get_all_meter_stats()
        
        # Format for JSON
        formatted_stats = {}
        for meter_id, stat in stats.items():
            formatted_stats[meter_id] = {
                "last_volume": stat.get('last_volume', 0),
                "continuous_hours": round(stat.get('continuous_hours', 0), 2),
                "night_flow": round(stat.get('night_flow', 0), 2),
                "last_update": stat.get('updated_at', 'N/A')
            }
        
        return jsonify(formatted_stats)
    except Exception as e:
        logger.error(f"Error getting meter stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "last_processed_id": last_processed_id,
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/api/sync-csv")
def sync_csv():
    """Sync CSV data to database (one-time operation)."""
    try:
        synced = sync_from_csv("water_meter_readings.csv")
        logger.info(f"Synced {synced} readings from CSV")
        return jsonify({"synced": synced})
    except Exception as e:
        logger.error(f"Error syncing CSV: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logger.info("Initializing database...")
    init_db()
    
    # Sync existing CSV data on startup (if any)
    logger.info("Syncing CSV data if present...")
    synced = sync_from_csv("water_meter_readings.csv")
    if synced > 0:
        logger.info(f"Synced {synced} readings from CSV")
    
    logger.info("Starting monitoring thread...")
    monitor_thread = threading.Thread(target=monitor_new_readings, daemon=True)
    monitor_thread.start()

    logger.info("Starting Flask app on http://localhost:5000")
    app.run(debug=True, port=5000, use_reloader=False)
