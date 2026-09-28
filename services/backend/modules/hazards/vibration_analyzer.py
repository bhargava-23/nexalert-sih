"""Vibration hazard intelligence module

Analyzes accelerometer data from MPU6500 to detect ground instability
that may indicate landslide risk.

Specification: Document 04 (Mathematical Intelligence)
Hardware: MPU6500 3-axis accelerometer on ESP32-S3
"""
import logging
from typing import Optional, Tuple
from datetime import datetime, timezone
import math

logger = logging.getLogger(__name__)


class VibrationAnalyzer:
    """Vibration-based landslide hazard analysis

    Uses existing NexAlert intelligence framework:
    - Baseline: Normal ground vibration levels
    - Anomaly: Deviations from baseline
    - Evidence: Sustained high-frequency vibration
    - Severity: Magnitude and duration
    - State: NORMAL → WATCH → SUSPECTED → CONFIRMED → CRITICAL
    """

    def __init__(self):
        # Thresholds (m/s²)
        self.baseline_max = 0.2  # Normal background vibration
        self.watch_threshold = 0.5  # Start monitoring
        self.suspected_threshold = 1.0  # Possible ground instability
        self.confirmed_threshold = 2.0  # Significant seismic activity
        self.critical_threshold = 5.0  # Extreme ground motion

        # State persistence (similar to Track 4 firmware)
        self.persistence_required = 3  # Consecutive readings
        self.state_history = []
        self.current_state = "NORMAL"
        self.state_counter = 0

    def analyze_vibration(
        self,
        vibration_mps2: float,
        measurement_timestamp: datetime,
        baseline_vibration: Optional[float] = None
    ) -> dict:
        """Analyze vibration reading for landslide hazard

        Args:
            vibration_mps2: Vibration magnitude (m/s²) from MPU6500
            measurement_timestamp: When measurement was taken
            baseline_vibration: Expected baseline vibration level

        Returns:
            Hazard assessment dict with state, evidence, confidence, severity, risk
        """
        # Use baseline or default
        baseline = baseline_vibration if baseline_vibration is not None else self.baseline_max

        # Compute anomaly (deviation from baseline)
        anomaly = max(0.0, vibration_mps2 - baseline)

        # Compute evidence (normalized vibration level)
        # Evidence increases with sustained vibration above threshold
        if vibration_mps2 < self.watch_threshold:
            evidence = 0.0
        elif vibration_mps2 < self.suspected_threshold:
            evidence = 0.3 + (vibration_mps2 - self.watch_threshold) / (self.suspected_threshold - self.watch_threshold) * 0.2
        elif vibration_mps2 < self.confirmed_threshold:
            evidence = 0.5 + (vibration_mps2 - self.suspected_threshold) / (self.confirmed_threshold - self.suspected_threshold) * 0.3
        else:
            evidence = min(1.0, 0.8 + (vibration_mps2 - self.confirmed_threshold) / (self.critical_threshold - self.confirmed_threshold) * 0.2)

        # Compute confidence (how certain we are about the reading)
        # Lower for borderline values, higher for clear signals
        if vibration_mps2 < self.watch_threshold:
            confidence = 0.9  # Confident it's normal
        elif vibration_mps2 < self.suspected_threshold:
            confidence = 0.5  # Uncertain - could be noise
        elif vibration_mps2 < self.confirmed_threshold:
            confidence = 0.7  # Moderately confident
        else:
            confidence = min(0.95, 0.7 + (vibration_mps2 - self.confirmed_threshold) / self.critical_threshold * 0.25)

        # Compute severity (potential impact)
        # Based on vibration magnitude
        if vibration_mps2 < self.suspected_threshold:
            severity = 0.0
        elif vibration_mps2 < self.confirmed_threshold:
            severity = 0.3 + (vibration_mps2 - self.suspected_threshold) / (self.confirmed_threshold - self.suspected_threshold) * 0.3
        else:
            severity = min(1.0, 0.6 + (vibration_mps2 - self.confirmed_threshold) / self.critical_threshold * 0.4)

        # Compute risk (operational risk score)
        # Combines evidence, confidence, and severity
        risk = (evidence * 0.4 + confidence * 0.2 + severity * 0.4)

        # Determine hazard state with persistence
        new_state = self._determine_state(vibration_mps2, evidence, risk)

        # Information condition
        # GOOD if clear signal, DEGRADED if noisy, UNKNOWN if insufficient data
        if vibration_mps2 > self.confirmed_threshold or vibration_mps2 < self.baseline_max:
            information_condition = "GOOD"
        elif confidence < 0.6:
            information_condition = "DEGRADED"
        else:
            information_condition = "GOOD"

        return {
            "hazard_type": "landslide",
            "state": self.current_state,
            "evidence": round(evidence, 3),
            "confidence": round(confidence, 3),
            "severity": round(severity, 3),
            "risk": round(risk, 3),
            "anomaly": round(anomaly, 3),
            "information_condition": information_condition,
            "raw_vibration_mps2": round(vibration_mps2, 3),
            "baseline_vibration": round(baseline, 3),
            "assessment_timestamp": measurement_timestamp.isoformat()
        }

    def _determine_state(self, vibration: float, evidence: float, risk: float) -> str:
        """Determine hazard state with persistence

        Implements state machine: NORMAL → WATCH → SUSPECTED → CONFIRMED → CRITICAL
        """
        # Determine target state based on thresholds
        if vibration >= self.critical_threshold:
            target_state = "CRITICAL"
        elif vibration >= self.confirmed_threshold:
            target_state = "CONFIRMED"
        elif vibration >= self.suspected_threshold:
            target_state = "SUSPECTED"
        elif vibration >= self.watch_threshold:
            target_state = "WATCH"
        else:
            target_state = "NORMAL"

        # Apply persistence
        if target_state != self.current_state:
            self.state_counter += 1
            if self.state_counter >= self.persistence_required:
                logger.info(f"Vibration state transition: {self.current_state} → {target_state} (vibration={vibration:.2f} m/s²)")
                self.current_state = target_state
                self.state_counter = 0
        else:
            self.state_counter = 0

        return self.current_state


# Global analyzer instance
_vibration_analyzer: Optional[VibrationAnalyzer] = None


def get_vibration_analyzer() -> VibrationAnalyzer:
    """Get global vibration analyzer instance"""
    global _vibration_analyzer
    if _vibration_analyzer is None:
        _vibration_analyzer = VibrationAnalyzer()
    return _vibration_analyzer


def analyze_telemetry_vibration(telemetry_record: dict) -> Optional[dict]:
    """Analyze vibration from telemetry record

    Args:
        telemetry_record: Telemetry dict with measurements.vibration_mps2

    Returns:
        Hazard assessment dict or None if no vibration data
    """
    measurements = telemetry_record.get("measurements", {})
    vibration = measurements.get("vibration_mps2")

    if vibration is None:
        return None

    timestamp_str = telemetry_record.get("measurement_timestamp")
    if timestamp_str:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    else:
        timestamp = datetime.now(timezone.utc)

    analyzer = get_vibration_analyzer()
    return analyzer.analyze_vibration(vibration, timestamp)
