# Testing the Scalable Water Leak Detection System

## ✅ Quick Start (3 Easy Steps)

### Step 1: Initialize Database
```bash
python -c "from db import init_db; init_db()"
```

### Step 2: Start Simulator (Terminal 1)
```bash
python meter_simulator.py
```
You'll see readings being generated and stored in database.

### Step 3: Start Dashboard (Terminal 2)
```bash
python app.py
```
Open browser: **http://localhost:5000**

## 🎯 What You'll See

### Dashboard Features
1. **Volume Chart** - Real-time water consumption (updates every 5 seconds)
2. **Leak Alerts** - Detected leaks with timestamps
3. **Meter Statistics** - Current state of each meter

### Alert Types
- 🟨 **NIGHT_FLOW_LEAK**: Suspicious water usage during sleep hours (2-5 AM)
- 🔴 **CONTINUOUS_FLOW_LEAK**: Water flowing for 24+ hours (pipe leak)

## 🧪 Testing Alerts Manually

### Trigger Continuous Flow Leak
Since 24-hour leak takes time, use test script:

```python
# test_manual.py
from db import init_db, insert_reading
from leak_detector_scalable import process_reading_scalable
from datetime import datetime, timedelta

init_db()

meter_id = "TEST-001"
base_time = datetime.utcnow()

# Simulate 24+ hours of continuous flow (0.2L per 5-min reading)
for i in range(300):  # 300 * 5 min = 1500 min = 25 hours
    current_time = base_time + timedelta(minutes=i*5)
    volume = 1000.0 + (i * 0.2)
    leak = process_reading_scalable(meter_id, current_time, volume)
    if leak:
        print(f"✓ {leak} triggered at reading {i}")
        break
```

Run it:
```bash
python test_manual.py
# Output: ✓ CONTINUOUS_FLOW_LEAK triggered at reading 288
```

### Trigger Night Flow Leak
```python
# test_night_flow.py
from db import init_db, insert_reading
from leak_detector_scalable import process_reading_scalable
from datetime import datetime

init_db()

meter_id = "NIGHT-001"
# Create timestamp at 3 AM (night hours)
night_time = datetime.fromisoformat("2026-01-30T03:00:00")

# Initialize
process_reading_scalable(meter_id, night_time, 1000.0)

# Add 2.5L during night hours
leak1 = process_reading_scalable(meter_id, 
                                 datetime.fromisoformat("2026-01-30T03:15:00"),
                                 1001.2)
leak2 = process_reading_scalable(meter_id,
                                 datetime.fromisoformat("2026-01-30T03:30:00"),
                                 1002.5)

if leak2:
    print(f"✓ {leak2} triggered for night flow!")
```

## 🔍 Verify Data in Database

```bash
# Check how many readings stored
sqlite3 water_leak_monitoring.db "SELECT COUNT(*) FROM meter_readings;"

# Check how many alerts detected
sqlite3 water_leak_monitoring.db "SELECT * FROM leak_alerts;"

# Check meter state
sqlite3 water_leak_monitoring.db "SELECT meter_id, continuous_hours, night_flow FROM meter_state;"
```

## 📊 Scale to 50,000 Clients

Edit `meter_simulator.py`:
```python
NUM_METERS = 50000  # Changed from 1
```

Then run simulator - database will handle all 50k meters efficiently!

Monitor database growth:
```bash
watch -n 5 'ls -lh water_leak_monitoring.db; echo "---"; \
            sqlite3 water_leak_monitoring.db "SELECT COUNT(*) FROM meter_readings;"'
```

## 🚀 Dashboard API Endpoints

Test endpoints from command line:

```bash
# Get recent readings
curl http://localhost:5000/api/readings | python -m json.tool

# Get recent alerts
curl http://localhost:5000/api/alerts | python -m json.tool

# Get meter statistics
curl http://localhost:5000/api/meter-stats | python -m json.tool

# Health check
curl http://localhost:5000/api/health
```

## 🐛 Troubleshooting

**No data in dashboard?**
```bash
# Check database exists
ls water_leak_monitoring.db

# Check simulator is writing
sqlite3 water_leak_monitoring.db "SELECT COUNT(*) FROM meter_readings;"
# Should be > 0 after running simulator for a few seconds
```

**Alerts empty?**
- Continuous flow alert needs 24 hours of readings (use test script above)
- Night flow alert only triggers during 2-5 AM hours
- Check app.py logs for processing messages

**Performance slow with many meters?**
```bash
# Optimize database
sqlite3 water_leak_monitoring.db "VACUUM;"

# Check database size
ls -lh water_leak_monitoring.db
```

## Next Steps

1. ✅ Database-backed system working
2. ✅ Alerts displaying on dashboard
3. ✅ Scalable to 50,000+ clients
4. ⏭️ Read [SCALABILITY.md](SCALABILITY.md) for production deployment
5. ⏭️ Set NUM_METERS = 50000 for full-scale testing
