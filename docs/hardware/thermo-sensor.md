## Project Overview

This is a **PlatformIO-based ESP32 project** that creates a WiFi-connected temperature monitoring server using a MAX31855 thermocouple sensor. The ESP32 hosts a simple web server that exposes temperature readings via HTTP endpoints.

---

## Project Structure

```
Thermo/
├── platformio.ini          # PlatformIO configuration (board, libs, settings)
├── src/
│   └── main.cpp            # Main application code
├── include/                # Project header files (currently empty)
├── lib/                    # Private/custom libraries (currently empty)
├── test/                   # Unit tests directory
├── .pio/                   # Build artifacts & library dependencies (auto-generated)
│   ├── build/              # Compiled binaries
│   └── libdeps/            # Downloaded library dependencies
└── .vscode/                # VS Code configuration files
```

### Key Files

| File | Purpose |
|------|---------|
| platformio.ini | Project configuration: target board (`esp32dev`), framework (`arduino`), serial monitor speed, and library dependencies |
| main.cpp | Main application code containing WiFi setup, web server routes, and thermocouple reading logic |

---

## Hardware Configuration

The project uses these GPIO pins for the MAX31855 thermocouple:

| Signal | GPIO Pin |
|--------|----------|
| CLK (Clock) | GPIO 18 |
| MISO (Data Out) | GPIO 19 |
| CS (Chip Select) | GPIO 5 |

**Static IP Configuration:**
- IP Address: `192.168.0.47`
- Gateway: `192.168.0.1`
- Subnet: `255.255.255.0`

---

## Web Server Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | HTML info page with links |
| `/temp` | GET | JSON temperature data (Celsius & Fahrenheit) |
| `/diagnostics` | GET | Detailed sensor diagnostics and error codes |

---

## Library Dependencies

Defined in platformio.ini:

- `Adafruit MAX31855 library` - Thermocouple sensor driver
- `AsyncTCP` - Async TCP library for ESP32
- `ESPAsyncWebServer` - Asynchronous web server

---

## How to Upload Code to Your ESP32

### Method 1: Using the PlatformIO Toolbar (Recommended)

1. **Connect your ESP32** to your computer via USB cable

2. **Look at the bottom status bar** in VS Code. You'll see the PlatformIO toolbar:

   ![PlatformIO Toolbar Location](https://docs.platformio.org/en/latest/_images/platformio-ide-vscode-toolbar.png)

3. **Click the Upload button** (right arrow icon →)

   The toolbar buttons from left to right:
   | Icon | Action |
   |------|--------|
   | 🏠 (Home) | Open PlatformIO Home |
   | ✓ (Checkmark) | **Build** - Compile without uploading |
   | → (Arrow) | **Upload** - Compile and flash to board |
   | 🧹 (Trash) | Clean build files |
   | 🔌 (Plug) | Serial Monitor |
   | 🖥️ (Terminal) | Open terminal |

4. **Wait for the upload** to complete. You'll see output like:
   ```
   Uploading .pio/build/esp32dev/firmware.bin
   ...
   Writing at 0x00010000... (100 %)
   Wrote 123456 bytes
   Hard resetting via RTS pin...
   ```

### Method 2: Using Command Palette

1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type `PlatformIO: Upload`
3. Press Enter

### Method 3: Using Keyboard Shortcut

- Press `Cmd+Alt+U` (macOS) or `Ctrl+Alt+U` (Windows/Linux)

---

## Complete Workflow

```bash
# 1. Build only (verify code compiles)
#    Click ✓ in toolbar or run:
pio run

# 2. Upload to board
#    Click → in toolbar or run:
pio run --target upload

# 3. Monitor serial output
#    Click 🔌 in toolbar or run:
pio device monitor
```

---

## After Uploading

1. **Open Serial Monitor** (click the plug icon 🔌 in the toolbar)
2. **Note the IP address** printed in the console
3. **Access the web interface** at:
   - `http://192.168.0.47/` - Home page
   - `http://192.168.0.47/temp` - Temperature JSON
   - `http://192.168.0.47/diagnostics` - Sensor diagnostics

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Upload fails | Hold the **BOOT** button on ESP32 when upload starts |
| Port not found | Check USB cable (some are charge-only) |
| WiFi won't connect | Update `WIFI_SSID` and `WIFI_PASSWORD` in main.cpp |
| Sensor reads NaN | Check thermocouple wiring to GPIO pins 5, 18, 19 |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────┐
│         VS Code Bottom Status Bar           │
├─────────────────────────────────────────────┤
│  🏠  ✓  →  🧹  🔌  🖥️   env:esp32dev        │
│       │  │      │                           │
│       │  │      └── Serial Monitor          │
│       │  └── UPLOAD (Use this!)             │
│       └── Build only                        │
└─────────────────────────────────────────────┘
```