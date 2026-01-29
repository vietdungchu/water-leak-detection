import unittest
from datetime import datetime, timedelta
from leak_detector import process_reading, meter_state, is_night


class TestLeakDetector(unittest.TestCase):
    """Test suite for water leak detection system."""

    def setUp(self):
        """Clear meter state before each test."""
        meter_state.clear()

    def test_initial_reading_no_alert(self):
        """First reading should initialize state without alert."""
        result = process_reading(
            "MTR-001",
            datetime.fromisoformat("2026-01-29T12:00:00"),
            100.0
        )
        self.assertIsNone(result)
        self.assertIn("MTR-001", meter_state)
        self.assertEqual(meter_state["MTR-001"]["last_volume"], 100.0)

    def test_is_night_function(self):
        """Test night hours detection (2-5 AM)."""
        self.assertTrue(is_night(2))
        self.assertTrue(is_night(3))
        self.assertTrue(is_night(4))
        self.assertTrue(is_night(5))
        self.assertFalse(is_night(1))
        self.assertFalse(is_night(6))
        self.assertFalse(is_night(12))

    def test_continuous_flow_leak_detection(self):
        """Test continuous flow leak detection (24+ hours of flow)."""
        meter_id = "MTR-002"
        base_time = datetime.fromisoformat("2026-01-29T12:00:00")

        # Initialize
        process_reading(meter_id, base_time, 100.0)

        # Simulate 24 hours of continuous flow (delta > 0.1L per reading)
        for i in range(1, 25):
            current_time = base_time + timedelta(hours=i)
            result = process_reading(meter_id, current_time, 100.0 + (i * 0.2))
            
            # Alert should trigger after 24 hours
            if i < 24:
                self.assertIsNone(result, f"Hour {i}: should not alert yet")
            else:
                self.assertEqual(result, "CONTINUOUS_FLOW_LEAK")

    def test_continuous_flow_reset_on_low_flow(self):
        """Test that continuous hours reset when flow drops below threshold."""
        meter_id = "MTR-003"
        base_time = datetime.fromisoformat("2026-01-29T12:00:00")

        # Initialize
        process_reading(meter_id, base_time, 100.0)

        # 20 hours of continuous flow
        for i in range(1, 21):
            process_reading(
                meter_id,
                base_time + timedelta(hours=i),
                100.0 + (i * 0.2)
            )

        # Drop below threshold (no alert yet, but resets counter)
        result = process_reading(
            meter_id,
            base_time + timedelta(hours=21),
            100.0 + (20 * 0.2) + 0.05  # delta = 0.05 (< 0.1)
        )
        self.assertIsNone(result)
        self.assertEqual(meter_state[meter_id]["continuous_hours"], 0)

    def test_night_flow_leak_detection(self):
        """Test night flow leak detection (2L+ between 2-5 AM)."""
        meter_id = "MTR-004"
        # Start at 2 AM
        base_time = datetime.fromisoformat("2026-01-29T02:00:00")

        # Initialize
        process_reading(meter_id, base_time, 100.0)

        # Simulate night flow accumulation
        result1 = process_reading(
            meter_id,
            base_time + timedelta(minutes=30),
            101.2  # delta = 1.2L (night hours, accumulated)
        )
        self.assertIsNone(result1)

        result2 = process_reading(
            meter_id,
            base_time + timedelta(hours=1),
            102.5  # delta = 1.3L, total night flow = 2.5L
        )
        self.assertEqual(result2, "NIGHT_FLOW_LEAK")

    def test_night_flow_no_alert_during_day(self):
        """Test that daytime flow doesn't trigger night leak alert."""
        meter_id = "MTR-005"
        # Start at 10 AM
        base_time = datetime.fromisoformat("2026-01-29T10:00:00")

        # Initialize
        process_reading(meter_id, base_time, 100.0)

        # High daytime flow
        result = process_reading(
            meter_id,
            base_time + timedelta(hours=1),
            110.0  # delta = 10L during day
        )
        self.assertIsNone(result)
        # night_flow should still be 0
        self.assertEqual(meter_state[meter_id]["night_flow"], 0.0)

    def test_multiple_meters_independent_state(self):
        """Test that multiple meters maintain independent state."""
        base_time = datetime.fromisoformat("2026-01-29T12:00:00")

        # Meter 1: high flow
        process_reading("MTR-A", base_time, 100.0)
        process_reading("MTR-A", base_time + timedelta(hours=1), 110.0)

        # Meter 2: low flow (delta < 0.1L)
        process_reading("MTR-B", base_time, 200.0)
        process_reading("MTR-B", base_time + timedelta(hours=1), 200.05)

        # Check independent state
        self.assertEqual(meter_state["MTR-A"]["continuous_hours"], 1.0)
        self.assertEqual(meter_state["MTR-B"]["continuous_hours"], 0.0)

    def test_state_persistence_across_readings(self):
        """Test that meter state persists across multiple readings."""
        meter_id = "MTR-006"
        base_time = datetime.fromisoformat("2026-01-29T12:00:00")

        # Initialize
        process_reading(meter_id, base_time, 100.0)
        initial_time = meter_state[meter_id]["last_time"]

        # Read again
        process_reading(meter_id, base_time + timedelta(hours=1), 100.5)
        updated_time = meter_state[meter_id]["last_time"]

        # State should be updated
        self.assertNotEqual(initial_time, updated_time)
        self.assertEqual(meter_state[meter_id]["last_volume"], 100.5)

    def test_zero_delta_no_continuous_flow(self):
        """Test that zero delta (no consumption) keeps continuous hours at 0."""
        meter_id = "MTR-007"
        base_time = datetime.fromisoformat("2026-01-29T12:00:00")

        # Initialize
        process_reading(meter_id, base_time, 100.0)

        # No change
        result = process_reading(
            meter_id,
            base_time + timedelta(hours=1),
            100.0  # delta = 0
        )
        self.assertIsNone(result)
        self.assertEqual(meter_state[meter_id]["continuous_hours"], 0)


if __name__ == "__main__":
    unittest.main()
