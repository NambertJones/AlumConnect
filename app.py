# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Secret key for session & flash messages (MUST be set for production)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret')

# --- MongoDB Configuration ---
MONGO_URI = os.environ.get('MONGO_URI') or \
    'mongodb+srv://nambybackup:jxGx4JJSNH3RwDyQ@cluster0.btzx44b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

client = MongoClient(MONGO_URI)
db = client.alumni_accelerator_db

# Collections
users_collection = db.users
job_listings_collection = db.job_listings
mentorships_collection = db.mentorships
connections_collection = db.connections


# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html', title="Alumni Career Accelerator")


@app.route('/networking')
def networking():
    alumni_users = list(users_collection.find({'user_type': 'alumni'}).limit(3))
    return render_template('networking.html', title="Alumni-Student Networking", alumni_users=alumni_users)


@app.route('/job_board')
def job_board():
    job_listings = list(job_listings_collection.find().sort('posted_date', -1).limit(5))
    return render_template('job_board.html', title="Referral-Based Job Board", job_listings=job_listings)


@app.route('/mentorship')
def mentorship():
    mentors = list(users_collection.find({'user_type': 'alumni'}).limit(3))
    return render_template('mentorship.html', title="Mentorship Matchmaking", mentors=mentors)


@app.route('/dashboard')
def dashboard():
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
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')

        if not username or not email or not password or not user_type:
            flash('All fields are required!', 'error')
            return redirect(url_for('register'))

        if users_collection.find_one({'username': username}):
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))
        if users_collection.find_one({'email': email}):
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        new_user = {
            'username': username,
            'email': email,
            'password_hash': password,  # NOTE: In production, hash passwords!
            'user_type': user_type,
            'created_at': datetime.datetime.now()
        }
        users_collection.insert_one(new_user)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title="Register")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = users_collection.find_one({'username': username})
        if user and user['password_hash'] == password:
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html', title="Login")


# Local run (only in development)
if __name__ == '__main__':
    # Insert dummy data only if DB is empty (for quick local testing)
    if users_collection.count_documents({}) == 0:
        print("Adding dummy data...")
        dummy_alumni_id = users_collection.insert_one({
            'username': 'alumni1',
            'email': 'alumni1@example.com',
            'password_hash': 'password',
            'user_type': 'alumni',
            'created_at': datetime.datetime.now()
        }).inserted_id

        dummy_student_id = users_collection.insert_one({
            'username': 'student1',
            'email': 'student1@example.com',
            'password_hash': 'password',
            'user_type': 'student',
            'created_at': datetime.datetime.now()
        }).inserted_id

        job_listings_collection.insert_one({
            'title': 'Junior Developer',
            'company': 'Tech Innovations',
            'location': 'Remote',
            'description': 'Exciting role for a new developer.',
            'posted_date': datetime.datetime.now(),
            'referral_available': True,
            'user_id': dummy_alumni_id
        })

        mentorships_collection.insert_one({
            'mentor_id': dummy_alumni_id,
            'mentee_id': dummy_student_id,
            'status': 'active',
            'request_date': datetime.datetime.now()
        })

        connections_collection.insert_one({
            'user_id': dummy_student_id,
            'connected_user_id': dummy_alumni_id,
            'status': 'accepted',
            'connection_date': datetime.datetime.now()
        })
        print("Dummy data added.")
    app.run(debug=True)
