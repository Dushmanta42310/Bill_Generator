import sqlite3
import datetime
import traceback
import config
from supabase import create_client, Client

# Initialize Supabase client lazily
_supabase_client = None

def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        if config.SUPABASE_URL and config.SUPABASE_KEY:
            _supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        else:
            raise ValueError("Supabase URL and Key must be set in config.py or .env file.")
    return _supabase_client

def get_db_connection():
    """
    Establishes and returns a database connection based on config.
    Falls back to SQLite if Oracle DB or Supabase connection fails or is not selected.
    Returns:
        conn: The database connection object (supabase client, oracledb.Connection, or sqlite3.Connection)
        db_type: A string, 'supabase', 'oracle', or 'sqlite'
    """
    if config.DB_TYPE == 'supabase':
        try:
            client = get_supabase_client()
            return client, 'supabase'
        except Exception as e:
            print(f"Warning: Failed to connect to Supabase. Falling back to SQLite. Error: {e}")
            conn = sqlite3.connect(config.SQLITE_DB_PATH)
            return conn, 'sqlite'
    elif config.DB_TYPE == 'oracle':
        try:
            import oracledb
            # Connect to Oracle Database in Thin mode
            conn = oracledb.connect(
                user=config.ORACLE_USER,
                password=config.ORACLE_PASSWORD,
                dsn=config.ORACLE_DSN
            )
            return conn, 'oracle'
        except Exception as e:
            print(f"Warning: Failed to connect to Oracle Database. Falling back to SQLite. Error: {e}")
            conn = sqlite3.connect(config.SQLITE_DB_PATH)
            return conn, 'sqlite'
    else:
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        return conn, 'sqlite'

