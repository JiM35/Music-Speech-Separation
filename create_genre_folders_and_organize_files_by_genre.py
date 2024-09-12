import os
import json
import re
import shutil
from difflib import get_close_matches

# List of words to ignore in titles
ignore_words = ['Remix', 'feat', 'Official Music Video', 'Lyric Video', 'Official Video', 'Official Audio', 'Acoustic',
                'Official Lyric Video', 'Official Lyrics', 'Official HD Video', 'Official Visualizer',
                'Official Dance Video', 'SMS [Skiza] to 811']


# Function to sanitize folder names
def sanitize_folder_name(name):
    return re.sub(r'[\\/:*?"<>|]', '_', name)


# Function to create folders based on genreNames
def create_folders(data, parent_folder, no_genre_folder):
    if not os.path.exists(parent_folder):
        os.makedirs(parent_folder)

    for entry in data:
        genres = entry.get('genreNames', [])
        if genres:
            sanitized_genres = [sanitize_folder_name(genre) for genre in genres]
            folder_name = os.path.join(parent_folder, ", ".join(sanitized_genres))
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                print(f"Created folder: {folder_name}")
        else:
            if not os.path.exists(no_genre_folder):
                os.makedirs(no_genre_folder)
                print(f"Created folder: {no_genre_folder}")


# Function to remove ignore words from a string
def remove_ignore_words(text):
    for word in ignore_words:
        text = re.sub(re.escape(word), '', text, flags=re.IGNORECASE)
    return text.strip()


# Function to find the closest match for a given filename
def find_closest_match(filename, titles):
    filename_base = os.path.splitext(filename)[0]
    filename_base_cleaned = remove_ignore_words(filename_base)
    titles_cleaned = [remove_ignore_words(title) for title in titles]
    closest_matches = get_close_matches(filename_base_cleaned, titles_cleaned, n=1, cutoff=0.6)
    return titles[titles_cleaned.index(closest_matches[0])] if closest_matches else None


# Function to move files to their respective folders
def move_files(data, source_folder, parent_folder, no_genre_folder):
    titles = [entry['title'] for entry in data]

    for entry in data:
        artist = entry.get('artist', '')
        title = entry.get('title', '')
        genres = entry.get('genreNames', [])

        if genres:
            sanitized_genres = [sanitize_folder_name(genre) for genre in genres]
            folder_name = os.path.join(parent_folder, ", ".join(sanitized_genres))
        else:
            folder_name = no_genre_folder

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Find the closest matching file in the source folder
        file_list = os.listdir(source_folder)
        closest_match = find_closest_match(f"{artist} - {title}", file_list)

        if closest_match:
            src_file_path = os.path.join(source_folder, closest_match)
            dst_file_path = os.path.join(folder_name, closest_match)

            if os.path.isfile(src_file_path):
                shutil.move(src_file_path, dst_file_path)
                print(f"Moved file: {closest_match} to folder: {folder_name}")
            else:
                print(f"File not found: {src_file_path}")
        else:
            print(f"No close match found for: {artist} - {title}")


# Read JSON data from a file
with open('JSON files/unique_audio_pairs.json', 'r') as file:
    data = json.load(file)

# Define the parent folder, source folder, and no genre folder
parent_folder = "H:/genre folders"
source_folder = "H:/datasets/music"
no_genre_folder = os.path.join(parent_folder, "No Genre")

# Create folders based on genreNames and the no genre folder
create_folders(data, parent_folder, no_genre_folder)

# Move files to their respective folders
move_files(data, source_folder, parent_folder, no_genre_folder)
