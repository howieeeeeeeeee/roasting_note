# RoastLogger

A personal, mobile-responsive web application for home coffee roasters to track beans, log detailed roast profiles, and manage inventory.

## Features

- Bean inventory management with stock tracking
- Live roasting interface with real-time temperature monitoring
- K-Type temperature sensor integration (auto-polling, smart averaging)
- Roast profiles with temperature curves and key event markers
- Review system for tasting notes and ratings
- Mobile-responsive design

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- MongoDB (local or Atlas)

### Setup

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI and settings

# Run the app
uv run python app.py
```

Open `http://localhost:5000` in your browser.

## Hardware/Firmware

The ESP32 firmware code for the temperature sensor board is located in the `thermo/` folder. This is a PlatformIO project that can be built and uploaded to your ESP32 device.

See **[Hardware Setup](docs/hardware/)** for complete setup and usage instructions.

## Documentation

For detailed information, see the `docs/` folder:

- **[Project Overview](docs/README.md)** - Start here for navigation and architecture
- **[Architecture](docs/architecture/)** - API endpoints, data models, tech stack
- **[Features](docs/features/)** - Detailed feature specifications
- **[Hardware Setup](docs/hardware/)** - K-Type temperature sensor integration
- **[Deployment](docs/deployment/)** - Render deployment guide
- **[Testing](tests/README.md)** - Running and writing tests

## License

MIT License - Feel free to use this for your own coffee roasting adventures!
