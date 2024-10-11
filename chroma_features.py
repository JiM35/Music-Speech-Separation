import os
import librosa
import numpy as np
import h5py
from scipy.signal import savgol_filter
from sklearn.metrics.pairwise import cosine_similarity


# Function to extract chroma features from an audio file
def extract_chroma_features(audio_path):
    y, sr = librosa.load(audio_path)
    # Extract chroma feature (24-dimensional)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_chroma=24)

    # Smooth the chroma features using a Savitzky-Golay filter across each chroma bin
    smoothed_chroma = savgol_filter(chroma, window_length=7, polyorder=2, axis=1)

    # Generate time corresponding to each chroma frame
    chroma_times = librosa.frames_to_time(np.arange(smoothed_chroma.shape[1]), sr=sr)

    return smoothed_chroma, chroma_times  # Return the full chroma feature set


# Save chroma features for all training songs, skipping already processed files
def save_chroma_data(genre_folder, output_h5):
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
                        chroma_features, chroma_times = extract_chroma_features(song_path)

                        if chroma_features is not None:
                            # Store chroma features and times in the HDF5 file
                            song_group = genre_group.create_group(song_file)
                            song_group.create_dataset('chroma_features', data=chroma_features)
                            song_group.create_dataset('chroma_times', data=chroma_times)
                            print(f"Processed: {song_file}")
                        else:
                            print(f"Skipped: {song_file} (No chroma data)")


# Predict song by matching chroma features with cosine similarity
def predict_song(audio_path, output_h5):
    new_chroma_features, _ = extract_chroma_features(audio_path)

    if new_chroma_features is None:
        return "No chroma data detected in the song."

    # Average the new chroma features across frames to get a single vector
    new_chroma_features_mean = np.mean(new_chroma_features, axis=1).reshape(1, -1)

    # Open the HDF5 file to access stored chroma data
    with h5py.File(output_h5, 'r') as h5_file:
        best_match = None
        best_similarity = -1.0  # Similarity score, where higher is better

        for genre in h5_file:
            genre_group = h5_file[genre]

            for song_file in genre_group:
                song_group = genre_group[song_file]
                stored_chroma_features = np.array(song_group['chroma_features'])

                # Average stored chroma features across frames
                stored_chroma_features_mean = np.mean(stored_chroma_features, axis=1).reshape(1, -1)

                # Calculate cosine similarity using the averaged chroma features
                similarity = cosine_similarity(new_chroma_features_mean, stored_chroma_features_mean)[0][0]

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (genre, song_file, similarity)

        return best_match if best_match else "No match found"


genre_folder = "H:/genre folders"
output_h5 = "chroma_data.h5"

# Save chroma data of training songs, skipping already processed files
save_chroma_data(genre_folder, output_h5)

# Predict new song
audio_path = ("H:/(Temporary) Radio Recordings/soundcityfmnrb started 04-53-30 am ended 9-59-39 "
              "am_wav_segments/segment_006.wav")
match = predict_song(audio_path, output_h5)
print(f"Predicted match: {match}")
