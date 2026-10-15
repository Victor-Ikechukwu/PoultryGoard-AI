"""Environmental sensors + early-warning fusion.

Implements the yellow-highlighted PDF extension: add temperature, humidity, CO2
and ammonia (NH3) sensors to the cameras and study the relationship between
environment, chick behaviour and mortality -- turning the system into a genuine
early-warning tool rather than a mortality detector alone.

For the proof of concept the readings are simulated with realistic drift and
optional anomaly injection, behind an interface a real Modbus/MQTT sensor feed
can replace.  Target bands tighten as the flock ages (brooding is hot, finishing
is cooler).
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import random
import time

from . import config


@dataclass
class SensorReading:
    t: float
    temp_c: float
    humidity: float
    co2_ppm: float
    nh3_ppm: float


@dataclass
class EnvAlert:
    metric: str
    value: float
    band: tuple
    severity: str          # "warn" | "alarm"
    message: str


def target_temp_band(age_days: int) -> tuple:
    """Broiler set-point drops ~0.3 C/day from ~33 C at day 0 to ~21 C."""
    sp = max(21.0, 33.0 - 0.3 * age_days)
    return (round(sp - 2, 1), round(sp + 2, 1))


class EnvironmentSensors:
    """Simulated multi-sensor node (temp/humidity/CO2/NH3)."""

    def __init__(self, settings: config.Settings | None = None, seed: int | None = None):
        self.s = settings or config.DEFAULTS
        self.rng = random.Random(seed)
        self._t0 = time.time()
        self.inject = {"temp": 0.0, "humidity": 0.0, "co2": 0.0, "nh3": 0.0}

    def read(self, now: float | None = None) -> SensorReading:
        now = now or time.time()
        e = now - self._t0
        band = target_temp_band(self.s.flock_age_days)
        base_t = (band[0] + band[1]) / 2
        temp = base_t + 1.2 * math.sin(e / 40) + self.rng.uniform(-0.3, 0.3) + self.inject["temp"]
        hum = 60 + 6 * math.sin(e / 55 + 1) + self.rng.uniform(-1.5, 1.5) + self.inject["humidity"]
        co2 = 1800 + 500 * (0.5 + 0.5 * math.sin(e / 70)) + self.rng.uniform(-80, 80) + self.inject["co2"]
        nh3 = 9 + 4 * (0.5 + 0.5 * math.sin(e / 90 + 2)) + self.rng.uniform(-1, 1) + self.inject["nh3"]
        return SensorReading(now, round(temp, 2), round(max(0, hum), 1),
                             round(max(0, co2), 0), round(max(0, nh3), 1))

    def evaluate(self, r: SensorReading) -> list[EnvAlert]:
        alerts: list[EnvAlert] = []
        tband = target_temp_band(self.s.flock_age_days)
        if r.temp_c < tband[0] - 1 or r.temp_c > tband[1] + 1:
            sev = "alarm" if abs(r.temp_c - sum(tband) / 2) > 4 else "warn"
            alerts.append(EnvAlert("temperature", r.temp_c, tband, sev,
                                   f"Temp {r.temp_c} C outside {tband} C for age {self.s.flock_age_days}d"))
        hb = self.s.humidity_band
        if r.humidity < hb[0] or r.humidity > hb[1]:
            alerts.append(EnvAlert("humidity", r.humidity, hb, "warn",
                                   f"Humidity {r.humidity}% outside {hb}%"))
        if r.co2_ppm > self.s.co2_band_ppm[1]:
            sev = "alarm" if r.co2_ppm > 5000 else "warn"
            alerts.append(EnvAlert("co2", r.co2_ppm, self.s.co2_band_ppm, sev,
                                   f"CO2 {r.co2_ppm:.0f} ppm above {self.s.co2_band_ppm[1]:.0f}"))
        if r.nh3_ppm > self.s.nh3_band_ppm[1]:
            sev = "alarm" if r.nh3_ppm > 25 else "warn"
            alerts.append(EnvAlert("nh3", r.nh3_ppm, self.s.nh3_band_ppm, sev,
                                   f"NH3 {r.nh3_ppm:.1f} ppm above {self.s.nh3_band_ppm[1]:.0f} (welfare limit 25)"))
        return alerts

    # demo helpers -----------------------------------------------------------
    def trigger_anomaly(self, metric: str, amount: float):
        if metric in self.inject:
            self.inject[metric] = amount

    def clear_anomalies(self):
        self.inject = {k: 0.0 for k in self.inject}
