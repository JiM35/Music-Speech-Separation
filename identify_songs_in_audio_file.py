# identify_songs_in_audio_file.py

import requests
import ffmpeg
import json
import os

# AudD API key
API_KEY = '055e9477fae3ad290470847bc2ae34f7'

# Input audio file
input_audio = "H:\\(Temporary) Radio Recordings\\soundcityfmnrb started 05-40-03 am ended 1-40-03 am.mp3"

# Output JSON file
output_json_file = 'audio_identification_results.json'


# Function to send audio segment to AudD
def identify_song(file_path, api_key):
    with open(file_path, 'rb') as f:
        files = {
            'file': f
        }
        data = {
            'api_token': api_key,
            'return': 'timecode,apple_music,spotify'
        }
        response = requests.post('https://api.audd.io/', data=data, files=files)
    return response.json()


# Increase segment length and adjust overlap
segment_length = 90  # 90 seconds
overlap = 20  # 20 seconds
duration = 3600  # 1 hour

# Generate segment timestamps
timestamps = [(i, min(i + segment_length, duration)) for i in range(0, duration, segment_length - overlap)]

# Container to store results
results = []

# Load existing results if the file exists
if os.path.exists(output_json_file):
    with open(output_json_file, 'r') as json_file:
        results = json.load(json_file)

# Identify each segment
for i, (start, end) in enumerate(timestamps):
    output_segment = f'temp_segment_{i}.mp3'
    (
        ffmpeg
        .input(input_audio, ss=start, t=(end - start))
        .output(output_segment)
        .run(overwrite_output=True)
    )
    result = identify_song(output_segment, API_KEY)
    results.append({'segment': i + 1, 'start': start, 'end': end, 'result': result})
    print(f'Segment {i + 1}:', result)

# Save results to the JSON file
if os.path.exists(output_json_file):
    with open(output_json_file, 'r+') as json_file:
        existing_results = json.load(json_file)
        existing_results.extend(results)
        json_file.seek(0)
        json.dump(existing_results, json_file, indent=4)
else:
    with open(output_json_file, 'w') as json_file:
        json.dump(results, json_file, indent=4)
