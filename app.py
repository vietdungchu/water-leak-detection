"""
Flask web application for water leak detection monitoring dashboard.
Displays real-time graphs and leak alerts.
"""

from flask import Flask, render_template, jsonify
import csv
import json
from datetime import datetime, timedelta
from leak_detector import process_reading, meter_state
import threading
import time

app = Flask(__name__)

# Global data storage
readings_data = {}
alerts_data = []

CSV_FILE = "water_meter_readings.csv"


def load_recent_readings(hours=2):
    """Load recent readings from CSV for the last N hours."""
    recent_time = datetime.utcnow() - timedelta(hours=hours)
    data_by_meter = {}

    try:
        with open(CSV_FILE, newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                meter_id = row["meter_id"]
                timestamp = datetime.fromisoformat(row["timestamp"])
                volume = float(row["volume_liters"])

                # Only include recent readings
                if timestamp >= recent_time:
                    if meter_id not in data_by_meter:
                        data_by_meter[meter_id] = {"timestamps": [], "volumes": []}

                    data_by_meter[meter_id]["timestamps"].append(
                        timestamp.strftime("%H:%M:%S")
                    )
                    data_by_meter[meter_id]["volumes"].append(volume)

    except FileNotFoundError:
        pass

    return data_by_meter


def monitor_readings():
    """Background thread to continuously monitor readings and detect leaks."""
    while True:
        try:
            with open(CSV_FILE, newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    meter_id = row["meter_id"]
                    timestamp = datetime.fromisoformat(row["timestamp"])
                    volume = float(row["volume_liters"])

                    # Process reading for leak detection
                    leak = process_reading(meter_id, timestamp, volume)

                    if leak:
                        alert = {
                            "meter_id": meter_id,
                            "type": leak,
                            "timestamp": timestamp.isoformat(),
                            "volume": volume
                        }
                        alerts_data.append(alert)
                        print(
                            f"🚨 ALERT: {leak} detected on meter {meter_id}"
                        )

            time.sleep(5)  # Check every 5 seconds

        except Exception as e:
            print(f"Error in monitoring thread: {e}")
            time.sleep(5)


@app.route("/")
def dashboard():
    """Render main dashboard."""
    return render_template("dashboard.html")


@app.route("/api/readings")
def get_readings():
    """Return recent readings as JSON."""
    readings = load_recent_readings(hours=2)
    return jsonify(readings)


@app.route("/api/alerts")
def get_alerts():
    """Return recent alerts."""
    # Keep only last 50 alerts
    recent_alerts = alerts_data[-50:] if alerts_data else []
    return jsonify(recent_alerts)


@app.route("/api/meter-stats")
def get_meter_stats():
    """Return current meter statistics."""
    stats = {}
    for meter_id, state in meter_state.items():
        stats[meter_id] = {
            "last_volume": state["last_volume"],
            "continuous_hours": round(state["continuous_hours"], 2),
            "night_flow": round(state["night_flow"], 2),
            "last_update": state["last_time"].isoformat() if hasattr(
                state["last_time"], "isoformat"
            ) else str(state["last_time"])
        }
    return jsonify(stats)


if __name__ == "__main__":
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_readings, daemon=True)
    monitor_thread.start()

    # Run Flask app
    app.run(debug=True, port=5000, use_reloader=False)
