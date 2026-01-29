"""
Scalable leak detection engine for 50,000+ clients.
Uses database-backed state tracking instead of global variables.
"""

from datetime import datetime
from db import (
    get_meter_state, update_meter_state, insert_alert,
    get_unprocessed_readings
)

# Thresholds
MIN_FLOW = 0.1
CONTINUOUS_HOURS = 24
NIGHT_START = 2
NIGHT_END = 5
NIGHT_THRESHOLD = 2.0

# Track processed readings to avoid reprocessing
last_processed_id = 0


def is_night(hour):
    """Check if hour is during night window (2-5 AM)."""
    return NIGHT_START <= hour <= NIGHT_END


def process_reading_scalable(meter_id, timestamp, volume):
    """
    Process meter reading with database-backed state.
    Returns leak type or None.
    """
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    
    # Load current state from database
    state = get_meter_state(meter_id)
    
    if state is None:
        # First reading for this meter - initialize
        update_meter_state(meter_id, volume, timestamp.isoformat(), 0, 0)
        return None
    
    # Parse last_time from database
    last_time = datetime.fromisoformat(state['last_time'])
    last_volume = state['last_volume']
    continuous_hours = state['continuous_hours']
    night_flow = state['night_flow']
    
    # Calculate delta
    delta = volume - last_volume
    hours = (timestamp - last_time).total_seconds() / 3600
    
    # Continuous flow detection
    if delta > MIN_FLOW:
        continuous_hours += hours
    else:
        continuous_hours = 0
    
    # Night flow detection
    if is_night(timestamp.hour):
        night_flow += delta
    else:
        # Reset night flow when it's not night hours
        night_flow = 0
    
    # Update state in database
    update_meter_state(meter_id, volume, timestamp.isoformat(), continuous_hours, night_flow)
    
    # Check for leaks
    leak_type = None
    if continuous_hours >= CONTINUOUS_HOURS:
        leak_type = "CONTINUOUS_FLOW_LEAK"
    elif night_flow >= NIGHT_THRESHOLD:
        leak_type = "NIGHT_FLOW_LEAK"
    
    # Store alert if detected
    if leak_type:
        insert_alert(meter_id, leak_type, volume, timestamp.isoformat())
    
    return leak_type


def process_batch_readings(readings):
    """
    Process multiple readings efficiently.
    Useful for batch imports or syncing from CSV.
    """
    alerts = []
    for reading in readings:
        leak = process_reading_scalable(
            reading['meter_id'],
            reading['timestamp'],
            reading['volume_liters']
        )
        if leak:
            alerts.append({
                'meter_id': reading['meter_id'],
                'type': leak,
                'timestamp': reading['timestamp'],
                'volume': reading['volume_liters']
            })
    return alerts


def sync_from_csv(csv_file):
    """
    Sync readings from CSV file to database.
    Used during migration from CSV-only setup.
    """
    import csv
    from db import insert_reading
    
    synced = 0
    try:
        with open(csv_file, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                meter_id = row['meter_id']
                timestamp = row['timestamp']
                volume = float(row['volume_liters'])
                
                if insert_reading(meter_id, timestamp, volume):
                    synced += 1
    except FileNotFoundError:
        pass
    
    return synced
