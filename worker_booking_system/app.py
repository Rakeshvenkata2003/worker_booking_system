from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client, Client
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Supabase Connection
url = "https://acwagsjybyeghfsevjtu.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjd2Fnc2p5YnllZ2hmc2V2anR1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzkxMTk0NTcsImV4cCI6MjA1NDY5NTQ1N30.weEd8Gb31fN_Krv_jdyfV7O39l54VUGh33u-Ale3X-0"
supabase: Client = create_client(url, key)

@app.route('/')
def home():
    return render_template('index.html')

# Routes
# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        role = request.form['role']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        if role == 'user':
            door_no = request.form['doorNo']
            street = request.form['street']
            city = request.form['city']
            address = f"{door_no}, {street}, {city}"

            # Insert into Users table
            supabase.table('users').insert({
                "name": name,
                "email": email,
                "password": hashed_password,
                "address": address
            }).execute()

        elif role == 'worker':
            profession = request.form['profession']
            hourly_charge = request.form['hourlyCharge']
            worker_city = request.form['workerCity']

            # Insert into Workers table
            supabase.table('workers').insert({
                "name": name,
                "email": email,
                "password": hashed_password,
                "profession": profession,
                "hourly_charge": hourly_charge,
                "city": worker_city
            }).execute()

        return redirect(url_for('login'))  # Redirect to login page after successful signup
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_data = supabase.table('users').select('*').eq('email', email).execute()
        worker_data = supabase.table('workers').select('*').eq('email', email).execute()

        if user_data.data:
            user = user_data.data[0]
            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_type'] = 'user'
                return redirect(url_for('user_dashboard'))
        
        if worker_data.data:
            worker = worker_data.data[0]
            if check_password_hash(worker['password'], password):
                session['user_id'] = worker['id']
                session['user_type'] = 'worker'
                return redirect(url_for('worker_dashboard'))

        return "Invalid credentials, please try again."
    return render_template('login.html')

@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    # Check if the user is logged in (if 'user_id' exists in the session)
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    # Get the user data from the database using the user_id
    user_data = supabase.table('users').select('*').eq('id', session['user_id']).execute().data

    # Fetch workers from the database
    workers = supabase.table('workers').select('*').execute().data

    # If the form is submitted, filter workers based on the selected profession or city
    if request.method == 'POST':
        profession = request.form.get('profession')
        city = request.form.get('city')
        
        # Filter workers based on the selected criteria (if any)
        query = supabase.table('workers').select('*')
        
        if profession:
            query = query.eq('profession', profession)
        if city:
            query = query.eq('city', city)
        
        workers = query.execute().data

    return render_template('user_dashboard.html', user=user_data, workers=workers)

@app.route('/worker_dashboard')
def worker_dashboard():
    # Check if worker is logged in (session should store worker_id, not user_id)
    if 'user_id' not in session:  
        return redirect(url_for('login'))  # Redirect to login if not logged in

    # Fetch worker details
    worker_data = supabase.table('workers').select('*').eq('id', session['user_id']).execute().data
    if not worker_data:  # If no worker found
        return "Worker not found", 404
    
    worker = worker_data[0]  # Extract first (and only) result

    # Fetch bookings for this worker
    bookings = supabase.table('bookings').select('*').eq('worker_id', session['user_id']).execute().data

    # Fetch user details for each booking
    for booking in bookings:
        user_data = supabase.table('users').select('*').eq('id', booking['user_id']).execute().data
        if user_data:
            user = user_data[0]
            booking['user_name'] = user['name']
            booking['user_address'] = user['address']

    # Booking statistics
    total_requests = len(bookings)
    accepted_count = sum(1 for b in bookings if b['status'] == 'Accepted')
    rejected_count = sum(1 for b in bookings if b['status'] == 'Rejected')

    return render_template(
        'worker_dashboard.html',
        worker=worker,  # Pass single worker, not list
        bookings=bookings,
        total_requests=total_requests,
        accepted_count=accepted_count,
        rejected_count=rejected_count
    )

@app.route('/logout')
def logout():
    # Logic to handle logout (e.g., clearing session or cookies)
    session.pop('user_id', None)  # Example to pop the user session
    session.pop('user_type', None)  # Ensure user_type is cleared as well
    return redirect(url_for('login'))  # Redirect to login page after logging out

@app.route('/book_worker', methods=['POST'])
def book_worker():
    try:
        worker_id = request.form['worker_id']
        booking_date = request.form['date']
        booking_time = request.form['time']
        user_id = session['user_id']
        
        # Ensure that required fields are present
        if not worker_id or not booking_date or not booking_time:
            return "Error: Missing required fields", 400

        # Insert the booking into the database
        supabase.table('bookings').insert({
            'user_id': user_id,
            'worker_id': worker_id,
            'booking_date': booking_date,
            'booking_time': booking_time,
            'status': 'Pending'
        }).execute()

        return redirect(url_for('user_dashboard'))
    
    except KeyError as e:
        # If a required form key is missing
        return f"Error: Missing form field {e}", 400
    except Exception as e:
        # Handle other exceptions
        return f"An unexpected error occurred: {e}", 500

@app.route('/history')
def history():
    # Check if user is logged in (if 'user_id' is in the session)
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['user_id']
    
    # Fetch bookings made by the user from the bookings table
    bookings = supabase.table('bookings').select('*').eq('user_id', user_id).execute().data
    
    # Fetch worker details for each booking
    for booking in bookings:
        worker_data = supabase.table('workers').select('*').eq('id', booking['worker_id']).execute().data
        if worker_data:
            worker = worker_data[0]
            booking['worker_name'] = worker['name']
            booking['worker_city'] = worker['city']
            booking['hourly_charge'] = worker['hourly_charge']
    
    return render_template('history.html', bookings=bookings)

@app.route('/accept_booking/<int:booking_id>', methods=['POST'])
def accept_booking(booking_id):
    # Update status to 'Accepted'
    supabase.table('bookings').update({'status': 'Accepted'}).eq('id', booking_id).execute()
    return redirect(url_for('worker_dashboard'))

@app.route('/reject_booking/<int:booking_id>', methods=['POST'])
def reject_booking(booking_id):
    # Update status to 'Rejected'
    supabase.table('bookings').update({'status': 'Rejected'}).eq('id', booking_id).execute()
    return redirect(url_for('worker_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
