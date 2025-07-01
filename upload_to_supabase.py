import os
import re
from urllib.parse import quote

from supabase import create_client, Client

# Initialize Supabase client
url: str = "https://myjqzfcghejvpduorgle.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im15anF6ZmNnaGVqdnBkdW9yZ2xlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY0MzIyODIsImV4cCI6MjA2MjAwODI4Mn0.9CZT5h9qMt3P99emaq0YJlsy_nibBwCjvFqgdhZko0k"
supabase: Client = create_client(url, key)


# Directories for audio and images
audio_base_dir = "static/audio/songsmp3"
image_base_dir = "static/images/songpics/Songs-pictures"
log_file = "upload_log.txt"

# Function to sanitize filenames (handle special characters and spaces)
def sanitize_filename(name):
    # Replace non-breaking space with regular space
    name = name.replace('\u00A0', ' ')
    # URL encode the filename to handle special characters
    name = quote(name)
    # Remove unsafe characters (e.g., symbols that aren't allowed in file paths)
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    return name

# Function to check if the file is already uploaded
def already_uploaded(bucket, path):
    folder = os.path.dirname(path)
    filename = os.path.basename(path)
    files = supabase.storage.from_(bucket).list(folder)
    return any(f['name'] == filename for f in files)

# Function to log the upload status
def log_upload(log_file, message):
    with open(log_file, "a", encoding='utf-8') as log:
        log.write(message + "\n")

# Upload image files
for category in os.listdir(image_base_dir):
    category_path = os.path.join(image_base_dir, category)
    if os.path.isdir(category_path):
        for filename in os.listdir(category_path):
            if filename.endswith((".jpg", ".jpeg", ".png")):
                safe_filename = sanitize_filename(filename)
                file_path = os.path.join(category_path, filename)
                storage_path = f"{category}/{safe_filename}"

                if already_uploaded("musiverse-images", storage_path):
                    print(f"Skipped (already uploaded): {storage_path}")
                    continue

                try:
                    with open(file_path, "rb") as f:
                        supabase.storage.from_("musiverse-images").upload(storage_path, f)
                    print(f"Uploaded image: {storage_path}")
                    log_upload(log_file, f"IMAGE: {storage_path}")
                except Exception as e:
                    print(f"Error uploading {storage_path}: {e}")
                    log_upload(log_file, f"ERROR: {storage_path} - {e}")
