# Copilot Instructions: Water Leak Detection System

## Project Overview
This is a water meter leak detection system consisting of:
- **meter_simulator.py**: Simulates real-time water meter readings with occasional leak events
- **leak_detector.py**: Analyzes meter readings to identify leak patterns
- **water_meter_readings.csv**: Data pipeline connecting both components

## Architecture & Data Flow
```
meter_simulator.py (generates readings)
        ↓
water_meter_readings.csv (persists data)
        ↓
leak_detector.py (analyzes & alerts)
```

**Key Pattern**: Stateful leak detection using per-meter session tracking.
- `meter_state` dictionary maintains continuous tracking across readings (last volume, timestamp, accumulated hours/flow)
- Each meter is processed independently, enabling multi-meter scenarios

## Leak Detection Algorithms
Two independent heuristics trigger alerts:

1. **Continuous Flow Leak** (`CONTINUOUS_FLOW_LEAK`)
   - Detects: Water flowing for ≥24 consecutive hours above MIN_FLOW threshold (0.1L)
   - When delta > 0.1L, increment `continuous_hours` by elapsed time; reset on low-flow readings
   - File: [leak_detector.py](leak_detector.py#L48)

2. **Night Flow Leak** (`NIGHT_FLOW_LEAK`)
   - Detects: Anomalous water usage during sleeping hours (02:00-05:00)
   - Accumulates flow during night hours until ≥2.0L total, then alerts
   - File: [leak_detector.py](leak_detector.py#L51)

## Critical Implementation Details

### State Management
- State persists across all readings for a meter (global `meter_state` dict)
- First reading for a meter initializes state; subsequent readings update delta calculations
- No explicit reset mechanism—state survives for session lifetime

### Time Handling
- Timestamps are ISO format strings, parsed to `datetime` objects for comparison
- Hours calculated via `.total_seconds() / 3600` from datetime deltas
- Night hours use 24-hour format (NIGHT_START=2, NIGHT_END=5)

### CSV Integration
- Input: meter_id, timestamp (ISO), volume_liters (float)
- Simulator runs indefinitely, appending readings every 5 seconds
- Detector processes sequentially; alerts print to stdout

## Development Workflow

**Run the simulator** (generates data continuously):
```bash
python meter_simulator.py
```

**Run the detector** (processes existing CSV):
```bash
python leak_detector.py
```

**Test scenario**: Run both in parallel—simulator generates readings while detector analyzes them in real-time.

## Common Tuning Points
All thresholds are module-level constants in leak_detector.py:
- `MIN_FLOW`: Delta volume threshold (0.1L)
- `CONTINUOUS_HOURS`: Hours required for continuous leak alert (24)
- `NIGHT_HOURS`: Sleep window (2-5 AM)
- `NIGHT_THRESHOLD`: Accumulated night flow for alert (2.0L)

## Code Patterns to Follow
1. **State initialization**: Check if meter_id in state; if not, create initial dict and return early
2. **Delta calculations**: Always use `(current - last) / hours` for flow rates
3. **Accumulation logic**: Increment counters on conditions, reset on opposite conditions
4. **Alert format**: Return leak type string or None (no alert)

