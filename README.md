# Ride Invoice Studio (Rapido-Style Bill Generator)

A full-stack premium Ride Invoice Generator and Management system built to replicate the official Rapido invoices from PDF receipts. The system integrates:
1. **Interactive Real-world Maps**: OpenStreetMap + Leaflet.js with live Nominatim geocoding and OSRM road distance/time calculations.
2. **Flask REST API**: Back-end endpoints built in Python for complete ride database lifecycle.
3. **Oracle Database Connectivity**: Supports connection to Oracle Database in **Thin Mode** (via the modern `oracledb` Python driver - no Instant Client installation required).
4. **Fallback SQLite Mode**: Automatically falls back to SQLite (`rides.db`) when Oracle Database credentials are not configured or the instance is offline, enabling immediate out-of-the-box local testing.
5. **Print Layouts**: High-fidelity CSS sheets styled matching the official Rapido receipts, fully compatible with browser print functions to print/save as PDF.

---

## Technical Stack & Libraries

- **Backend**: Python 3.x, Flask (3.1.x)
- **Database Driver**: `oracledb` (4.x) / `sqlite3`
- **Frontend**: HTML5, Vanilla CSS3 (custom responsive slate theme, print layouts), Vanilla Javascript (ES6)
- **Mapping Libraries**: Leaflet.js (v1.9.4 CDN)
- **APIs Used**: OpenStreetMap Tiles, OSRM Routing Engine (Free), Nominatim Geocoder (Free)

---

## Installation & Setup

1. **Clone/Navigate to the workspace**:
   Make sure you are in the application folder (`d:\SOFTWERE\Bill_Generator`).

2. **Verify Python Packages**:
   The required packages (`flask` and `oracledb`) are already installed on your system. If needed, you can install/reinstall them via pip:
   ```bash
   pip install flask oracledb
   ```

3. **Configure Database Settings**:
   Open [config.py](file:///d:/SOFTWERE/Bill_Generator/config.py) in your editor. By default, the database type is set to `'sqlite'`:
   ```python
   DB_TYPE = 'sqlite'
   ```
   To use your Oracle Database, change this setting to `'oracle'` and input your connection details:
   ```python
   DB_TYPE = 'oracle'
   ORACLE_USER = 'your_username'
   ORACLE_PASSWORD = 'your_password'
   ORACLE_DSN = 'localhost:1521/FREEPDB1'
   ```
   *Note: If Oracle connection fails at startup, the console will print a warning and automatically activate the SQLite fallback, keeping the site fully functional.*

4. **Running the Application**:
   Propose or execute the command:
   ```bash
   python app.py
   ```
   The Flask developer server will start at `http://localhost:5000`.

---

## Features Walkthrough

1. **Dashboard Interface**:
   - **Sliders / Forms**: Fill in passenger name, driver name, vehicle number, select ride time, state, and payment method.
   - **Interactive Map**: Click on the map to define the Pickup (P) and Drop (D) points, or search addresses directly. The road path is drawn automatically, and distance + duration are computed and loaded.
   - **Override Switch**: Toggle this switch to input specific values (like the ones from your PDF) manually. Taxes are calculated automatically on the fly.
   - **Save Ride**: Saves all metadata and computed charges to the database (Oracle/SQLite).
2. **Three Invoices Sheets (Tabs)**:
   - **Payment Summary (Tab 1)**: Replicates Page 1 of the PDF, displaying route statistics, green/red pick/drop points, bill breakdown, and QR Pay container. Includes a live mini-map showing the selected route.
   - **TSP Tax Invoice (Tab 2)**: Replicates Page 2 of the PDF, showing GST split (2.5% CGST + 2.5% SGST) for the driver's service.
   - **Roppen Tax Invoice (Tab 3)**: Replicates Page 3 of the PDF, showcasing GST split (9% CGST + 9% SGST) for booking services, alongside a mock QR code and company footnotes.
3. **Print Tab Action**:
   - Pressing "Print Tab" launches the print window. The stylesheet hides the configuration panels, sidebars, and active controls, printing **only** the selected sheet in pristine A4 white paper design.
4. **Historical Database Log**:
   - Lists past rides saved in the database.
   - Search/Filter records instantly by customer, captain, or ride ID.
   - Select the "View" (eye) icon to reload any past ride back into the interactive visualizer and print tabs.
   - Select the "Delete" (trash) icon to remove records from the database.
