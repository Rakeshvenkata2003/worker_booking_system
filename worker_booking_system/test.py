from supabase import create_client, Client

# Supabase URL and key
url = "https://izuxatcswpuiybddnotk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml6dXhhdGNzd3B1aXliZGRub3RrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg5NTcxMDYsImV4cCI6MjA1NDUzMzEwNn0.F1t-KgvHcx2MrQ94-xtL9BJ7OMRwuWKMQbzhMQEEgd4"

# Create a Supabase client
supabase: Client = create_client(url, key)

def test_connection():
    try:
        # Perform a simple query to check the connection
        response = supabase.table('users').select('*').limit(1).execute()  # Select 1 record, regardless of data
        
        # Check if response is successful and data is returned
        if response.data is not None:
            print("Successfully connected to Supabase!")
            print("Response:", response.data)
        else:
            print("Connection successful, but no data found in the 'users' table.")

    except Exception as e:
        print(f"Error connecting to Supabase: {e}")

# Run the connection test
test_connection()
