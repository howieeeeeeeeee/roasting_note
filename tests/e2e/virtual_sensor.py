"""Deterministic loopback sensor implementing the ESP32 HTTP contract."""

from __future__ import annotations

import ipaddress
import threading
import time
from dataclasses import dataclass

from flask import Flask, Response, jsonify, request


SCENARIOS = {
    "healthy-ramp",
    "slow-success",
    "rate-limited",
    "timeout",
    "offline",
    "malformed",
    "fault",
}


@dataclass
class SensorState:
    scenario: str = "healthy-ramp"
    call_count: int = 0
    rate_limit_calls: int = 2

    def __post_init__(self):
        self.lock = threading.Lock()

    def configure(self, scenario, rate_limit_calls=None):
        if scenario not in SCENARIOS:
            raise ValueError(f"unknown scenario: {scenario}")
        with self.lock:
            self.scenario = scenario
            self.call_count = 0
            if rate_limit_calls is not None:
                value = int(rate_limit_calls)
                if value < 0:
                    raise ValueError("rate_limit_calls must be non-negative")
                self.rate_limit_calls = value

    def next_call(self):
        with self.lock:
            self.call_count += 1
            return self.scenario, self.call_count, self.rate_limit_calls

    def snapshot(self):
        with self.lock:
            return {
                "scenario": self.scenario,
                "call_count": self.call_count,
                "rate_limit_calls": self.rate_limit_calls,
            }


def _is_loopback(remote_address):
    try:
        return ipaddress.ip_address(remote_address or "").is_loopback
    except ValueError:
        return False


def _temperature(call_number):
    celsius = round(145.0 + (call_number - 1) * 2.5, 2)
    return {
        "temperature_celsius": celsius,
        "temperature_fahrenheit": round((celsius * 9 / 5) + 32, 2),
    }


def create_sensor_app(*, slow_delay=0.2, timeout_delay=1.2):
    app = Flask(__name__)
    state = SensorState()
    app.extensions["e2e_sensor_state"] = state

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", **state.snapshot()})

    @app.get("/temp")
    def temperature():
        scenario, call_number, limited_calls = state.next_call()
        if scenario == "slow-success":
            time.sleep(slow_delay)
            return jsonify(_temperature(call_number))
        if scenario == "rate-limited" and call_number <= limited_calls:
            return jsonify({"error": "rate_limited"}), 429
        if scenario == "timeout":
            time.sleep(timeout_delay)
            return jsonify(_temperature(call_number))
        if scenario == "offline":
            return jsonify({"error": "sensor_offline"}), 503
        if scenario == "malformed":
            return Response(
                '{"temperature_celsius":',
                status=200,
                mimetype="application/json",
            )
        if scenario == "fault":
            return jsonify({"error": "thermocouple_fault"}), 503
        return jsonify(_temperature(call_number))

    @app.get("/diagnostics")
    def diagnostics():
        scenario = state.snapshot()["scenario"]
        if scenario == "fault":
            return jsonify(
                {
                    "status": "FAULT",
                    "error_code": 5,
                    "errors": ["open_circuit", "short_to_ground"],
                    "thermocouple_celsius": None,
                    "internal_celsius": 24.0,
                }
            )
        return jsonify(
            {
                "status": "OK",
                "error_code": 0,
                "errors": [],
                "thermocouple_celsius": _temperature(1)[
                    "temperature_celsius"
                ],
                "internal_celsius": 24.0,
            }
        )

    @app.post("/__e2e/scenario")
    def set_scenario():
        if not _is_loopback(request.remote_addr):
            return jsonify({"error": "loopback access required"}), 403
        payload = request.get_json(silent=True) or {}
        try:
            state.configure(
                payload.get("scenario"),
                payload.get("rate_limit_calls"),
            )
        except (TypeError, ValueError) as error:
            return jsonify({"error": str(error)}), 400
        return jsonify({"success": True, **state.snapshot()})

    return app
