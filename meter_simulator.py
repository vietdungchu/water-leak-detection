import csv
import time
import random
from datetime import datetime

# CSV file name
CSV_FILE = "water_meter_readings.csv"

# Meter configuration
METER_ID = "MTR-001"
INITIAL_VOLUME = 10000.0  # liters
INTERVAL_SECONDS = 5      # time between readings

# Leak simulation
LEAK_PROBABILITY = 0.05   # 5% chance to simulate a leak


def simulate_water_consumption(is_leak=False):
    """
    Simulate water consumption in liters.
    Normal usage: small random value
    Leak usage: higher constant value
    """
    if is_leak:
        return random.uniform(5.0, 10.0)  # leak flow
    else:
        return random.uniform(0.0, 1.5)   # normal usage


def write_csv_header():
    """Create CSV file with header if it does not exist."""
    try:
        with open(CSV_FILE, mode="x", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["meter_id", "timestamp", "volume_liters"])
    except FileExistsError:
        pass  # File already exists


def append_reading(meter_id, timestamp, volume):
    """Append one meter reading to CSV."""
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([meter_id, timestamp, volume])


def main():
    print("Starting water meter simulator...")
    write_csv_header()

    current_volume = INITIAL_VOLUME

    while True:
        timestamp = datetime.utcnow().isoformat()

        # Randomly decide if there is a leak
        is_leak = random.random() < LEAK_PROBABILITY

        consumption = simulate_water_consumption(is_leak)
        current_volume += consumption

        append_reading(METER_ID, timestamp, round(current_volume, 2))

        status = "LEAK" if is_leak else "NORMAL"
        print(f"[{timestamp}] {status} | +{consumption:.2f} L | Total: {current_volume:.2f} L")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
