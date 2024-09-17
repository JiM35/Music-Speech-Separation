import os
import librosa
import numpy as np
import subprocess
import h5py
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# Initialize the scaler
scaler = StandardScaler()

# Path to your audio dataset (songs used for training)
audio_dataset_path = 'H:\\genre folders'
# Path to the 20-hour DJ mix
dj_mix_path = "H:/(Temporary) Radio Recordings/Rema, Shallipopi - BENIN BOYS.wav"
# Path to HDF5 file for storing features
hdf5_path = 'audio_features.h5'


# Function to split the large MP3 file into overlapping smaller segments using ffmpeg and save them in a new folder
def split_audio(input_file, segment_length=180, overlap=0.5):
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
        print(f"Audio split into {segment_length // 60} minute WAV segments with {int(overlap * 100)}% overlap and saved in {output_dir}")
        return output_dir
    except subprocess.CalledProcessError as e:
        print(f"Error splitting audio: {e}")
        return None


# Function to extract and save features to HDF5
def feature_extractor(file, sample_rate=44100):
    try:
        audio, sample_rate = librosa.load(file, sr=sample_rate, res_type='kaiser_fast')

        mfccs = np.mean(librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=40).T, axis=0)
        chroma = np.mean(librosa.feature.chroma_stft(y=audio, sr=sample_rate).T, axis=0)
        mel = np.mean(librosa.feature.melspectrogram(y=audio, sr=sample_rate).T, axis=0)
        contrast = np.mean(librosa.feature.spectral_contrast(y=audio, sr=sample_rate).T, axis=0)
        tonnetz = np.mean(librosa.feature.tonnetz(y=librosa.effects.harmonic(audio), sr=sample_rate).T, axis=0)
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sample_rate)

        stft = librosa.stft(audio)
        stft_magnitude, stft_phase = np.abs(stft), np.angle(stft)

        stft_magnitude_mean = np.mean(stft_magnitude, axis=1)
        stft_phase_mean = np.mean(stft_phase, axis=1)

        combined_features = np.hstack((
            mfccs.flatten(), chroma.flatten(), mel.flatten(), contrast.flatten(), tonnetz.flatten(),
            np.array([tempo]).flatten(), stft_magnitude_mean.flatten(), stft_phase_mean.flatten()
        ))

        return combined_features

    except Exception as e:
        print(f"Error processing {file}: {e}")
        return None


# Save features to HDF5
def save_features_to_hdf5(hdf5_file, song_name, features):
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


# Process the DJ mix and predict which songs are present
def process_dj_mix(dj_mix_path, training_songs):
    segment_dir = split_audio(dj_mix_path)

    if segment_dir is None:
        print("Audio splitting failed.")
        return

    predictions = []
    segment_number = 1
    for segment_file in sorted(os.listdir(segment_dir)):
        segment_path = os.path.join(segment_dir, segment_file)
        dj_mix_features = feature_extractor(segment_path)

        if dj_mix_features is None:
            print(f"Could not extract features from {segment_path}")
            continue

        all_features = np.array(list(training_songs.values()))

        if not all(len(f) == len(all_features[0]) for f in all_features):
            print("Inconsistent feature lengths found in training data.")
            return None

        scaler.fit(all_features)

        scaled_training_songs = {song: scaler.transform([features])[0] for song, features in training_songs.items()}
        dj_mix_features_scaled = scaler.transform([dj_mix_features])

        closest_match = None
        highest_similarity = -1

        for song, features in scaled_training_songs.items():
            similarity = cosine_similarity([dj_mix_features_scaled[0]], [features])[0][0]
            if similarity > highest_similarity:
                highest_similarity = similarity
                closest_match = song

        predictions.append((segment_number, closest_match))
        segment_number += 1

    return predictions


def load_training_songs(audio_dataset_path, hdf5_path):
    training_songs = {}
    for genre in os.listdir(audio_dataset_path):
        genre_path = os.path.join(audio_dataset_path, genre)
        if os.path.isdir(genre_path):
            for file in os.listdir(genre_path):
                file_path = os.path.join(genre_path, file)
                song_name = os.path.splitext(file)[0]

                features = load_features_from_hdf5(hdf5_path, song_name)
                if features is None:  # If not found in HDF5, extract and save
                    features = feature_extractor(file_path)
                    if features is not None:
                        save_features_to_hdf5(hdf5_path, song_name, features)

                if features is not None:
                    training_songs[song_name] = features
    return training_songs


# Main script execution
if __name__ == "__main__":
    print("Loading training songs...")
    training_songs = load_training_songs(audio_dataset_path, hdf5_path)

    print("Processing the DJ mix...")
    predicted_songs = process_dj_mix(dj_mix_path, training_songs)

    if predicted_songs:
        print("Predicted songs in the DJ mix:")
        for segment_number, song in predicted_songs:
            print(f"Segment {segment_number} was predicted to have the song: {song}")
    else:
        print("No songs were predicted.")
