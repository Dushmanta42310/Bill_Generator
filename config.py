import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Database Type: 'supabase', 'oracle', or 'sqlite'
# The application will default to 'supabase' if URL/Key are set, or SQLite as backup.
DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# Oracle Database Configuration
ORACLE_USER = os.environ.get('ORACLE_USER', 'system')
ORACLE_PASSWORD = os.environ.get('ORACLE_PASSWORD', 'your_password')
ORACLE_DSN = os.environ.get('ORACLE_DSN', 'localhost:1521/FREEPDB1')

# SQLite Configuration (Fallback)
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rides.db')

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'rapido_bill_generator_secret_key')
DEBUG = True
PORT = 5000
HOST = '0.0.0.0'
