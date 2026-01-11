Here is a technical specification document for your "RoastLogger" web application. This document outlines the data models, features, and technical requirements based on your ideas.

-----

## **Project Spec: RoastLogger Web App**

### **1. Project Overview**

**RoastLogger** is a personal, mobile-responsive web application designed to help a home roaster track coffee beans, log detailed roast profiles, and manage inventory.

The application will be built using the **Python Flask** framework for the backend, **MongoDB** as the database (connected via **PyMongo**), and deployed on the **Render** free plan.

### **2. Technical Stack**

* **Backend:** Python 3.x, Flask
* **Database:** MongoDB (e.g., MongoDB Atlas Free Tier M0)
* **ODM/Driver:** PyMongo
* **Frontend:** HTML5, CSS3 (with media queries for RWD), vanilla JavaScript (for live timer and API calls)
* **Deployment:** Render (using `gunicorn` as the WSGI server)
* **Environment:** Python `virtualenv`, `requirements.txt`

-----

### **3. Data Models (MongoDB Schema)**

The database will consist of two primary collections: `beans` and `roasts`.

#### **3.1. `beans` Collection**

Stores information about each type of green coffee bean in your inventory.

```json
{
  "_id": "ObjectId",
  "name": "String", // e.g., "Ethiopia Yirgacheffe Gedeo"
  "origin": "String", // e.g., "Ethiopia"
  "process": "String", // e.g., "Washed", "Natural", "Honey"
  "supplier": "String", // e.g., "Sweet Maria's"
  "purchase_date": "Date",
  "purchase_price_total": "Decimal128", // Total cost for the batch
  "purchase_weight_grams": "Integer", // Weight of the batch when purchased
  "unit_price_per_kg": "Decimal128", // (Calculated, optional)
  "stock_grams": "Integer", // Current available stock in grams
  "notes": "String", // Tasting notes, website description, etc.
  "color": "String", // Hex color code for visual identification (e.g., "#6B8E6F"), defaults to "#6B8E6F" (muted green)
  "archived": "Boolean", // Default false. True = soft deleted
  "created_at": "Date",
  "updated_at": "Date"
}
```

#### **3.2. `roasts` Collection**

Stores all data related to a single roasting session. This model embeds the temperature curve, key timings, and reviews.

```json
{
  "_id": "ObjectId",
  "bean_id": "ObjectId", // Reference to an _id in the 'beans' collection
  "title": "String", // e.g., "Roast #23 - Yirgacheffe", defaults to "Untitled Roast"
  "roast_date": "Date", // The date of the roast

  // ----- Weights & Loss -----
  "original_weight_grams": "Integer",
  "roasted_weight_grams": "Integer", // Can be null until entered post-roast
  "weight_loss_percentage": "Float", // (Calculated) (original - roasted) / original

  // ----- Roast Profile -----
  "temp_measurement_method": "String", // e.g., "K-Type (Bean)", "IR Gun (Drum)", defaults to "IR Gun"
  "roaster": "String", // e.g., "Freshroast SR800", "Behmor 1600", defaults to "Freshroast SR800"
  "roast_start_time": "Date", // Timestamp when "Start" is clicked
  "roast_end_time": "Date", // Timestamp when "End" is clicked
  "roast_duration_seconds": "Integer", // (Calculated)

  "key_timings": [
    // Array of embedded documents
    {
      "event_name": "String", // e.g., "Yellowing", "First Crack Start", "First Crack End", "Drop"
      "time_seconds": "Integer" // Seconds from roast_start_time
    }
  ],

  "temp_curve": [
    // Array of embedded documents, logged during the roast
    {
      "time_seconds": "Integer", // Seconds from roast_start_time
      "temperature": "Float", // The temperature reading
      "fan_setting": "Integer", // e.g., 1-9
      "power_setting": "Integer", // e.g., 1-9
      "ror": "Float", // Rate of Rise in °C/min (optional, calculated field)
      "note": "String" // Optional note for this event
    }
  ],

  "general_notes": "String", // General notes for the whole roast

  // ----- Reviews (Embedded) -----
  "reviews": [
    // Array of embedded review documents
    {
      "_id": "ObjectId", // Unique ID for the review
      "overall_score": "Integer", // Overall score 1-5
      "extraction_method": "String", // One of: "espresso", "pourover", "ice_drop", "cold_brew", "other"
      "notes": "String", // Tasting notes, brew method details, etc.
      "review_date": "Date",
      "created_at": "Date",
      "updated_at": "Date"
    }
  ],

  "archived": "Boolean", // Default false. True = soft deleted
  "created_at": "Date",
  "updated_at": "Date"
}
```

