import os
import librosa
import numpy as np
import h5py
from scipy.signal import savgol_filter
import datetime


# Function to convert seconds to hh:mm:ss with sub-second precision
def seconds_to_hms(seconds):
    return str(datetime.timedelta(seconds=seconds))  # Keep fractional seconds


# Function to extract BPMs from an audio file
def extract_bpm_sequence(audio_path, hop_length=2048):
    y, sr = librosa.load(audio_path)
    # Tempo/Beat detection
    _, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)

    if len(beats) < 2:
        return None, None  # Not enough beats for BPM calculation

    beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop_length)
    beat_intervals = np.diff(beat_times)
    tempo_over_time = 60.0 / beat_intervals

    # Apply Savitzky-Golay filter to smooth
    smoothed_tempo = savgol_filter(tempo_over_time, window_length=7, polyorder=2)

    return smoothed_tempo, beat_times


# Save BPM sequences for all training songs, skipping already processed files
def save_bpm_data(genre_folder, output_h5):
    # Open or create the HDF5 file
    with h5py.File(output_h5, 'a') as h5_file:
        for genre in os.listdir(genre_folder):
            genre_path = os.path.join(genre_folder, genre)

            if os.path.isdir(genre_path):
                # Create a group for the genre if it doesn't exist
                if genre not in h5_file:
                    genre_group = h5_file.create_group(genre)
                else:
                    genre_group = h5_file[genre]

                for song_file in os.listdir(genre_path):
                    if song_file.endswith('.wav'):
                        # Skip the song if it's already processed
                        if song_file in genre_group:
                            print(f"Skipped (already processed): {song_file}")
                            continue

                        song_path = os.path.join(genre_path, song_file)
                        bpm_sequence, beat_times = extract_bpm_sequence(song_path)

                        if bpm_sequence is not None:
                            # Store BPM sequence and beat times in the HDF5 file
                            song_group = genre_group.create_group(song_file)
                            song_group.create_dataset('bpm_sequence', data=bpm_sequence)
                            song_group.create_dataset('beat_times', data=beat_times)
                            print(f"Processed: {song_file}")
                        else:
                            print(f"Skipped: {song_file} (Not enough beats)")


# Predict song by matching BPM sequences with similarity score
def predict_song(audio_path, output_h5, hop_length=2048):
    new_bpm_sequence, _ = extract_bpm_sequence(audio_path, hop_length=hop_length)

    if new_bpm_sequence is None:
        return "No beats detected in the song."

    # Open the HDF5 file to access stored BPM data
    with h5py.File(output_h5, 'r') as h5_file:
        best_match = None
        best_similarity = 0.0  # Similarity score, where higher is better

        for genre in h5_file:
            genre_group = h5_file[genre]

            for song_file in genre_group:
                song_group = genre_group[song_file]
                stored_bpm_sequence = np.array(song_group['bpm_sequence'])

                min_len = min(len(new_bpm_sequence), len(stored_bpm_sequence))

                # Calculate the absolute difference between the two sequences
                diff = np.sum(np.abs(new_bpm_sequence[:min_len] - stored_bpm_sequence[:min_len]))

                # Normalize the difference based on the number of beats compared
                normalized_diff = diff / min_len if min_len > 0 else float('inf')

                # Convert difference to similarity score (higher score is better)
                similarity_score = 1 / (1 + normalized_diff)

                if similarity_score > best_similarity:
                    best_similarity = similarity_score
                    best_match = (genre, song_file, similarity_score)

        return best_match if best_match else "No match found"


genre_folder = "H:/genre folders"
output_h5 = "bpm_data.h5"

# Save BPMs of training songs, skipping already processed files
save_bpm_data(genre_folder, output_h5)

# Predict new song
audio_path = "H:/genre folders/Hip-Hop_Rap, Music/Dip - Tyga ft. Nicki Minaj (lyrics).wav"
match = predict_song(audio_path, output_h5)
print(f"Predicted match: {match}")
