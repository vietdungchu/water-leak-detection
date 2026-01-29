import csv
from datetime import datetime

CSV_FILE = "water_meter_readings.csv"

# Thresholds (tune later)
MIN_FLOW = 0.1           # liters
CONTINUOUS_HOURS = 24
NIGHT_START = 2
NIGHT_END = 5
NIGHT_THRESHOLD = 2.0    # liters/hour

# State per meter
meter_state = {}


def is_night(hour):
    return NIGHT_START <= hour <= NIGHT_END


def process_reading(meter_id, timestamp, volume):
    """Process one meter reading and detect leak."""
    if meter_id not in meter_state:
        meter_state[meter_id] = {
            "last_volume": volume,
            "last_time": timestamp,
            "continuous_hours": 0,
            "night_flow": 0.0
        }
        return None

    state = meter_state[meter_id]

    delta = volume - state["last_volume"]
    hours = (timestamp - state["last_time"]).total_seconds() / 3600

    # Continuous flow detection
    if delta > MIN_FLOW:
        state["continuous_hours"] += hours
    else:
        state["continuous_hours"] = 0

    # Night flow detection
    if is_night(timestamp.hour):
        state["night_flow"] += delta

    # Update state
    state["last_volume"] = volume
    state["last_time"] = timestamp

    # Leak decision
    if state["continuous_hours"] >= CONTINUOUS_HOURS:
        return "CONTINUOUS_FLOW_LEAK"

    if state["night_flow"] >= NIGHT_THRESHOLD:
        return "NIGHT_FLOW_LEAK"

    return None


def main():
    print("Starting leak detector...")

    with open(CSV_FILE, newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            meter_id = row["meter_id"]
            timestamp = datetime.fromisoformat(row["timestamp"])
            volume = float(row["volume_liters"])

            leak = process_reading(meter_id, timestamp, volume)

            if leak:
                print(f"🚨 Leak detected | Meter: {meter_id} | Type: {leak}")


if __name__ == "__main__":
    main()
