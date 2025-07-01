import os
import re

def sanitize_filename(name):
    # Replace non-breaking spaces and weird whitespace with regular space
    name = name.replace('\u00A0', ' ')
    name = re.sub(r'\s+', ' ', name)  # Collapse multiple spaces/tabs/newlines
    name = name.strip()
    # Optional: Remove unsafe characters (if any)
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    return name

def clean_folder(folder_path):
    for root, _, files in os.walk(folder_path):
        for filename in files:
            clean_name = sanitize_filename(filename)
            if clean_name != filename:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, clean_name)
                os.rename(old_path, new_path)
                print(f"Renamed: {filename} → {clean_name}")

# 👇 Edit these paths to match your folders
audio_dir = "static/audio/songsmp3"
image_dir = "static/images/songpics/Songs-pictures"

# Clean all categories inside audio and image directories
for base_dir in [audio_dir, image_dir]:
    clean_folder(base_dir)
