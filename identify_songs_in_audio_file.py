import requests
import ffmpeg
import json
import os

# AudD API key
API_KEY = '055e9477fae3ad290470847bc2ae34f7'

# Input audio file
input_audio = "H:/(Temporary) Radio Recordings/soundcityfmnrb started 04-53-30 am ended 9-59-39 am.mp3"

# Output JSON file directory
output_json_file = "JSON files/audio_identification_results.json"

# Generate another output JSON file named after the audio file
audio_base_name = os.path.splitext(os.path.basename(input_audio))[0]
additional_output_json_file = f'JSON files/{audio_base_name}_identification_results.json'

# Create a directory for storing the temporary segments
temp_dir = f"temp_segments/{audio_base_name}"
os.makedirs(temp_dir, exist_ok=True)

# Check if the audio file has already been identified
if os.path.exists(additional_output_json_file):
    print(f"Identification results for '{audio_base_name}' already exist. Skipping the process.")
else:
    print(f"Processing audio file: {input_audio}")

    # Function to send audio segment to AudD
    def identify_song(file_path, api_key):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'api_token': api_key, 'return': 'timecode,apple_music,spotify'}
            try:
                response = requests.post('https://api.audd.io/', data=data, files=files)
                response.raise_for_status()  # Raise an HTTPError for bad responses
                response_json = response.json()  # Attempt to decode the JSON response
                if response_json:  # Check if the response JSON is not empty
                    return response_json
                else:
                    print(f"Empty JSON response for file {file_path}")
                    return {}
            except requests.exceptions.RequestException as e:
                print(f"Request error for file {file_path}: {e}")
                return {}
            except json.JSONDecodeError as e:
                print(f"JSON decode error for file {file_path}: {e}")
                return {}

    # Function to get the duration of the audio file
    def get_audio_duration(file_path):
        probe = ffmpeg.probe(file_path)
        duration = float(probe['format']['duration'])
        return duration

    # Get the full duration of the audio file
    duration = get_audio_duration(input_audio)

    # Increase segment length and adjust overlap
    segment_length = 90  # 90 seconds
    overlap = 30  # 20 seconds

    # Generate segment timestamps for the full duration of the file
    timestamps = [(i, min(i + segment_length, duration)) for i in range(0, int(duration), segment_length - overlap)]

    # Container to store results
    results = []

    # Load existing results if the file exists
    if os.path.exists(output_json_file):
        with open(output_json_file, 'r') as json_file:
            results = json.load(json_file)

    # Identify each segment
    for i, (start, end) in enumerate(timestamps):
        output_segment = os.path.join(temp_dir, f'temp_segment_{i}.mp3')
        (
            ffmpeg
            .input(input_audio, ss=start, t=(end - start))
            .output(output_segment)
            .run(overwrite_output=True)
        )
        result = identify_song(output_segment, API_KEY)
        results.append({'segment': i + 1, 'start': start, 'end': end, 'result': result})
        print(f'Segment {i + 1}:', result)

    # Function to save results into a JSON file
    def save_results_to_file(file_path, results):
        if os.path.exists(file_path):
            with open(file_path, 'r+') as json_file:
                existing_results = json.load(json_file)
                existing_results.extend(results)
                json_file.seek(0)
                json.dump(existing_results, json_file, indent=4)
        else:
            with open(file_path, 'w') as json_file:
                json.dump(results, json_file, indent=4)

    # Save results to the main output JSON file
    save_results_to_file(output_json_file, results)

    # Save results to the additional JSON file named after the audio file
    save_results_to_file(additional_output_json_file, results)
