# Copilot Instructions: Water Leak Detection System

## Project Overview
This is a scalable water meter leak detection system consisting of:
- **meter_simulator.py**: Simulates real-time water meter readings with leak events (scalable to 50,000+ clients)
- **leak_detector_scalable.py**: Database-backed leak detection engine
- **app.py**: Flask web dashboard for monitoring
- **db.py**: SQLite database layer (can upgrade to PostgreSQL)
- **templates/dashboard.html**: Interactive real-time monitoring interface

## Architecture & Data Flow

```
meter_simulator.py (generates readings for N meters)
        ↓
water_leak_monitoring.db (SQLite, scalable)
        ↓
leak_detector_scalable.py (processes readings, detects leaks)
        ↓ (stores alerts)
water_leak_monitoring.db
        ↓
app.py (Flask server)
        ↓
/api/readings, /api/alerts, /api/meter-stats → dashboard.html
```

**Key Pattern**: Database-backed, stateless leak detection.
- `meter_state` table maintains per-meter session tracking (survives restarts)
- Each meter processed independently with database indices
- Scales to 50,000+ clients via SQLite (or PostgreSQL for production)

## Leak Detection Algorithms
Two independent heuristics trigger alerts:

1. **Continuous Flow Leak** (`CONTINUOUS_FLOW_LEAK`)
   - Detects: Water flowing for ≥24 consecutive hours above MIN_FLOW threshold (0.1L)
   - When delta > 0.1L, increment `continuous_hours` by elapsed time; reset on low-flow readings
   - File: [leak_detector_scalable.py](leak_detector_scalable.py#L30)

2. **Night Flow Leak** (`NIGHT_FLOW_LEAK`)
   - Detects: Anomalous water usage during sleeping hours (02:00-05:00)
   - Accumulates flow during night hours until ≥2.0L total, then alerts
   - File: [leak_detector_scalable.py](leak_detector_scalable.py#L40)

## Critical Implementation Details

### Database Schema (db.py)
- **meter_readings**: All incoming readings (with indices on meter_id, timestamp)
- **leak_alerts**: Detected leaks stored for dashboard
- **meter_state**: Per-meter state (last_volume, last_time, continuous_hours, night_flow)

### State Management
- State persists in database (survives app restarts)
- Load state per meter on each reading via `get_meter_state(meter_id)`
- Update state after processing via `update_meter_state(...)`
- No global memory required—scales to unlimited meters

### Time Handling
- Timestamps are ISO format strings throughout system
- Parsed to `datetime` objects only for calculations
- Hours calculated via `.total_seconds() / 3600`
- Night hours use 24-hour format (NIGHT_START=2, NIGHT_END=5)

### Monitoring Loop
- Background thread calls `get_unprocessed_readings(last_processed_id)`
- Processes readings since last check (avoids duplicates)
- Stores alerts in database if leak detected
- Checks every 2 seconds (configurable)

## Development Workflow

**Initialize database** (one-time):
```bash
python -c "from db import init_db; init_db()"
```

**Run the simulator** (generates readings):
```bash
python meter_simulator.py
```

**Run the dashboard** (monitoring interface):
```bash
python app.py
```
Then visit: http://localhost:5000

**Test detection logic**:
```bash
python -m unittest test_leak_detector -v
```

## Scaling Configuration

### Development (1 meter)
```python
# meter_simulator.py
NUM_METERS = 1
```

### Production (50,000 meters)
```python
# meter_simulator.py
NUM_METERS = 50000
```

### Database Upgrade Path
1. **SQLite** (current): Good for ≤10,000 meters
2. **PostgreSQL**: Production ready, supports 50,000+ meters
3. **Sharding**: Split database by meter_id hash for ultra-scale

See [SCALABILITY.md](SCALABILITY.md) for production setup guide.

## Common Tuning Points
All thresholds in leak_detector_scalable.py:
- `MIN_FLOW`: Delta volume threshold (0.1L)
- `CONTINUOUS_HOURS`: Hours required for continuous leak alert (24)
- `NIGHT_START`/`NIGHT_END`: Sleep window (2-5 AM)
- `NIGHT_THRESHOLD`: Accumulated night flow for alert (2.0L)

## Code Patterns to Follow
1. **State persistence**: Always load from DB first, update DB after
2. **Unprocessed readings**: Use `get_unprocessed_readings(id)` to avoid reprocessing
3. **Delta calculations**: Use `(current - last) / hours` for flow rates
4. **Accumulation logic**: Increment on conditions, reset opposites
5. **Alert storage**: Call `insert_alert()` when leak detected

