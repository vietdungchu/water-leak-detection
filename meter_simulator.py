import time
import random
from datetime import datetime
from db import init_db, insert_reading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
INTERVAL_SECONDS = 5
LEAK_PROBABILITY = 0.05
NUM_METERS = 1  # Start with 1, can scale to 50000

# Meter configurations
meters = {}


def init_meters(num_meters=1):
    """Initialize meter states."""
    for i in range(num_meters):
        meter_id = f"MTR-{i+1:06d}"
        meters[meter_id] = {
            "volume": 10000.0 + (i * 100),  # Slightly different initial volumes
            "is_leaking": False,
            "leak_duration": 0
        }


def simulate_water_consumption(meter_id, is_leak=False):
    """Simulate water consumption in liters."""
    if is_leak:
        return random.uniform(5.0, 10.0)  # leak flow
    else:
        return random.uniform(0.0, 1.5)   # normal usage


def main():
    logger.info("Initializing database...")
    init_db()
    
    logger.info(f"Initializing {NUM_METERS} meter(s)...")
    init_meters(NUM_METERS)
    
    logger.info("Starting water meter simulator...")
    reading_count = 0
    
    try:
        while True:
            timestamp = datetime.utcnow().isoformat()
            
            for meter_id, state in meters.items():
                # Randomly decide if there is a leak
                is_leak = random.random() < LEAK_PROBABILITY
                
                if is_leak:
                    state["is_leaking"] = True
                    state["leak_duration"] += INTERVAL_SECONDS
                else:
                    state["is_leaking"] = False
                    state["leak_duration"] = 0
                
                consumption = simulate_water_consumption(meter_id, is_leak)
                state["volume"] += consumption
                
                # Insert reading into database
                insert_reading(meter_id, timestamp, round(state["volume"], 2))
                reading_count += 1
                
                status = "LEAK" if is_leak else "NORMAL"
                if reading_count % 10 == 0:  # Log every 10 readings
                    logger.info(
                        f"[{timestamp}] {meter_id} {status} | "
                        f"+{consumption:.2f}L | Total: {state['volume']:.2f}L"
                    )
            
            time.sleep(INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        logger.info(f"Simulator stopped. Generated {reading_count} readings.")


if __name__ == "__main__":
    main()
