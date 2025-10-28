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
  "temp_measurement_method": "String", // e.g., "K-Type (Bean)", "IR Gun (Drum)"
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
      "fan_setting": "Integer", // e.g., 1-5
      "power_setting": "Integer" // e.g., 1-10 or 1-100%
    }
  ],
  
  "general_notes": "String", // General notes for the whole roast
  
  // ----- Reviews (Embedded) -----
  "reviews": [
    // Array of embedded review documents
    {
      "_id": "ObjectId", // Unique ID for the review
      "rating": "Integer", // e.g., 1-5
      "notes": "String", // Tasting notes, brew method, etc.
      "review_date": "Date",
      "created_at": "Date",
      "updated_at": "Date"
    }
  ],
  
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
  * **On Roast Delete:** When a roast is deleted, the backend must find the `bean` and **increment** (restore) its `stock_grams` by the roast's `original_weight_grams`.
    * `db.beans.updateOne({_id: bean_id}, {$inc: {stock_grams: original_weight}})`
  * **On Roast Edit:** If a roast's `original_weight_grams` is *changed*, the backend must calculate the *difference* from the old weight and apply that difference to the `bean`'s stock.

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
2. **Pre-Roast Setup:**
      * On this page, the user sees:
          * A dropdown to select a **Bean** (populated from the `beans` collection).
          * An input for **Original Weight (grams)**.
          * *Note:* These can be set now or later in the "Edit" screen.
3. **Roasting:**
      * **"Start Roast" Button:**
          * *Frontend:* Starts an on-screen timer (e.g., `00:00`).
          * *Backend Call:* Sends an API request to set the `roast_start_time` to `datetime.now()` for this `roast_id`.
      * **Event Logging (Buttons):**
          * A set of buttons: "Mark Yellowing", "Mark FC Start", "Mark FC End", "Mark SC Start", "Mark Drop".
          * *Action:* Clicking a button gets the current timer value (in seconds) and sends an API request to `$push` a new sub-document to the `key_timings` array.
          * *Example:* `POST /api/roast/add_timing/<roast_id>` with JSON body: `{"event_name": "First Crack Start", "time_seconds": 542}`.
      * **Data Entry (Form):**
          * A small form with inputs for: **Temperature**, **Fan Setting**, **Power Setting**.
          * An "Add Event" button.
          * *Action:* Clicking gets the current timer value and form values. Sends an API request to `$push` a new sub-document to the `temp_curve` array.
          * *Example:* `POST /api/roast/add_event/<roast_id>` with JSON body: `{"time_seconds": 545, "temperature": 190.5, "fan_setting": 3, "power_setting": 4}`.
      * **Live Display:**
          * The page should have two "log" areas that update via JavaScript as events are added, showing the `key_timings` and `temp_curve` data just submitted.
4. **Ending the Roast:**
      * **"End Roast" Button:**
          * *Frontend:* Stops the on-screen timer.
          * *Backend Call:* Sends an API request to set the `roast_end_time` to `datetime.now()`.
          * *Action:* The user is then redirected to the "Edit Roast" page to fill in post-roast details.

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
* `POST /api/beans/delete/<bean_id>`: Delete a bean.
* `POST /api/roast/create`: Create a new *draft* roast. Returns `{ "new_roast_id": "..." }`.
* `POST /api/roast/delete/<roast_id>`: Delete a roast (triggers stock-return logic).
* `POST /api/roast/update/<roast_id>`: Save all data from the "Edit Roast" page.
* `POST /api/roast/start/<roast_id>`: Set the `roast_start_time`.
* `POST /api/roast/end/<roast_id>`: Set the `roast_end_time`.
* `POST /api/roast/add_timing/<roast_id>`: `$push` new event to `key_timings`.
* `POST /api/roast/add_event/<roast_id>`: `$push` new event to `temp_curve`.
* `POST /api/roast/add_review/<roast_id>`: `$push` new review to `reviews`.

-----

### **6. Deployment & Environment (Render)**

* **Database:** Use a free **MongoDB Atlas** M0 cluster. The application will connect to this using a connection string.
* **Environment Variables:**
  * `FLASK_APP=app.py`
  * `FLASK_ENV=production`
  * `SECRET_KEY`: A long, random string for Flask sessions.
  * `MONGO_URI`: The full connection string from MongoDB Atlas, including username and password. (e.g., `mongodb+srv://<username>:<password>@cluster...`)
* **`requirements.txt`:** Must include `Flask`, `pymongo`, `gunicorn`, `python-dotenv`.
* **`render.yaml`:**
  * **Service Type:** Web Service
  * **Build Command:** `pip install -r requirements.txt`
  * **Start Command:** `gunicorn app:app` (assuming your Flask app instance is named `app` in `app.py`).
* **Free Plan:** Be aware the Render free plan will spin down the service after 15 minutes of inactivity, causing a \~30-second delay on the next visit. This is acceptable for a personal project.
