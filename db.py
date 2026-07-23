import sqlite3
import datetime
import traceback
import oracledb
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
                
            print("SQLite database initialized successfully.")
            
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

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
