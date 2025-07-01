from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import uuid

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')  # Loaded from .env

# Initialize Supabase client using env variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Buckets
AUDIO_BUCKET = "musiverse-audio"
IMAGE_BUCKET = "musiverse-images"

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        response = supabase.table("musisongs").select("*").execute()
        songs = response.data
        popular_songs = [song for song in songs if int(song.get('popularity', 0)) >= 80]

        for song in songs + popular_songs:
            song['song_url'] = supabase.storage.from_(AUDIO_BUCKET).get_public_url(song['filename'])
            if song.get('image'):
                song['image_url'] = supabase.storage.from_(IMAGE_BUCKET).get_public_url(song['image']).split('?')[0]

        return render_template('dashboard.html', songs=songs, popular_songs=popular_songs)

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/popular')
def popular():
    try:
        response = supabase.table('musisongs').select('*').order('popularity', desc=True).limit(20).execute()
        popular_songs = response.data or []
        for song in popular_songs:
            song['song_url'] = supabase.storage.from_(AUDIO_BUCKET).get_public_url(song['filename'])
            song['image_url'] = supabase.storage.from_(IMAGE_BUCKET).get_public_url(song['image']).split('?')[0]
    except Exception as e:
        print("Error fetching popular songs:", e)
        popular_songs = []

    return render_template('partials/popular.html', popular_songs=popular_songs)

@app.route('/add_music')
def add_music():
    return render_template('partials/add_music.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        folder_name = "user_uploads"
        audio_file = request.files.get('file')
        if not audio_file:
            flash("Audio file is required", "danger")
            return redirect(url_for('add_music'))

        audio_filename = secure_filename(audio_file.filename)
        audio_data = audio_file.read()
        audio_path = f"{folder_name}/{audio_filename}"

        audio_upload = supabase.storage.from_(AUDIO_BUCKET).upload(audio_path, audio_data)
        if audio_upload.get('error'):
            flash("Error uploading audio file", "danger")
            return redirect(url_for('add_music'))

        title = request.form.get('title').strip()
        artist = request.form.get('artist').strip() or None
        album = request.form.get('album').strip() or None
        genre = request.form.get('genre') or None

        insert_data = {
            "song_name": title,
            "singer": artist,
            "album": album,
            "category": genre,
            "filename": audio_path,
        }

        insert_data_clean = {k: v for k, v in insert_data.items() if v is not None}
        insert_response = supabase.table("musisongs").insert(insert_data_clean).execute()
        if insert_response.get('error'):
            flash("Error inserting song data", "danger")
            return redirect(url_for('add_music'))

        flash("Successfully uploaded!", "success")
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f"Unexpected error: {str(e)}", "danger")
        return redirect(url_for('add_music'))

@app.route('/categories')
def categories():
    categories_list = ['English', 'Hindi', 'Korean', 'Punjabi', 'Pop', 'Classical', 'Romantic', 'Motivational']
    selected_category = request.args.get('category', 'All')

    if selected_category == 'All':
        response = supabase.table("musisongs").select("*").execute()
    else:
        response = supabase.table("musisongs").select("*").eq("category", selected_category).execute()

    songs = response.data or []

    for song in songs:
        song['song_url'] = supabase.storage.from_(AUDIO_BUCKET).get_public_url(song['filename'])
        song['image_url'] = supabase.storage.from_(IMAGE_BUCKET).get_public_url(song['image']).split('?')[0] if song.get('image') else None

    return render_template('partials/categories.html', categories=categories_list, category=selected_category, songs=songs)

@app.route('/api/songs')
def api_songs():
    category = request.args.get('category')
    if not category:
        return jsonify({'error': 'No category specified'}), 400

    response = supabase.table("musisongs").select("*").ilike("category", category).execute()
    songs = response.data or []

    for song in songs:
        song['song_url'] = supabase.storage.from_(AUDIO_BUCKET).get_public_url(song['filename'])
        song['image_url'] = supabase.storage.from_(IMAGE_BUCKET).get_public_url(song['image']).split('?')[0]

    return jsonify(songs)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip().lower()
    if not query:
        return redirect(url_for('dashboard'))

    try:
        response = supabase.table("musisongs").select("*").execute()
        all_songs = response.data or []
        filtered_songs = [
            song for song in all_songs
            if query in song.get("song_name", "").lower() or query in song.get("singer", "").lower()
        ]
        for song in filtered_songs:
            song['song_url'] = supabase.storage.from_(AUDIO_BUCKET).get_public_url(song['filename'])
            song['image_url'] = supabase.storage.from_(IMAGE_BUCKET).get_public_url(song['image']).split('?')[0]
        return render_template("partials/search_results.html", query=query, songs=filtered_songs)

    except Exception as e:
        return f"Error: {str(e)}", 500


if __name__ == '__main__':
    app.run(debug=True)
