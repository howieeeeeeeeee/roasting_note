# Hardware Documentation

Documentation for hardware components used with RoastLogger.

## Components

| Component | Description | Documentation |
|-----------|-------------|---------------|
| K-Type Temperature Sensor | ESP32 + MAX31855 thermocouple | [thermo-sensor.md](./thermo-sensor.md) |

## Temperature Sensor Overview

The temperature sensor is a separate hardware project (Thermo) that provides real-time temperature readings via HTTP.

- **Controller:** ESP32 DevKit
- **Sensor:** MAX31855 K-Type Thermocouple Amplifier
- **Communication:** WiFi HTTP server
- **Default IP:** 192.168.0.47

See [thermo-sensor.md](./thermo-sensor.md) for complete setup and usage instructions.
