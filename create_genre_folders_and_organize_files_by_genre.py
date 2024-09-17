import os
import json
import re
import shutil
from difflib import get_close_matches

# Extended list of words to ignore in titles
ignore_words = [
    'Remix', 'feat', 'featuring', 'Official Music Video', 'Lyric Video', 'Official Video', 'Official Audio',
    'Acoustic', 'Official Lyric Video', 'Official Lyrics', 'Official HD Video', 'Official Visualizer', 'Official',
    'Official Dance Video', 'SMS [Skiza] to 811', 'Album Version', 'Lyrics', 'Audio', 'ft', 'x', 'Official Clean Audio',
    'Visualizer', 'SKIZA CODE'
]


# Function to sanitize folder names
def sanitize_folder_name(name):
    return re.sub(r'[\\/:*?."<>()|]', '_', name)


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
        text = re.sub(fr'(\s+)?{re.escape(word)}(\s+)?', ' ', text, flags=re.IGNORECASE)
    return text.strip()


# Function to normalize text by removing special characters, ignore words, and ignoring case
def normalize_text(text):
    text = remove_ignore_words(text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove special characters
    return text.lower().strip()


# Function to find the closest match for a given filename
def find_closest_match(filename, titles):
    filename_base = os.path.splitext(filename)[0]
    filename_base_cleaned = normalize_text(filename_base)
    titles_cleaned = [normalize_text(title) for title in titles]

    # First iteration: use get_close_matches
    closest_matches = get_close_matches(filename_base_cleaned, titles_cleaned, n=1, cutoff=0.6)
    if closest_matches:
        return titles[titles_cleaned.index(closest_matches[0])]

    # Second iteration: if no close match found, check for 4-word overlap
    filename_words = set(filename_base_cleaned.split())
    for title, title_cleaned in zip(titles, titles_cleaned):
        title_words = set(title_cleaned.split())
        common_words = filename_words.intersection(title_words)
        if len(common_words) >= 4:
            return title

    # Third iteration: if no match after 4-word overlap, check for 3-word overlap
    for title, title_cleaned in zip(titles, titles_cleaned):
        title_words = set(title_cleaned.split())
        common_words = filename_words.intersection(title_words)
        if len(common_words) >= 3:
            return title

    # Return None if no match found
    return None


# Function to move files to their respective folders
def move_files(data, source_folder, parent_folder, no_genre_folder, unmatched_folder):
    titles = [entry['title'] for entry in data]
    moved_files = []

    # Ensure the Unmatched folder exists
    if not os.path.exists(unmatched_folder):
        os.makedirs(unmatched_folder)

    # Move matched files to genre folders
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
                moved_files.append(closest_match)
                print(f"Moved file: {closest_match} to folder: {folder_name}")
            else:
                print(f"File not found: {src_file_path}")
        else:
            print(f"No close match found for: {artist} - {title}")

    # Find remaining files in the source folder
    remaining_files = [f for f in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, f))]

    # If there are remaining files, ask user for confirmation to move them to the Unmatched folder
    if remaining_files:
        print(f"\nThere are {len(remaining_files)} files remaining in the source folder.")
        move_to_unmatched = input("Do you want to move these remaining files to the Unmatched folder? (y/n): ").lower()

        if move_to_unmatched == 'y':
            for file in remaining_files:
                if file not in moved_files:
                    src_file_path = os.path.join(source_folder, file)
                    dst_file_path = os.path.join(unmatched_folder, file)
                    shutil.move(src_file_path, dst_file_path)
                    print(f"Moved unmatched file: {file} to folder: {unmatched_folder}")
        else:
            print("Remaining files were not moved.")


# Read JSON data from a file
with open('JSON files/unique_audio_pairs.json', 'r') as file:
    data = json.load(file)

# Define the parent folder, source folder, and no genre folder
parent_folder = "H:/genre folders"
source_folder = "H:/datasets/music"
no_genre_folder = os.path.join(parent_folder, "No Genre")
unmatched_folder = os.path.join(parent_folder, "Unmatched")

# Create folders based on genreNames and the no genre folder
create_folders(data, parent_folder, no_genre_folder)

# Move files to their respective folders, including asking for unmatched files
move_files(data, source_folder, parent_folder, no_genre_folder, unmatched_folder)