def init_db():
    """
    Initializes the database schema.
    For Supabase, verify table connectivity.
    For Oracle/SQLite, creates the RIDES table and indexes.
    """
    conn, db_type = get_db_connection()
    if db_type == 'supabase':
        try:
            # Try a test select query to verify Table access
            conn.table('rides').select('ride_id').limit(1).execute()
            print("Supabase connected and 'rides' table is accessible.")
        except Exception as e:
            print(f"Warning: Supabase table 'rides' could not be accessed: {e}")
            print("Please make sure you have run the schema script in the Supabase SQL Editor.")
    
    # Always ensure local SQLite DB is initialized as fallback
    try:
        sqlite_conn = sqlite3.connect(config.SQLITE_DB_PATH)
        sqlite_cur = sqlite_conn.cursor()
        sqlite_cur.execute("""
            CREATE TABLE IF NOT EXISTS RIDES (
                RIDE_ID TEXT PRIMARY KEY,
                CUSTOMER_NAME TEXT NOT NULL,
                TIME_OF_RIDE TEXT NOT NULL,
                DISTANCE_KM REAL NOT NULL,
                DURATION_MIN REAL NOT NULL,
                PICKUP_ADDRESS TEXT NOT NULL,
                DROP_ADDRESS TEXT NOT NULL,
                TOTAL_AMOUNT REAL NOT NULL,
                RIDE_CHARGE REAL NOT NULL,
                BOOKING_FEES REAL NOT NULL,
                CONVENIENCE_CHARGES REAL NOT NULL,
                GATEWAY_CHARGES REAL NOT NULL,
                PAYMENT_METHOD TEXT NOT NULL,
                CAPTAIN_NAME TEXT NOT NULL,
                VEHICLE_NUMBER TEXT NOT NULL,
                INVOICE_NO TEXT NOT NULL,
                STATE TEXT NOT NULL,
                CAPTAIN_FEE REAL NOT NULL,
                RIDE_CGST REAL NOT NULL,
                RIDE_SGST REAL NOT NULL,
                BOOKING_CGST REAL NOT NULL,
                BOOKING_SGST REAL NOT NULL
            )
        """)
        sqlite_cur.execute("CREATE INDEX IF NOT EXISTS IDX_RIDES_CUSTOMER_NAME ON RIDES(CUSTOMER_NAME)")
        sqlite_cur.execute("CREATE INDEX IF NOT EXISTS IDX_RIDES_TIME ON RIDES(TIME_OF_RIDE)")
        
        sqlite_cur.execute("""
            CREATE TABLE IF NOT EXISTS TRAVEL_LOGS (
                LOG_ID TEXT PRIMARY KEY,
                TRAVEL_DATE TEXT NOT NULL,
                START_TIME TEXT,
                END_TIME TEXT,
                LOG_TYPE TEXT NOT NULL,
                TITLE TEXT NOT NULL,
                SUBTITLE TEXT,
                MODE TEXT,
                DISTANCE_KM REAL DEFAULT 0.0,
                DURATION_MIN REAL DEFAULT 0.0,
                PICKUP_ADDRESS TEXT,
                DROP_ADDRESS TEXT,
                PICKUP_LAT REAL,
                PICKUP_LNG REAL,
                DROP_LAT REAL,
                DROP_LNG REAL,
                RIDE_ID TEXT
            )
        """)
        sqlite_cur.execute("CREATE INDEX IF NOT EXISTS IDX_TRAVEL_DATE ON TRAVEL_LOGS(TRAVEL_DATE)")
        sqlite_conn.commit()
        sqlite_cur.close()
        sqlite_conn.close()
    except Exception as sq_err:
        print(f"SQLite init note: {sq_err}")

    if db_type == 'supabase':
        seed_sample_timeline()
        return

    cursor = conn.cursor()
    try:
        if db_type == 'oracle':
            # Create table in Oracle
            try:
                cursor.execute("""
                    CREATE TABLE RIDES (
                        RIDE_ID VARCHAR2(30) PRIMARY KEY,
                        CUSTOMER_NAME VARCHAR2(100) NOT NULL,
                        TIME_OF_RIDE TIMESTAMP NOT NULL,
                        DISTANCE_KM NUMBER(5, 2) NOT NULL,
                        DURATION_MIN NUMBER(5, 2) NOT NULL,
                        PICKUP_ADDRESS VARCHAR2(500) NOT NULL,
                        DROP_ADDRESS VARCHAR2(500) NOT NULL,
                        TOTAL_AMOUNT NUMBER(8, 2) NOT NULL,
                        RIDE_CHARGE NUMBER(8, 2) NOT NULL,
                        BOOKING_FEES NUMBER(8, 2) NOT NULL,
                        CONVENIENCE_CHARGES NUMBER(8, 2) NOT NULL,
                        GATEWAY_CHARGES NUMBER(8, 2) NOT NULL,
                        PAYMENT_METHOD VARCHAR2(50) NOT NULL,
                        CAPTAIN_NAME VARCHAR2(100) NOT NULL,
                        VEHICLE_NUMBER VARCHAR2(30) NOT NULL,
                        INVOICE_NO VARCHAR2(30) NOT NULL,
                        STATE VARCHAR2(50) NOT NULL,
                        CAPTAIN_FEE NUMBER(8, 2) NOT NULL,
                        RIDE_CGST NUMBER(8, 2) NOT NULL,
                        RIDE_SGST NUMBER(8, 2) NOT NULL,
                        BOOKING_CGST NUMBER(8, 2) NOT NULL,
                        BOOKING_SGST NUMBER(8, 2) NOT NULL
                    )
                """)
                print("Oracle table RIDES created.")
            except Exception as e:
                if 'ORA-00955' in str(e):
                    print("Oracle table RIDES already exists.")
                else:
                    raise

            # Create Indexes in Oracle
            try:
                cursor.execute("CREATE INDEX IDX_RIDES_CUSTOMER_NAME ON RIDES(CUSTOMER_NAME)")
                cursor.execute("CREATE INDEX IDX_RIDES_TIME ON RIDES(TIME_OF_RIDE)")
                print("Oracle indexes created.")
            except Exception as e:
                if 'ORA-00955' in str(e):
                    print("Oracle indexes already exist.")
                else:
                    raise
        else:
            # Create table and indexes in SQLite
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS RIDES (
                    RIDE_ID TEXT PRIMARY KEY,
                    CUSTOMER_NAME TEXT NOT NULL,
                    TIME_OF_RIDE TEXT NOT NULL,
                    DISTANCE_KM REAL NOT NULL,
                    DURATION_MIN REAL NOT NULL,
                    PICKUP_ADDRESS TEXT NOT NULL,
                    DROP_ADDRESS TEXT NOT NULL,
                    TOTAL_AMOUNT REAL NOT NULL,
                    RIDE_CHARGE REAL NOT NULL,
                    BOOKING_FEES REAL NOT NULL,
                    CONVENIENCE_CHARGES REAL NOT NULL,
                    GATEWAY_CHARGES REAL NOT NULL,
                    PAYMENT_METHOD TEXT NOT NULL,
                    CAPTAIN_NAME TEXT NOT NULL,
                    VEHICLE_NUMBER TEXT NOT NULL,
                    INVOICE_NO TEXT NOT NULL,
                    STATE TEXT NOT NULL,
                    CAPTAIN_FEE REAL NOT NULL,
                    RIDE_CGST REAL NOT NULL,
                    RIDE_SGST REAL NOT NULL,
                    BOOKING_CGST REAL NOT NULL,
                    BOOKING_SGST REAL NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS IDX_RIDES_CUSTOMER_NAME ON RIDES(CUSTOMER_NAME)")
            cursor.execute("CREATE INDEX IF NOT EXISTS IDX_RIDES_TIME ON RIDES(TIME_OF_RIDE)")
            
            # Automated SQLite migration check for GATEWAY_CHARGES column
            cursor.execute("PRAGMA table_info(RIDES)")
            existing_columns = [col_info[1] for col_info in cursor.fetchall()]
            if 'GATEWAY_CHARGES' not in existing_columns:
                cursor.execute("ALTER TABLE RIDES ADD COLUMN GATEWAY_CHARGES REAL NOT NULL DEFAULT 0.00")
                print("SQLite RIDES table migrated: added GATEWAY_CHARGES column.")

            # Create TRAVEL_LOGS table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS TRAVEL_LOGS (
                    LOG_ID TEXT PRIMARY KEY,
                    TRAVEL_DATE TEXT NOT NULL,
                    START_TIME TEXT,
                    END_TIME TEXT,
                    LOG_TYPE TEXT NOT NULL,
                    TITLE TEXT NOT NULL,
                    SUBTITLE TEXT,
                    MODE TEXT,
                    DISTANCE_KM REAL DEFAULT 0.0,
                    DURATION_MIN REAL DEFAULT 0.0,
                    PICKUP_ADDRESS TEXT,
                    DROP_ADDRESS TEXT,
                    PICKUP_LAT REAL,
                    PICKUP_LNG REAL,
                    DROP_LAT REAL,
                    DROP_LNG REAL,
                    RIDE_ID TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS IDX_TRAVEL_DATE ON TRAVEL_LOGS(TRAVEL_DATE)")
            print("SQLite database initialized successfully.")
            
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()
    
    # Seed sample timeline data for demo
    seed_sample_timeline()

def parse_row(row, columns, db_type):
    """Helper to convert a DB row tuple to a dictionary."""
    data = dict(zip(columns, row))
    
    # Standardize time representation to ISO string
    if isinstance(data.get('TIME_OF_RIDE'), datetime.datetime):
        data['TIME_OF_RIDE'] = data['TIME_OF_RIDE'].isoformat()
    elif isinstance(data.get('TIME_OF_RIDE'), str):
        pass
        
    # Convert numerical column names to lowercase for frontend consistency
    return {k.lower(): v for k, v in data.items()}

def get_columns(cursor, db_type):
    """Retrieve column names from cursor descriptor."""
    return [col[0] for col in cursor.description]

def save_ride(ride_data):
    """
    Saves a ride dictionary to the database.
    """
    conn, db_type = get_db_connection()
    
    # Clean and parse date
    time_val = ride_data['time_of_ride']
    if isinstance(time_val, str):
        try:
            # Standard ISO format parsing
            if time_val.endswith('Z'):
                time_val = time_val[:-1] + '+00:00'
            dt = datetime.datetime.fromisoformat(time_val)
        except Exception:
            # Fallback to current time if parsing fails
            dt = datetime.datetime.now()
    else:
        dt = time_val

    # Standardize bind time representation
    bind_time = dt if db_type == 'oracle' else dt.isoformat()

    if db_type == 'supabase':
        payload = {
            'ride_id': ride_data['ride_id'],
            'customer_name': ride_data['customer_name'],
            'time_of_ride': bind_time,
            'distance_km': float(ride_data['distance_km']),
            'duration_min': float(ride_data['duration_min']),
            'pickup_address': ride_data['pickup_address'],
            'drop_address': ride_data['drop_address'],
            'total_amount': float(ride_data['total_amount']),
            'ride_charge': float(ride_data['ride_charge']),
            'booking_fees': float(ride_data['booking_fees']),
            'convenience_charges': float(ride_data['convenience_charges']),
            'gateway_charges': float(ride_data['gateway_charges']),
            'payment_method': ride_data['payment_method'],
            'captain_name': ride_data['captain_name'],
            'vehicle_number': ride_data['vehicle_number'],
            'invoice_no': ride_data['invoice_no'],
            'state': ride_data['state'],
            'captain_fee': float(ride_data['captain_fee']),
            'ride_cgst': float(ride_data['ride_cgst']),
            'ride_sgst': float(ride_data['ride_sgst']),
            'booking_cgst': float(ride_data['booking_cgst']),
            'booking_sgst': float(ride_data['booking_sgst'])
        }
        try:
            conn.table('rides').insert(payload).execute()
            return True
        except Exception as e:
            print(f"Error saving ride to Supabase: {e}")
            traceback.print_exc()
            raise e

    # SQLite / Oracle Insert
    cursor = conn.cursor()
    sql = """
        INSERT INTO RIDES (
            RIDE_ID, CUSTOMER_NAME, TIME_OF_RIDE, DISTANCE_KM, DURATION_MIN,
            PICKUP_ADDRESS, DROP_ADDRESS, TOTAL_AMOUNT, RIDE_CHARGE, BOOKING_FEES,
            CONVENIENCE_CHARGES, GATEWAY_CHARGES, PAYMENT_METHOD, CAPTAIN_NAME, VEHICLE_NUMBER,
            INVOICE_NO, STATE, CAPTAIN_FEE, RIDE_CGST, RIDE_SGST, BOOKING_CGST, BOOKING_SGST
        ) VALUES (
            :ride_id, :customer_name, :time_of_ride, :distance_km, :duration_min,
            :pickup_address, :drop_address, :total_amount, :ride_charge, :booking_fees,
            :convenience_charges, :gateway_charges, :payment_method, :captain_name, :vehicle_number,
            :invoice_no, :state, :captain_fee, :ride_cgst, :ride_sgst, :booking_cgst, :booking_sgst
        )
    """

    params = {
        'ride_id': ride_data['ride_id'],
        'customer_name': ride_data['customer_name'],
        'time_of_ride': bind_time,
        'distance_km': float(ride_data['distance_km']),
        'duration_min': float(ride_data['duration_min']),
        'pickup_address': ride_data['pickup_address'],
        'drop_address': ride_data['drop_address'],
        'total_amount': float(ride_data['total_amount']),
        'ride_charge': float(ride_data['ride_charge']),
        'booking_fees': float(ride_data['booking_fees']),
        'convenience_charges': float(ride_data['convenience_charges']),
        'gateway_charges': float(ride_data['gateway_charges']),
        'payment_method': ride_data['payment_method'],
        'captain_name': ride_data['captain_name'],
        'vehicle_number': ride_data['vehicle_number'],
        'invoice_no': ride_data['invoice_no'],
        'state': ride_data['state'],
        'captain_fee': float(ride_data['captain_fee']),
        'ride_cgst': float(ride_data['ride_cgst']),
        'ride_sgst': float(ride_data['ride_sgst']),
        'booking_cgst': float(ride_data['booking_cgst']),
        'booking_sgst': float(ride_data['booking_sgst'])
    }

    try:
        cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving ride: {e}")
        traceback.print_exc()
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_all_rides():
    """
    Retrieves all rides, ordered by time of ride descending.
    """
    conn, db_type = get_db_connection()
    if db_type == 'supabase':
        try:
            response = conn.table('rides').select('*').order('time_of_ride', desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching rides from Supabase: {e}")
            return []

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM RIDES ORDER BY TIME_OF_RIDE DESC")
        columns = get_columns(cursor, db_type)
        rows = cursor.fetchall()
        return [parse_row(row, columns, db_type) for row in rows]
    except Exception as e:
        print(f"Error fetching rides: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_ride_by_id(ride_id):
    """
    Fetches a specific ride by its ID.
    """
    conn, db_type = get_db_connection()
    if db_type == 'supabase':
        try:
            response = conn.table('rides').select('*').eq('ride_id', ride_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching ride by ID from Supabase: {e}")
            return None

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM RIDES WHERE RIDE_ID = :ride_id", {'ride_id': ride_id})
        columns = get_columns(cursor, db_type)
        row = cursor.fetchone()
        if row:
            return parse_row(row, columns, db_type)
        return None
    except Exception as e:
        print(f"Error fetching ride by ID: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def delete_ride(ride_id):
    """
    Deletes a specific ride from the database.
    """
    conn, db_type = get_db_connection()
    if db_type == 'supabase':
        try:
            conn.table('rides').delete().eq('ride_id', ride_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting ride from Supabase: {e}")
            return False

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM RIDES WHERE RIDE_ID = :ride_id", {'ride_id': ride_id})
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting ride: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

# Timeline functions

def get_timeline_by_date(travel_date):
    """
    Retrieves all travel logs for a specific date (YYYY-MM-DD).
    """
    conn, db_type = get_db_connection()
    if db_type == 'supabase':
        try:
            response = conn.table('travel_logs').select('*').eq('travel_date', travel_date).order('start_time').execute()
            return response.data
        except Exception as e:
            # Fallback to SQLite if table not present in Supabase
            conn = sqlite3.connect(config.SQLITE_DB_PATH)
            db_type = 'sqlite'

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM TRAVEL_LOGS WHERE TRAVEL_DATE = :travel_date ORDER BY START_TIME ASC", {'travel_date': travel_date})
        columns = get_columns(cursor, db_type)
        rows = cursor.fetchall()
        return [parse_row(row, columns, db_type) for row in rows]
    except Exception as e:
        print(f"Error fetching timeline for date {travel_date}: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def save_travel_log(log_data):
    """
    Saves or updates a travel log record.
    """
    conn, db_type = get_db_connection()
    log_id = log_data.get('log_id') or f"LOG_{int(datetime.datetime.now().timestamp() * 1000)}"
    
    payload = {
        'log_id': log_id,
        'travel_date': log_data['travel_date'],
        'start_time': log_data.get('start_time', ''),
        'end_time': log_data.get('end_time', ''),
        'log_type': log_data.get('log_type', 'travel'),
        'title': log_data['title'],
        'subtitle': log_data.get('subtitle', ''),
        'mode': log_data.get('mode', 'car'),
        'distance_km': float(log_data.get('distance_km', 0.0)),
        'duration_min': float(log_data.get('duration_min', 0.0)),
        'pickup_address': log_data.get('pickup_address', ''),
        'drop_address': log_data.get('drop_address', ''),
        'pickup_lat': float(log_data['pickup_lat']) if log_data.get('pickup_lat') is not None else None,
        'pickup_lng': float(log_data['pickup_lng']) if log_data.get('pickup_lng') is not None else None,
        'drop_lat': float(log_data['drop_lat']) if log_data.get('drop_lat') is not None else None,
        'drop_lng': float(log_data['drop_lng']) if log_data.get('drop_lng') is not None else None,
        'ride_id': log_data.get('ride_id', '')
    }

    if db_type == 'supabase':
        try:
            conn.table('travel_logs').upsert(payload).execute()
            return log_id
        except Exception as e:
            # Fallback to SQLite
            conn = sqlite3.connect(config.SQLITE_DB_PATH)
            db_type = 'sqlite'

    cursor = conn.cursor()
    sql = """
        INSERT OR REPLACE INTO TRAVEL_LOGS (
            LOG_ID, TRAVEL_DATE, START_TIME, END_TIME, LOG_TYPE, TITLE, SUBTITLE,
            MODE, DISTANCE_KM, DURATION_MIN, PICKUP_ADDRESS, DROP_ADDRESS,
            PICKUP_LAT, PICKUP_LNG, DROP_LAT, DROP_LNG, RIDE_ID
        ) VALUES (
            :log_id, :travel_date, :start_time, :end_time, :log_type, :title, :subtitle,
            :mode, :distance_km, :duration_min, :pickup_address, :drop_address,
            :pickup_lat, :pickup_lng, :drop_lat, :drop_lng, :ride_id
        )
    """
    try:
        cursor.execute(sql, payload)
        conn.commit()
        return log_id
    except Exception as e:
        print(f"Error saving travel log: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def delete_travel_log(log_id):
    """
    Deletes a specific travel log record.
    """
    conn, db_type = get_db_connection()
    if db_type == 'supabase':
        try:
            conn.table('travel_logs').delete().eq('log_id', log_id).execute()
            return True
        except Exception as e:
            # Fallback to SQLite
            conn = sqlite3.connect(config.SQLITE_DB_PATH)
            db_type = 'sqlite'

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM TRAVEL_LOGS WHERE LOG_ID = :log_id", {'log_id': log_id})
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting travel log: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_timeline_insights(travel_date):
    """
    Computes routine travel insights & stats for a given date.
    """
    logs = get_timeline_by_date(travel_date)
    total_dist = 0.0
    total_dur = 0.0
    mode_stats = {}
    stops_count = 0
    travel_legs_count = 0

    for log in logs:
        dist = float(log.get('distance_km') or 0.0)
        dur = float(log.get('duration_min') or 0.0)
        total_dist += dist
        total_dur += dur
        
        if log.get('log_type') == 'stop':
            stops_count += 1
        else:
            travel_legs_count += 1
            mode = log.get('mode') or 'car'
            if mode not in mode_stats:
                mode_stats[mode] = {'dist': 0.0, 'dur': 0.0, 'count': 0}
            mode_stats[mode]['dist'] += dist
            mode_stats[mode]['dur'] += dur
            mode_stats[mode]['count'] += 1

    return {
        'date': travel_date,
        'total_distance_km': round(total_dist, 2),
        'total_duration_min': round(total_dur, 2),
        'stops_count': stops_count,
        'travel_legs_count': travel_legs_count,
        'mode_breakdown': mode_stats
    }

def get_all_timeline_places():
    """
    Retrieves unique stop places saved across all timeline entries.
    """
    conn, db_type = get_db_connection()
    if db_type == 'supabase':
        try:
            res = conn.table('travel_logs').select('title, subtitle, pickup_address, pickup_lat, pickup_lng, travel_date').eq('log_type', 'stop').execute()
            return res.data
        except Exception:
            conn = sqlite3.connect(config.SQLITE_DB_PATH)
            db_type = 'sqlite'

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT TITLE, SUBTITLE, PICKUP_ADDRESS, PICKUP_LAT, PICKUP_LNG, TRAVEL_DATE FROM TRAVEL_LOGS WHERE LOG_TYPE = 'stop' ORDER BY TRAVEL_DATE DESC")
        columns = get_columns(cursor, db_type)
        rows = cursor.fetchall()
        return [parse_row(row, columns, db_type) for row in rows]
    except Exception as e:
        print(f"Error fetching timeline places: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def seed_sample_timeline():
    """
    Seeds initial sample daily timeline records matching today's date and 2026-07-01 if no logs exist.
    """
    try:
        today_str = datetime.date.today().isoformat()
        dates_to_seed = ['2026-07-01', today_str]
        
        for t_date in dates_to_seed:
            existing = get_timeline_by_date(t_date)
            if existing:
                continue
                
            prefix = t_date.replace('-', '')
            sample_logs = [
                {
                    'log_id': f'LOG_{prefix}_01',
                    'travel_date': t_date,
                    'start_time': '09:00 AM',
                    'end_time': '09:27 AM',
                    'log_type': 'stop',
                    'title': 'Arun Pal',
                    'subtitle': '3/503, Sector 3, Vasundhara, Ghaziabad, UP',
                    'mode': 'other',
                    'distance_km': 0.0,
                    'duration_min': 27.0,
                    'pickup_address': '3/503, Sector 3, Vasundhara, Ghaziabad, UP',
                    'pickup_lat': 28.6644,
                    'pickup_lng': 77.3601
                },
                {
                    'log_id': f'LOG_{prefix}_02',
                    'travel_date': t_date,
                    'start_time': '09:27 AM',
                    'end_time': '09:41 AM',
                    'log_type': 'travel',
                    'title': 'Missing travel',
                    'subtitle': 'Unconfirmed travel leg',
                    'mode': 'missing',
                    'distance_km': 5.1,
                    'duration_min': 14.0,
                    'pickup_address': 'Sector 3, Vasundhara, Ghaziabad',
                    'drop_address': 'Metro Station Vaishali',
                    'pickup_lat': 28.6644,
                    'pickup_lng': 77.3601,
                    'drop_lat': 28.6472,
                    'drop_lng': 77.3400
                },
                {
                    'log_id': f'LOG_{prefix}_03',
                    'travel_date': t_date,
                    'start_time': '09:41 AM',
                    'end_time': '09:48 AM',
                    'log_type': 'stop',
                    'title': 'Vaishali',
                    'subtitle': 'Metro Station Vaishali, Madan Mohan Malviya Marg',
                    'mode': 'other',
                    'distance_km': 0.0,
                    'duration_min': 7.0,
                    'pickup_address': 'Metro Station Vaishali, Madan Mohan Malviya Marg',
                    'pickup_lat': 28.6472,
                    'pickup_lng': 77.3400
                },
                {
                    'log_id': f'LOG_{prefix}_04',
                    'travel_date': t_date,
                    'start_time': '09:48 AM',
                    'end_time': '11:23 AM',
                    'log_type': 'travel',
                    'title': 'Train Transit',
                    'subtitle': 'Blue Line Metro Leg 1',
                    'mode': 'train',
                    'distance_km': 42.0,
                    'duration_min': 95.0,
                    'pickup_address': 'Metro Station Vaishali',
                    'drop_address': 'Noida Sector 62',
                    'pickup_lat': 28.6472,
                    'pickup_lng': 77.3400,
                    'drop_lat': 28.6250,
                    'drop_lng': 77.3700
                },
                {
                    'log_id': f'LOG_{prefix}_05',
                    'travel_date': t_date,
                    'start_time': '01:15 PM',
                    'end_time': '02:30 PM',
                    'log_type': 'travel',
                    'title': 'Train Transit',
                    'subtitle': 'Intercity Line Leg 2',
                    'mode': 'train',
                    'distance_km': 42.0,
                    'duration_min': 75.0,
                    'pickup_address': 'Noida Sector 62',
                    'drop_address': 'Faridabad Railway Station',
                    'pickup_lat': 28.6250,
                    'pickup_lng': 77.3700,
                    'drop_lat': 28.4089,
                    'drop_lng': 77.3178
                },
                {
                    'log_id': f'LOG_{prefix}_06',
                    'travel_date': t_date,
                    'start_time': '04:30 PM',
                    'end_time': '05:13 PM',
                    'log_type': 'travel',
                    'title': 'Car Ride',
                    'subtitle': 'Expressway Drive',
                    'mode': 'car',
                    'distance_km': 25.0,
                    'duration_min': 43.0,
                    'pickup_address': 'Faridabad',
                    'drop_address': 'Godrej Nature Plus, Gurgaon',
                    'pickup_lat': 28.4089,
                    'pickup_lng': 77.3178,
                    'drop_lat': 28.3800,
                    'drop_lng': 77.0500
                },
                {
                    'log_id': f'LOG_{prefix}_07',
                    'travel_date': t_date,
                    'start_time': '05:13 PM',
                    'end_time': '08:00 PM',
                    'log_type': 'stop',
                    'title': 'Godrej Nature Plus, Gurgaon',
                    'subtitle': 'Sohna Road, Gurgaon, Haryana',
                    'mode': 'other',
                    'distance_km': 0.0,
                    'duration_min': 167.0,
                    'pickup_address': 'Godrej Nature Plus, Gurgaon',
                    'pickup_lat': 28.3800,
                    'pickup_lng': 77.0500
                }
            ]
            
            for item in sample_logs:
                save_travel_log(item)
            print(f"Sample timeline logs for {t_date} seeded successfully.")
    except Exception as e:
        print(f"Error seeding timeline sample data: {e}")

