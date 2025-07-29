# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId # Used to work with MongoDB's default _id field
import os
import datetime # For timestamping documents
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file.
# This should be called at the very beginning of your application.
load_dotenv()

app = Flask(__name__)

# --- MongoDB Configuration ---
# Retrieve MONGO_URI from environment variables (loaded from .env).
# If not found, it falls back to a default local MongoDB URI.
MONGO_URI = os.environ.get('MONGO_URI')
if not MONGO_URI:
    print("MONGO_URI not found in environment variables or .env file. Falling back to local MongoDB.")
    MONGO_URI = 'mongodb://localhost:27017/'

# Establish connection to MongoDB client.
client = MongoClient(MONGO_URI)

# Select your database. Replace 'alumni_accelerator_db' with your preferred database name.
db = client.alumni_accelerator_db

# Define references to your MongoDB collections (analogous to tables in relational databases).
users_collection = db.users
job_listings_collection = db.job_listings
mentorships_collection = db.mentorships
connections_collection = db.connections

# --- Routes for your application pages ---

@app.route('/')
def index():
    """
    Renders the main index page.
    This page serves as the entry point and provides navigation to other sections.
    """
    return render_template('index.html', title="Alumni Career Accelerator")

@app.route('/networking')
def networking():
    """
    Renders the Alumni-Student Networking page.
    Fetches a limited number of alumni users to display for networking purposes.
    """
    # Fetch up to 3 alumni users from the 'users' collection.
    # In a production application, you would implement more advanced search, filtering, and pagination.
    alumni_users = list(users_collection.find({'user_type': 'alumni'}).limit(3))
    return render_template('networking.html', title="Alumni-Student Networking", alumni_users=alumni_users)

@app.route('/job_board')
def job_board():
    """
    Renders the Referral-Based Job Board page.
    Fetches a limited number of job listings, sorted by posted date (newest first).
    """
    # Fetch up to 5 job listings from the 'job_listings' collection, sorted by 'posted_date' in descending order.
    job_listings = list(job_listings_collection.find().sort('posted_date', -1).limit(5))
    return render_template('job_board.html', title="Referral-Based Job Board", job_listings=job_listings)

@app.route('/mentorship')
def mentorship():
    """
    Renders the Mentorship Matchmaking page.
    Fetches a limited number of potential mentors (alumni users) to display.
    """
    # Fetch up to 3 alumni users to suggest as mentors.
    mentors = list(users_collection.find({'user_type': 'alumni'}).limit(3))
    return render_template('mentorship.html', title="Mentorship Matchmaking", mentors=mentors)

@app.route('/dashboard')
def dashboard():
    """
    Renders the Success Tracking Dashboard page.
    Displays counts of connections, job applications, and mentorship sessions.
    Note: In a real application, these counts would be specific to the logged-in user.
    """
    # Get the total count of documents in each collection for demonstration.
    connections_count = connections_collection.count_documents({})
    jobs_applied_count = job_listings_collection.count_documents({})
    mentorship_sessions_count = mentorships_collection.count_documents({'status': 'active'})

    return render_template('dashboard.html',
                           title="Success Tracking Dashboard",
                           connections_count=connections_count,
                           jobs_applied_count=jobs_applied_count,
                           mentorship_sessions_count=mentorship_sessions_count)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles user registration.
    - GET: Displays the registration form.
    - POST: Processes the form submission, validates input, and saves new user data to MongoDB.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password') # IMPORTANT: In a production app, hash this password (e.g., using Werkzeug's generate_password_hash).
        user_type = request.form.get('user_type')

        # Basic server-side validation for required fields.
        if not username or not email or not password or not user_type:
            flash('All fields are required!', 'error')
            return redirect(url_for('register'))

        # Check if username or email already exists in the database.
        if users_collection.find_one({'username': username}):
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))
        if users_collection.find_one({'email': email}):
            flash('Email already registered. Please use a different email or login.', 'error')
            return redirect(url_for('register'))

        # Create a new user document (dictionary) to insert into MongoDB.
        new_user = {
            'username': username,
            'email': email,
            'password_hash': password, # Storing plain text password for simplicity, DO NOT do this in production.
            'user_type': user_type,
            'created_at': datetime.datetime.now() # Add a timestamp for when the user was created.
        }
        users_collection.insert_one(new_user) # Insert the new user document into the 'users' collection.
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title="Register")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    - GET: Displays the login form.
    - POST: Processes the form submission, verifies credentials against MongoDB.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Attempt to find the user by username in the 'users' collection.
        user = users_collection.find_one({'username': username})

        # Verify if the user exists and if the password matches.
        # IMPORTANT: In a production app, compare hashed passwords using a function like Werkzeug's check_password_hash.
        if user and user['password_hash'] == password:
            flash('Login successful!', 'success')
            # In a real application, you would set up a user session here (e.g., using Flask-Login)
            # to keep the user logged in across requests.
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html', title="Login")

# --- Main execution block ---
if __name__ == '__main__':
    # This block runs when the script is executed directly.

    # Optional: Add some dummy data for testing purposes if the 'users' collection is empty.
    # This helps in quickly populating the database for development without manual entry.
    if users_collection.count_documents({}) == 0:
        print("Adding dummy data...")
        # Insert a dummy alumni user and get their generated MongoDB ObjectId.
        dummy_alumni_id = users_collection.insert_one({
            'username': 'alumni1',
            'email': 'alumni1@example.com',
            'password_hash': 'password',
            'user_type': 'alumni',
            'created_at': datetime.datetime.now()
        }).inserted_id

        # Insert a dummy student user and get their generated MongoDB ObjectId.
        dummy_student_id = users_collection.insert_one({
            'username': 'student1',
            'email': 'student1@example.com',
            'password_hash': 'password',
            'user_type': 'student',
            'created_at': datetime.datetime.now()
        }).inserted_id

        # Insert a dummy job listing, linking it to the dummy alumni user via their ObjectId.
        job_listings_collection.insert_one({
            'title': 'Junior Developer',
            'company': 'Tech Innovations',
            'location': 'Remote',
            'description': 'Exciting role for a new developer.',
            'posted_date': datetime.datetime.now(),
            'referral_available': True,
            'user_id': dummy_alumni_id # Store ObjectId reference
        })

        # Insert a dummy mentorship entry, linking mentor and mentee by their ObjectIds.
        mentorships_collection.insert_one({
            'mentor_id': dummy_alumni_id,
            'mentee_id': dummy_student_id,
            'status': 'active',
            'request_date': datetime.datetime.now()
        })

        # Insert a dummy connection entry.
        connections_collection.insert_one({
            'user_id': dummy_student_id,
            'connected_user_id': dummy_alumni_id,
            'status': 'accepted',
            'connection_date': datetime.datetime.now()
        })
        print("Dummy data added.")

    # Run the Flask application in debug mode.
    # debug=True allows for automatic reloading on code changes and provides a debugger.
    # For production, set debug=False and use a production-ready WSGI server (e.g., Gunicorn).
    app.run(debug=True)
