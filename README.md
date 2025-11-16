# RoastLogger

A personal, mobile-responsive web application for home coffee roasters to track beans, log detailed roast profiles, and manage inventory.

## Features

- **Bean Management**: Track green coffee beans with detailed information including origin, process, supplier, and inventory
- **Live Roasting Interface**: Real-time roast tracking with timer, temperature logging, and key event markers
- **K-Type Temperature Sensor Integration**: Real-time temperature monitoring using Howie's design K-Type Sensor V1
  - Automatic temperature display during roasting (updates every 5 seconds)
  - Auto-logging of temperature data throughout the roast
  - Automatic temperature capture with manual events
  - Graceful handling of sensor unavailability
- **Roast Profiles**: Store complete roast data including temperature curves, timings, weights, and loss percentages
- **Review System**: Rate and review your roasts with tasting notes
- **Inventory Management**: Automatic stock tracking that updates when you roast
- **Responsive Design**: Fully functional on mobile, tablet, and desktop

## Tech Stack

- **Backend**: Python 3.11, Flask
- **Database**: MongoDB (PyMongo)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Deployment**: Render with Gunicorn

## Project Structure

```
roasting_note/
├── app.py                  # Main Flask application
├── models/
│   ├── __init__.py
│   ├── bean_helpers.py     # Bean CRUD operations
│   └── roast_helpers.py    # Roast CRUD operations
├── templates/
│   ├── base.html           # Base template with navigation
│   ├── index.html          # Dashboard with roast list
│   ├── beans_list.html     # Bean inventory list
│   ├── beans_form.html     # Add/edit bean form
│   ├── roast_live.html     # Live roasting interface
│   ├── roast_detail.html   # Roast detail view
│   └── roast_edit.html     # Post-roast editing
├── static/
│   └── css/
│       └── style.css       # Responsive styles
├── pyproject.toml          # Project dependencies (uv)
├── requirements.txt        # Alternative dependency file
├── render.yaml             # Render deployment config
├── .env.example            # Environment variables template
└── README.md
```

## Local Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager (install with: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`)
- MongoDB (local installation or MongoDB Atlas account)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd roasting_note
   ```

2. **Install dependencies with uv**:
   ```bash
   uv sync
   ```
   
   This will automatically create a virtual environment and install all dependencies from `pyproject.toml`.

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure:
   ```
   SECRET_KEY=your-secret-key-here
   MONGO_URI=mongodb://localhost:27017/  # or your MongoDB Atlas connection string
   TEMP_SENSOR_URL=http://192.168.0.47/temp  # URL of your K-Type temperature sensor
   ```

4. **Run the application**:
   ```bash
   uv run python app.py
   ```
   
   Or activate the virtual environment first:
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   python app.py
   ```

5. **Access the app**:
   Open your browser and navigate to `http://localhost:5000`

## MongoDB Setup

### Option 1: Local MongoDB

1. Install MongoDB Community Edition
2. Start MongoDB service
3. Use connection string: `mongodb://localhost:27017/`

### Option 2: MongoDB Atlas (Recommended for Production)

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (M0 Free Tier)
3. Set up database access (username/password)
4. Whitelist your IP address (or 0.0.0.0/0 for development)
5. Get your connection string:
   ```
   mongodb+srv://<username>:<password>@cluster.mongodb.net/roastlogger?retryWrites=true&w=majority
   ```

## K-Type Temperature Sensor Setup

RoastLogger integrates with Howie's design K-Type Sensor V1 for real-time temperature monitoring during roasting.

### Sensor Requirements