-----

### **4. Functional Specifications**

#### **4.1. General & UI/UX**

* **Responsive Web Design (RWD):** All pages must be fully functional and readable on both mobile (portrait/landscape) and desktop screens. Use flexible grids, media queries, and touch-friendly buttons.
* **Navigation:** A simple navigation bar (e.g., "Roasts", "Beans").

#### **4.2. Bean Management**

* **View Beans (List):**
  * A page (`/beans`) that displays a list/cards of all beans in the `beans` collection.
  * Show key info: `name`, `origin`, and current `stock_grams`.
  * Each bean entry should link to its "Edit Bean" page.
  * Include a "Add New Bean" button.
* **Add/Edit Bean (Form):**
  * A form (`/beans/add` or `/beans/edit/<bean_id>`) to create or update a bean.
  * The form must include fields for all properties in the `beans` schema (name, origin, stock, price, etc.).
* **Stock Management (Backend Logic):**
  * **On Roast Create:** When a new roast is saved with an `original_weight_grams`, the backend must find the corresponding `bean` (by `bean_id`) and **decrement** its `stock_grams` by that amount.
    * ` db.beans.updateOne({_id: bean_id}, {$inc: {stock_grams: -original_weight}}) `
  * **On Roast Archive:** When a roast is archived (soft deleted), the backend must find the `bean` and **increment** (restore) its `stock_grams` by the roast's `original_weight_grams`. The roast is not actually deleted, but marked with `archived: true`.
    * `db.beans.updateOne({_id: bean_id}, {$inc: {stock_grams: original_weight}})`
    * `db.roasts.updateOne({_id: roast_id}, {$set: {archived: true}})`
  * **On Roast Edit:** If a roast's `original_weight_grams` is *changed*, the backend must calculate the *difference* from the old weight and apply that difference to the `bean`'s stock.
* **Soft Deletion:**
  * Both beans and roasts use soft deletion via an `archived` boolean field
  * When "deleted", items are marked with `archived: true` instead of being removed from the database
  * All queries filter out archived items by default using `{archived: {$ne: true}}`
  * This preserves historical data and allows for potential recovery if needed

#### **4.3. Roast Management (Dashboard)**

* **View Roasts (List):**
  * The main page (`/`) should display a list of all past roasts from the `roasts` collection, sorted by `roast_date` (newest first).
  * Show key info: `title`, `bean_name` (requires a DB lookup/join), `roast_date`.
  * Each roast should link to a "Roast Detail" page.
  * Include a prominent "Start New Roast" button.
* **Roast Detail Page (`/roast/<roast_id>`):**
  * Display all information for a single roast.
  * Show calculated data: `weight_loss_percentage`, `roast_duration_seconds`.
  * Display `key_timings` and `temp_curve` data (a table or, ideally, a simple chart).
  * Display all `reviews` for this roast.
  * Include an "Edit this Roast" button.

#### **4.4. Live Roasting Interface**

This is the most complex UI. It should be a single page (`/roast/live/<roast_id>`) that uses JavaScript (`fetch`) to communicate with the backend API without page reloads.

1. **Initiation:**
      * Clicking "Start New Roast" on the dashboard creates a new, *draft* `roast` document in the DB (e.g., with `title: "Untitled"`, no weights, no bean).
      * The user is redirected to the "Live Roasting" page: `/roast/live/<new_roast_id>`.
2. **Pre-Roast Setup (Collapsible):**
      * On this page, the user sees:
          * A dropdown to select a **Bean** (populated from `beans` collection, **filtered to show only beans with stock > 0g**).
          * An input for **Original Weight (grams)**.
          * Section collapses automatically when roast starts to maximize screen space
          * *Note:* These can be set now or later in the "Edit" screen.
