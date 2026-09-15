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
| `DEVICE` | Unique stable deployment identity for audited sync preflight |
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
DEVICE=your-stable-machine-name
TEMP_SENSOR_URL=http://192.168.0.47/temp
TZ=Asia/Taipei
```

## Database Synchronization

Render and every non-loopback host remain preview-only. The browser phase API
requires both the direct request peer and `Host` to be loopback and rejects
forwarded-header locality, cross-origin mutation requests, and non-JSON bodies.
The old one-request mutation routes remain disabled.

On a trusted local instance reached directly through `localhost`, `127.0.0.1`,
or `::1`, Settings shows an exact count-only action forecast, then offers one
button to create and verify the complete destination backup and a second button
to Apply or Cancel. The forecast is revalidated before backup and apply.
Awaiting-apply state is ignored and resumable after restart; changed data hides
Apply, while interrupted/corrupt state requires manual artifact review. No
proxy, remote authentication, or hosted browser apply is supported.

Operators may instead use the guarded CLI from a trusted machine with both
endpoints configured:

```bash
uv run python scripts/sync_database.py \
  --direction online-to-local \
  --dry-run
```

Review the sanitized plan before separately authorizing an applied run. The CLI
requires both exact run-specific tokens; Settings requires its two distinct
phase clicks. Both create a complete destination backup under ignored
`db_backup/`. Only the reviewed audit record is eligible for publication. See
[Database Sync](../features/database-sync.md).

## Bean purchase history rollout (RN-0031)

Deploy purchase-history-compatible application code before syncing migrated
local beans to the hosted database. Legacy scalar records remain readable and
convert on a valid edit. Back up and migrate the local database with
`scripts/migrate_bean_purchases.py` while local writes are paused; see
[Bean Management](../features/beans-management.md#local-migration) for preview,
apply, verification, and backup paths. A rerun must report zero eligible beans.

Review a fresh guarded local-to-online dry run after your purchase corrections.
The code deployment and local migration do not authorize applying a remote
mirror; use the existing Settings or CLI confirmation flow separately.