- **Hardware**: K-Type thermocouple with HTTP endpoint (Howie's custom design)
- **Network**: Local network access to the sensor device
- **Response Format**: JSON response with `temperatur_celsius` field

### Configuration

1. **Set up your K-Type sensor hardware** and connect it to your local network
2. **Configure the sensor URL** in your `.env` file:
   ```
   TEMP_SENSOR_URL=http://192.168.0.47/temp
   ```
   Replace with your sensor's actual IP address and endpoint

3. **Test the sensor** by visiting the URL in your browser - you should see:
   ```json
   {"temperature_celsius": 27.00, "temperature_fahrenheit": 80.60}
   ```

### How It Works

- **Automatic Polling**: The live roast page polls the sensor every 5 seconds
- **Smart Averaging**: Makes 3 requests per poll and averages the top 2 readings for accuracy
- **Graceful Degradation**: If the sensor is offline, the app displays "Offline" and continues working
- **Auto-Logging**: Temperature data is automatically saved to your roast profile every 5 seconds
- **Manual Override**: You can still manually enter temperature values if needed

### Troubleshooting

- **"Offline" displayed**: Check that the sensor device is powered on and connected to the network
- **Intermittent readings**: Verify network stability and sensor device reliability
- **Wrong IP address**: Update `TEMP_SENSOR_URL` in your `.env` file and restart the application

## Deployment to Render

### Prerequisites

- GitHub repository with your code
- MongoDB Atlas cluster (free tier)
- Render account (free)

### Steps

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create a new Web Service on Render**:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect the `render.yaml` configuration

3. **Set Environment Variables** in Render Dashboard:
   - `SECRET_KEY`: Generate a long random string
   - `MONGO_URI`: Your MongoDB Atlas connection string
   - `FLASK_ENV`: `production`
   - `TEMP_SENSOR_URL`: Your K-Type sensor URL (Note: The sensor must be accessible from the Render server. For local sensors, consider using a VPN or exposing the sensor via a public endpoint with proper security.)

4. **Deploy**:
   - Render will automatically build and deploy
   - Your app will be available at `https://your-app-name.onrender.com`

### Important Notes for Render Free Tier

- The service will spin down after 15 minutes of inactivity
- First request after inactivity may take ~30 seconds to respond
- Perfect for personal projects and development

## Usage Guide

### Adding Beans

1. Navigate to "Beans" in the navigation
2. Click "Add New Bean"
3. Fill in bean information (name, origin, process, stock, etc.)
4. Click "Add Bean"

### Starting a Roast

1. From the dashboard, click "Start New Roast"
2. Select a bean from the dropdown
3. Enter the green weight (grams)
4. Click "Start Roast" to begin the timer
5. During roasting:
   - Click event buttons (Yellowing, FC Start, etc.) to mark key moments
   - Enter temperature, fan, and power settings
   - Click "Add Event" to log data points
6. Click "End Roast" when finished
7. You'll be redirected to edit the roast and add final details

### Editing Roasts

- Add roasted weight to calculate weight loss percentage
- Add general notes about the roast
- Review the temperature curve and key timings
- Add a title to identify the roast

### Adding Reviews

1. Open a roast from the dashboard
2. Scroll to the "Reviews" section
3. Click "Add Review"
4. Rate the roast (1-5) and add tasting notes
5. Submit the review

## API Endpoints

### Beans
- `GET /beans` - List all beans
- `POST /api/beans/add` - Create new bean
- `POST /api/beans/edit/<bean_id>` - Update bean
- `POST /api/beans/delete/<bean_id>` - Delete bean

### Roasts
- `GET /` - Dashboard (list roasts)
- `GET /roast/live/<roast_id>` - Live roasting interface
- `GET /roast/detail/<roast_id>` - View roast details
- `GET /roast/edit/<roast_id>` - Edit roast form
- `POST /api/roast/create` - Create new roast
- `POST /api/roast/start/<roast_id>` - Start roast timer
- `POST /api/roast/end/<roast_id>` - End roast timer
- `POST /api/roast/add_timing/<roast_id>` - Log key event
- `POST /api/roast/add_event/<roast_id>` - Log temperature data
- `POST /api/roast/update/<roast_id>` - Update roast
- `POST /api/roast/delete/<roast_id>` - Delete roast
- `POST /api/roast/add_review/<roast_id>` - Add review
- `GET /api/temp/current` - Get current temperature from K-Type sensor

## Database Schema

### Beans Collection

```javascript
{
  "_id": ObjectId,
  "name": String,
  "origin": String,
  "process": String,
  "supplier": String,
  "purchase_date": Date,
  "purchase_price_total": Decimal128,
  "purchase_weight_grams": Integer,
  "unit_price_per_kg": Decimal128,
  "stock_grams": Integer,
  "notes": String,
  "created_at": Date,
  "updated_at": Date
}
```

### Roasts Collection

```javascript
{
  "_id": ObjectId,
  "bean_id": ObjectId,
  "title": String,
  "roast_date": Date,
  "original_weight_grams": Integer,
  "roasted_weight_grams": Integer,
  "weight_loss_percentage": Float,
  "temp_measurement_method": String,
  "roast_start_time": Date,
  "roast_end_time": Date,
  "roast_duration_seconds": Integer,
  "key_timings": [
    {
      "event_name": String,
      "time_seconds": Integer
    }
  ],
  "temp_curve": [
    {
      "time_seconds": Integer,
      "temperature": Float,
      "fan_setting": Integer,
      "power_setting": Integer
    }
  ],
  "general_notes": String,
  "reviews": [
    {
      "_id": ObjectId,
      "rating": Integer,
      "notes": String,
      "review_date": Date,
      "created_at": Date,
      "updated_at": Date
    }
  ],
  "created_at": Date,
  "updated_at": Date
}
```

## Future Enhancements

- Data visualization with charts (temperature curves, roast progression)
- Export roast profiles as CSV/PDF
- Comparison view between multiple roasts
- Search and filter functionality
- Batch operations for beans
- Advanced analytics and statistics
- Photo uploads for beans and roasts
- Multi-user support with authentication

## Contributing

This is a personal project, but suggestions and bug reports are welcome! Please open an issue on GitHub.

## License

MIT License - Feel free to use this for your own coffee roasting adventures!

## Acknowledgments

Built for home coffee roasters who want to track and improve their roasting process.
