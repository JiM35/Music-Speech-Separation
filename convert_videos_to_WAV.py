import ffmpeg
import os
import json
from datetime import datetime

# Path to the JSON file that will store processed files
PROCESSED_FILES_JSON = "JSON files/processed_files.json"


# Load the list of processed files from the JSON file
def load_processed_files():
    if os.path.exists(PROCESSED_FILES_JSON):
        with open(PROCESSED_FILES_JSON, 'r') as f:
            return json.load(f)
    return []


# Save the list of processed files to the JSON file with new lines for readability
def save_processed_files(processed_files):
    with open(PROCESSED_FILES_JSON, 'w') as f:
        json.dump(processed_files, f, indent=4, separators=(",", ": "))


# Convert video file to wav
def convert_to_wav(input_file, output_file):
    try:
        ffmpeg.input(input_file).output(output_file, acodec='pcm_s16le', ar=44100).run()
        print(f"[{get_timestamp()}] Successfully converted {input_file} to {output_file}")
    except ffmpeg.Error as e:
        print(f"[{get_timestamp()}] An error occurred: {e.stderr.decode()}")


# Convert files in the input directory to wav
def convert_files_in_directory(input_directory, output_directory, extensions=['.mkv', '.mp4']):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Load the list of already processed files
    processed_files = load_processed_files()

    for filename in os.listdir(input_directory):
        if any(filename.lower().endswith(ext) for ext in extensions):
            input_file = os.path.join(input_directory, filename)
            output_file = os.path.join(output_directory, os.path.splitext(filename)[0] + ".wav")

            # Check if the file has already been processed
            if filename in processed_files:
                print(f"[{get_timestamp()}] File {filename} already processed. Skipping.")
                continue

            # Convert the file to wav format
            convert_to_wav(input_file, output_file)

            # Mark the file as processed and save the updated list
            processed_files.append(filename)
            save_processed_files(processed_files)


# Helper function to get the current timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    input_directory = "I:/Tutorials/Radio Music Speech Separation/datasets/music"
    output_directory = "H:/datasets/music"

    convert_files_in_directory(input_directory, output_directory)