3. **Roasting:**
      * **Display Layout:**
          * **Timer:** Large display showing MM:SS format
              * Shows FC time in parentheses when First Crack Start is clicked: "MM:SS (MM:SS)"
              * Updates to latest FC if multiple FC events logged
          * **Temperature & RoR:** Side-by-side panels showing:
              * Temperature: Real-time °C reading from sensor
              * RoR: Calculated rate of rise in °C/min (available after 20 seconds)
      * **"Start Roast" Button:**
          * *Frontend:* Starts on-screen timer, auto-collapses setup section
          * *Backend Call:* Sets `roast_start_time` to `datetime.now()`
          * Initiates temperature polling (every 1 second) and logging (every 3 seconds)
      * **Quick Key Events (Compact Buttons):**
          * Minimal buttons with short labels and tooltips:
              * Y (Yellowing)
              * FC (First Crack Start) - triggers FC time display
              * FC-end (First Crack End)
              * SC (Second Crack Start)
              * SC-end (Second Crack End)
          * Clicking logs event with current temperature and settings
      * **Fan & Power Controls:**
          * Direct +/- stepper buttons (no modal)
          * Range: 1-9 for both fan and power
          * Default values: Fan 9, Power 3
          * Large number display with increment/decrement buttons
      * **Data Entry (Form):**
          * Temperature input (auto-filled from sensor if empty)
          * Fan/power settings with stepper controls
          * Optional note field
          * "Add Event" button logs to `temp_curve`
      * **Automatic Background Processes:**
          * Temperature fetched every 1 second from sensor
          * Logged locally to `temp_logs/{roast_id}.csv` every second
          * Logged to database every 3 seconds with RoR value
          * RoR calculated using 20-second sliding window
      * **Live Timeline Display:**
          * Shows both `key_timings` and `temp_curve` events
          * Displays temperature, RoR (if available), fan, and power settings
          * Newest events at top
4. **Ending the Roast:**
      * **"End Roast" Button:**
          * *Frontend:* Stops timer and temperature polling
          * *Backend Call:* Sets `roast_end_time`, attempts final temperature reading
          * *Action:* Redirects to "Edit Roast" page for post-roast details

#### **4.5. Post-Roast & Editing**

* **Edit Roast Page (`/roast/edit/<roast_id>`):**
  * This page is a large form pre-filled with *all* data for the specified roast.
  * The user *must* be able to fill in/correct:
    * `roasted_weight_grams` (a key field).
    * `original_weight_grams` (if not set earlier).
    * `bean_id` (if not set earlier).
    * `title`, `general_notes`, `temp_measurement_method`.
  * The page should *display* the calculated `weight_loss_percentage` after `roasted_weight_grams` is entered.
  * The user should also be able to *edit or delete* individual entries from the `key_timings` and `temp_curve` arrays (e.g., "I clicked 'Yellowing' 10 seconds too late").
  * A "Save Changes" button updates the entire roast document.

#### **4.6. Review Management (TBD)**

* On the "Roast Detail" page (`/roast/<roast_id>`), there will be an "Add Review" button.
* This will show a simple form (rating, notes).
* Submitting the form will `$push` a new sub-document into the `roast`'s `reviews` array.

-----

### **5. API Endpoints (Flask Routes)**

A suggested structure for the Flask routes.

#### **5.1. HTML-Rendering Routes**

* `GET /`: Dashboard (list of roasts).
* `GET /beans`: List of beans.
* `GET /beans/add`: Show "add bean" form.
* `GET /beans/edit/<bean_id>`: Show "edit bean" form (pre-filled).
* `GET /roast/new`: Redirects to `POST /api/roast/create` and then to `/roast/live/<new_id>`.
* `GET /roast/live/<roast_id>`: The live roasting page.
* `GET /roast/detail/<roast_id>`: The read-only roast detail page.
* `GET /roast/edit/<roast_id>`: The post-roast edit form.

#### **5.2. Backend API Routes (for JavaScript `fetch`)**

* `POST /api/beans/add`: Process "add bean" form data.
* `POST /api/beans/edit/<bean_id>`: Process "edit bean" form data.
* `POST /api/beans/delete/<bean_id>`: Archive a bean (soft delete - sets `archived: true`).
* `POST /api/roast/create`: Create a new *draft* roast. Returns `{ "new_roast_id": "..." }`.
* `POST /api/roast/delete/<roast_id>`: Archive a roast (soft delete - sets `archived: true` and restores bean stock).
* `POST /api/roast/update/<roast_id>`: Save all data from the "Edit Roast" page.
* `POST /api/roast/start/<roast_id>`: Set the `roast_start_time`.
* `POST /api/roast/end/<roast_id>`: Set the `roast_end_time`.
* `POST /api/roast/add_timing/<roast_id>`: `$push` new event to `key_timings`.
* `POST /api/roast/add_event/<roast_id>`: `$push` new event to `temp_curve`.
* `POST /api/roast/add_review/<roast_id>`: `$push` new review to `reviews`.
* `POST /api/roast/update_review/<roast_id>/<review_id>`: Update an existing review.
* `POST /api/roast/delete_review/<roast_id>/<review_id>`: Delete a review from `reviews` array.
* `GET /api/temp/current`: Get current temperature from K-Type sensor. Returns JSON with temperature value or null if unavailable.
* `POST /api/roast/log_temp_local/<roast_id>`: Log temperature reading to local CSV file for detailed analysis.

-----

