# Water Leak Detection System - Quick Start Guide

## Features
- 📊 **Real-time Consumption Graph** - Visualize water volume over 2-hour window
- 🚨 **Live Alert Feed** - Monitor detected leaks as they occur
- 📈 **Meter Statistics** - Track continuous flow hours and night flow accumulation
- 🎯 **Multi-meter Support** - Monitor multiple meters independently

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the System

### Option 1: Simulator + Detector + Dashboard (Recommended)
Open 3 terminals:

**Terminal 1 - Start the Simulator** (generates water readings):
```bash
python meter_simulator.py
```

**Terminal 2 - Start the Web Dashboard** (monitoring interface):
```bash
python app.py
```
Then open browser to: **http://localhost:5000**

**Terminal 3 - Run Tests** (optional, to verify detection logic):
```bash
python -m unittest test_leak_detector -v
```

### Option 2: Detector Only (with existing CSV data)
```bash
python leak_detector.py
```

## Dashboard Features

### 📊 Volume Consumption Chart
- Displays water usage over last 2 hours
- Real-time updates every 5 seconds
- Shows consumption patterns and anomalies

### 🚨 Recent Alerts
- Lists detected leaks in real-time
- Shows meter ID, alert type, volume, and timestamp
- Color-coded by severity (yellow: night flow, red: continuous flow)

### 📈 Meter Statistics
- **Current Volume**: Total water consumed
- **Continuous Flow Hours**: Hours of flow above 0.1L threshold
- **Night Flow Accumulated**: Water usage during 2-5 AM
- **Last Update**: Timestamp of last reading

## Alert Types

1. **CONTINUOUS_FLOW_LEAK** ⚠️
   - Triggers when water flows for ≥24 consecutive hours
   - Indicates possible water leak in pipes
   - Status color: RED (critical)

2. **NIGHT_FLOW_LEAK** ⚠️
   - Triggers when ≥2.0L accumulates during sleep hours (2-5 AM)
   - Indicates anomalous usage
   - Status color: YELLOW (warning)

## Configuration

Edit thresholds in `leak_detector.py`:
```python
MIN_FLOW = 0.1           # Minimum liters to count as flow
CONTINUOUS_HOURS = 24    # Hours required for continuous leak alert
NIGHT_START = 2          # Night window start (2 AM)
NIGHT_END = 5            # Night window end (5 AM)
NIGHT_THRESHOLD = 2.0    # Liters for night flow alert
```

## Troubleshooting

**Dashboard shows no data?**
- Ensure `meter_simulator.py` is running
- Check that `water_meter_readings.csv` exists in project folder

**No alerts appearing?**
- Simulator needs 24+ hours of continuous reading for continuous flow alert
- For night flow, ensure readings occur during 2-5 AM
- Check detector logs in Terminal 3

**Port 5000 already in use?**
Edit `app.py` line 98:
```python
app.run(debug=True, port=5001, use_reloader=False)  # Change to 5001
```

## Architecture
```
meter_simulator.py
       ↓
water_meter_readings.csv ← app.py (reads)
       ↓
leak_detector.py → alerts_data → /api/alerts → dashboard.html
```

## Testing

Run automated tests to verify leak detection logic:
```bash
python -m unittest test_leak_detector -v
```

Tests cover:
- State initialization
- Continuous flow detection
- Night flow accumulation
- Multi-meter independence
- Edge cases (zero flow, flow resets)
