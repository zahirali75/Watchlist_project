import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from parent .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL dan SUPABASE_KEY harus diisi di file .env!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
