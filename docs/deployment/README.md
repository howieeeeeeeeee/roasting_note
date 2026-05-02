# Deployment Guide

Deployment instructions for RoastLogger.

## Render (Production)

RoastLogger is deployed on Render's free tier.

### Setup

1. **Create Web Service** on Render
2. **Connect GitHub repository**
3. **Configure build settings:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

### Environment Variables

Set these in Render dashboard:

| Variable | Description |
|----------|-------------|
| `FLASK_APP` | `app.py` |
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | Random string for sessions |
| `MONGO_URI` | MongoDB Atlas connection string |
| `MONGO_URI_LOCAL` | Local MongoDB (not used in production) |
| `DEFAULT_DB` | `local` by default; switch to online manually when needed |
| `TZ` | `Asia/Taipei` |

### Free Tier Limitations

- Service spins down after 15 minutes of inactivity
- ~30 second cold start delay on first request
- Acceptable for personal use

## MongoDB Atlas

### Setup

1. Create free M0 cluster on MongoDB Atlas
2. Create database user
3. Whitelist IP addresses (or allow from anywhere)
4. Copy connection string to `MONGO_URI`

### Collections

The application uses two collections:
- `beans` - Coffee bean inventory
- `roasts` - Roasting sessions

## Local Development

### Requirements

- Python 3.x
- MongoDB (local instance)
- pip packages from `requirements.txt`

### Setup

```bash
# Clone repository
git clone https://github.com/username/roasting_note.git
cd roasting_note

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your settings

# Run development server
flask run
```

### Environment Variables (.env)

```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
MONGO_URI=mongodb+srv://...
MONGO_URI_LOCAL=mongodb://localhost:27017/roastlogger
DEFAULT_DB=local
TEMP_SENSOR_URL=http://192.168.0.47/temp
TZ=Asia/Taipei
```
