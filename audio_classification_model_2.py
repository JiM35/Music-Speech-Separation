import os
import librosa
import subprocess
import h5py
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# Initialize the scaler
scaler = StandardScaler()

# ANSI code for green text
GREEN = "\033[92m"
RESET = "\033[0m"

# Path to your audio dataset (songs used for training)
audio_dataset_path = 'H:\\genre folders'
# Path to the 20-hour DJ mix
dj_mix_path = "C:/Users/giton/Desktop/combined_audio.mp3"
# Path to HDF5 file for storing features
hdf5_path = 'audio_features.h5'


# Function to split the large MP3 file into overlapping smaller segments using ffmpeg and save them in a new folder
def split_audio(input_file, segment_length=60, overlap=0.2):
    file_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.join(os.path.dirname(input_file), f"{file_name}_wav_segments")

    if os.path.exists(output_dir) and len(os.listdir(output_dir)) > 0:
        print(f"Segments for {file_name} already exist. Skipping splitting.")
        return output_dir

    os.makedirs(output_dir, exist_ok=True)

    try:
        segment_offset = int(segment_length * (1 - overlap))
        segment_duration_str = str(segment_length)
        segment_offset_str = str(segment_offset)

        ffmpeg_command = [
            'ffmpeg', '-i', input_file, '-f', 'segment', '-segment_time', segment_duration_str,
            '-segment_start_number', '0', '-segment_time_delta', segment_offset_str,
            '-c', 'pcm_s16le', '-ar', '44100', os.path.join(output_dir, 'segment_%03d.wav')
        ]
        subprocess.run(ffmpeg_command, check=True)
        print(f"Audio split into {segment_length // 60} minute WAV segments with {int(overlap * 100)}% overlap and "
              f"saved in {output_dir}")
        return output_dir
    except subprocess.CalledProcessError as e:
        print(f"Error splitting audio: {e}")
        return None


def load_training_songs(audio_dataset_path, hdf5_path):
    training_songs = {}

    # Check if the HDF5 file exists
    processed_songs = []
    if os.path.exists(hdf5_path):
        # Open the HDF5 file to check which songs already have features saved
        with h5py.File(hdf5_path, 'r') as hf:
            processed_songs = list(hf.keys())

    for genre in os.listdir(audio_dataset_path):
        genre_path = os.path.join(audio_dataset_path, genre)
        if os.path.isdir(genre_path):
            for file in os.listdir(genre_path):
                song_name = os.path.splitext(file)[0]
                file_path = os.path.join(genre_path, file)

                if song_name in processed_songs:
                    # Skip processing this file since its features already exist in HDF5
                    print(f"Features for {song_name} are already processed. Skipping...")
                    features = load_features_from_hdf5(hdf5_path, song_name)
                else:
                    # If song is new, extract and save features
                    features = feature_extractor(file_path)
                    if features is not None:
                        save_features_to_hdf5(hdf5_path, song_name, features)

                if features is not None:
                    training_songs[song_name] = features

    return training_songs


# Save features to HDF5
def save_features_to_hdf5(hdf5_file, song_name, features):
    # Check if the HDF5 file exists or create it if it doesn't
    with h5py.File(hdf5_file, 'a') as hf:
        if song_name in hf:
            print(f"Features for {song_name} already exist in {hdf5_file}.")
        else:
            hf.create_dataset(song_name, data=features)
            print(f"Saved features for {song_name}.")


# Load features from HDF5
def load_features_from_hdf5(hdf5_file, song_name):
    with h5py.File(hdf5_file, 'r') as hf:
        if song_name in hf:
            return hf[song_name][:]
        else:
            print(f"No features found for {song_name} in {hdf5_file}.")
            return None


# Feature extractor function
def feature_extractor(file, feature_type='mfcc', sample_rate=44100, n_mfcc=500):
    try:
        # Load the audio file
        audio, sr = librosa.load(file, sr=sample_rate, res_type='kaiser_fast')

        if feature_type == 'mfcc':
            # Extract MFCC features
            mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc).mean(axis=1)
            return mfccs
        else:
            print(f"Unknown feature type: {feature_type}")
            return None

    except Exception as e:
        print(f"Error processing {file} with {feature_type}: {e}")
        return None


# Process the DJ mix without majority voting
def process_dj_mix(dj_mix_path, training_songs):
    segment_dir = split_audio(dj_mix_path)

    if segment_dir is None:
        print("Audio splitting failed.")
        return []

    predictions = []
    segment_number = 0

    # Process each segment of the DJ mix
    for segment_file in sorted(os.listdir(segment_dir)):
        segment_path = os.path.join(segment_dir, segment_file)

        print(f"\nSegment {segment_number}:")  # Show the current segment number

        # Extract MFCC features from the DJ mix segment
        dj_mix_features = feature_extractor(segment_path)

        if dj_mix_features is None:
            print(f"Could not extract features from {segment_path}")
            continue

        # Compare with training songs
        max_similarity = -1
        predicted_song = None

        for song_name, song_features in training_songs.items():
            # Compute cosine similarity between the DJ mix segment and the training song features
            similarity = cosine_similarity(
                dj_mix_features.reshape(1, -1),
                song_features.reshape(1, -1)
            )[0][0]

            if similarity > max_similarity:
                max_similarity = similarity
                predicted_song = song_name

        if predicted_song:
            print(f"{GREEN}Predicted: {predicted_song} (Similarity: {max_similarity:.20f}){RESET}")
            predictions.append(predicted_song)
        else:
            print(f"No match found for segment {segment_number}")

        segment_number += 1

    return predictions


# Main script execution without majority voting
if __name__ == "__main__":
    print("Loading training songs...")
    training_songs = load_training_songs(audio_dataset_path, hdf5_path)

    print("Processing the DJ mix and showing predictions...")
    predicted_songs = process_dj_mix(dj_mix_path, training_songs)

    if predicted_songs:
        print("Predicted songs in the DJ mix:")
        for segment_number, song in predicted_songs:
            print(f"Segment {segment_number} was predicted to have the song: {song}")
    else:
        print("No songs were predicted.")