### **6. K-Type Temperature Sensor Integration**

The application integrates with a K-Type temperature sensor (Howie's design - K-Type Sensor V1) that provides real-time temperature readings via a local HTTP endpoint.

#### **6.1. Temperature Sensor Configuration**

* **Environment Variable:** `TEMP_SENSOR_URL`
* **Default Value:** `http://192.168.0.47/temp`
* **Response Format:**
  ```json
  {
    "temperature_celsius": 27.00,
    "temperature_fahrenheit": 80.60
  }
  ```
  Note: The code supports both `temperature_celsius` and `temperatur_celsius` field names for compatibility.

#### **6.2. Temperature Display**

* Real-time temperature display on the live roasting page (`/roast/live/<roast_id>`)
* Automatically updates every 5 seconds via polling
* Displays "Offline" when sensor is unavailable
* Only shown when roast is not finished (before `roast_end_time` is set)

#### **6.3. Temperature Polling Logic**

* Frontend polls `/api/temp/current` endpoint every 5 seconds
* Backend makes 3 consecutive requests to the sensor (100ms timeout each)
* Returns average of the two highest successful readings (rounded to integer)
* Returns `null` if fewer than 2 successful readings
* Temperature is displayed immediately in the UI (no database lag)

#### **6.4. Automatic Temperature Logging**

* When a valid temperature is retrieved and displayed:
  * Frontend immediately displays the value
  * Frontend sends the temperature to backend API to log to database
  * Creates entry in the `temp_curve` array every 5 seconds during active roast
* Only logs when:
  * Roast has started (`roast_start_time` exists)
  * Temperature value is valid (successfully retrieved from sensor)
  * User has the live roast page open (frontend is active)
* If temperature fetch fails:
  * No automatic log entry is created
  * Existing log entries are not modified
  * Display continues to show last known status

#### **6.5. Manual Event Temperature Integration**

* When user manually logs events (key timings, power changes), the system automatically includes the current temperature
* If temperature input field is empty:
  * Backend makes one request to sensor (100ms timeout)
  * Includes temperature in log entry if successful
  * Saves event without temperature if sensor unavailable
* User can manually override by entering temperature value
* Critical: Events are always saved regardless of sensor availability

#### **6.6. Final Temperature on Roast End**

* When "End Roast" button is clicked:
  * Backend fetches final temperature reading from sensor
  * Creates final entry in `temp_curve` array if successful
  * Roast ends normally even if temperature fetch fails

#### **6.7. Default Temperature Measurement Method**

* Changed from `"IR Gun"` to `"K-Type Sensor V1"` for new roasts
* Updated in `models/roast_helpers.py`:
  * `create_draft_roast()` function
  * `update_roast()` function default parameter

#### **6.8. Rate of Rise (RoR) Calculation**

* **Real-time RoR calculation** during roasting:
  * RoR = (current temperature - temperature 20 seconds ago) × 3
  * Provides °C/min measurement of temperature increase rate
  * Displayed alongside temperature on live roasting page
  * Calculated every second once 20 seconds of data is available
* **RoR Display:**
  * Shown in real-time next to temperature reading
  * Displays "--" until 20 seconds of data is collected
  * Rounded to 1 decimal place for readability
* **RoR Storage:**
  * Saved to database with temperature events in `temp_curve` array
  * New optional field: `ror` (Float) in temperature event documents
  * Only saved when temperature is logged (every 3 seconds)
* **RoR in Event Logs:**
  * Displayed in timeline on live roasting page
  * Shown in roast detail page event table as colored badge
  * Format: "RoR: X.X°C/min" next to temperature reading

#### **6.9. Local Temperature Logging**

* **Purpose:** Detailed second-by-second temperature logging for analysis
* **Storage Location:** `temp_logs/` directory in application root
* **File Format:**
  * CSV files named by roast_id: `{roast_id}.csv`
  * Header: `time_seconds,temperature`
  * One entry per second during active roast
* **API Endpoint:** `POST /api/roast/log_temp_local/<roast_id>`
* **Automatic Creation:**
  * Directory created if doesn't exist
  * New file created for each roast
  * Appends data throughout roast session
* **Use Cases:**
  * Detailed post-roast analysis
  * RoR calculations
  * Temperature curve graphing
  * Pattern recognition across roasts

#### **6.10. First Crack (FC) Time Tracking**

* **FC Time Display:**
  * When "First Crack Start" button is clicked, displays time-to-FC next to main timer
  * Format: "MM:SS (MM:SS)" where second time is FC start time
  * Shown in parentheses for clarity
* **Multiple FC Events:**
  * If multiple FC Start events are logged, displays the latest one
  * Updates display each time FC Start is clicked
* **Implementation:**
  * JavaScript tracks `fcStartTime` variable
  * Updates `fcTimeDisplay` badge element
  * Persists until roast ends

-----

### **7. Database Sync & Switch Feature**

The application supports connecting to two MongoDB databases: **local** (for home network use) and **online** (MongoDB Atlas, for remote access). Users can switch between databases and sync data between them.

#### **7.1. Settings Modal UI**

* **Settings Button:**
  * Location: Top-right corner of every page (in the navigation bar)
  * Icon: Gear (`settings` Material Icon)
  * On click: Opens the Settings Modal

* **Settings Modal Contents:**
  * **Database Switch:**
    * Radio buttons or toggle: "Local" / "Online"
    * Shows current active database with visual indicator
    * Switching triggers a page reload to use the new connection
  * **Sync Actions:**
    * Two buttons:
      * **"Sync Online → Local"** - Copies/updates data from online DB to local DB
      * **"Sync Local → Online"** - Copies/updates data from local DB to online DB
    * Each button shows loading state during sync
  * **Close Button** to dismiss the modal

#### **7.2. Sync Logic**

When syncing from Source DB → Target DB:

1. **Fetch all non-archived documents** from both `beans` and `roasts` collections in both DBs
2. **For each document in Source DB:**
   * If `_id` does NOT exist in Target DB → **Insert** (add new document)
   * If `_id` EXISTS in Target DB → **Update** (replace with source document)
3. **Track counts:**
   * `added`: Number of new documents inserted
   * `updated`: Number of existing documents updated
4. **Important:** Sync does NOT delete documents. If a document exists in Target but not in Source, it remains in Target.

#### **7.3. API Endpoints**

* `GET /api/settings/db` - Returns current database mode (`{"mode": "local" | "online"}`)
* `POST /api/settings/db` - Switch database mode
  * Body: `{"mode": "local" | "online"}`
  * Stores preference in session/cookie
  * Returns: `{"success": true, "mode": "local" | "online"}`
* `POST /api/sync/online-to-local` - Sync from online → local
  * Returns: `{"success": true, "beans": {"added": N, "updated": N}, "roasts": {"added": N, "updated": N}}`
* `POST /api/sync/local-to-online` - Sync from local → online
  * Returns: `{"success": true, "beans": {"added": N, "updated": N}, "roasts": {"added": N, "updated": N}}`

#### **7.4. Toast Notification on Sync Complete**

* On successful sync, display a toast notification with summary:
  * "Sync complete! Beans: X added, Y updated. Roasts: X added, Y updated."
* On error, display error toast:
  * "Sync failed: {error message}"

#### **7.5. Default Database & Session Behavior**

* Default database is determined by environment variable `DEFAULT_DB`
* Values: `"local"` or `"online"`
* If not set, defaults to `"local"`
* User's selection persists in Flask session cookie
* **All CRUD operations** (add/edit/delete beans, create/edit/end roasts, etc.) **use the currently selected database**
* Application dynamically references the active DB via helper functions (`get_beans_collection()`, `get_roasts_collection()`)

-----

### **8. Deployment & Environment (Render)**

* **Database:** Use a free **MongoDB Atlas** M0 cluster. The application will connect to this using a connection string.
* **Environment Variables:**
  * `FLASK_APP=app.py`
  * `FLASK_ENV=production`
  * `SECRET_KEY`: A long, random string for Flask sessions.
  * `MONGO_URI`: The full connection string for the **online** MongoDB Atlas (e.g., `mongodb+srv://<username>:<password>@cluster...`)
  * `MONGO_URI_LOCAL`: The connection string for the **local** MongoDB instance (e.g., `mongodb://localhost:27017/roastlogger`)
  * `DEFAULT_DB`: Default database to use on startup. Values: `"local"` or `"online"`. Defaults to `"local"` if not set.
  * `TEMP_SENSOR_URL`: URL of the K-Type temperature sensor endpoint (e.g., `http://192.168.0.47/temp`). Defaults to `http://192.168.0.47/temp` if not set.
* **`requirements.txt`:** Must include `Flask`, `pymongo`, `gunicorn`, `python-dotenv`, `requests`.
* **`render.yaml`:**
  * **Service Type:** Web Service
  * **Build Command:** `pip install -r requirements.txt`
  * **Start Command:** `gunicorn app:app` (assuming your Flask app instance is named `app` in `app.py`).
* **Free Plan:** Be aware the Render free plan will spin down the service after 15 minutes of inactivity, causing a ~30-second delay on the next visit. This is acceptable for a personal project.
