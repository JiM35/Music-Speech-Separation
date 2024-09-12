import os
import librosa
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import subprocess

# Initialize the scaler
scaler = StandardScaler()

# Path to your audio dataset (songs used for training)
audio_dataset_path = 'H:\\genre folders'
# Path to the 20-hour DJ mix
dj_mix_path = "H:\\(Temporary) Radio Recordings\\soundcityfmnrb started 05-40-03 am ended 1-40-03 am.mp3"


# Function to convert MP3 to WAV using ffmpeg
def convert_mp3_to_wav(mp3_file):
    wav_file = mp3_file.replace('.mp3', '.wav')
    if not os.path.exists(wav_file):
        command = f"ffmpeg -i \"{mp3_file}\" \"{wav_file}\""
        try:
            subprocess.run(command, shell=True, check=True)
        except Exception as e:
            print(f"Error converting {mp3_file} to WAV: {e}")
            return None
    return wav_file


# Extract features from a song or DJ mix segment
def feature_extractor(file, segment_length=60, sample_rate=22050):
    try:
        # Convert to WAV if needed
        if file.endswith('.mp3'):
            file = convert_mp3_to_wav(file)
            if file is None:
                return None

        audio, sample_rate = librosa.load(file, sr=sample_rate, res_type='kaiser_fast')

        # Split the audio into segments
        segment_length = segment_length * sample_rate  # segment_length is in seconds
        num_segments = int(len(audio) / segment_length)
        all_features = []

        for i in range(num_segments):
            start = i * segment_length
            end = start + segment_length
            segment = audio[start:end]

            # Extract features as done in the training phase
            mfccs = np.mean(librosa.feature.mfcc(y=segment, sr=sample_rate, n_mfcc=40).T, axis=0)
            chroma = np.mean(librosa.feature.chroma_stft(y=segment, sr=sample_rate).T, axis=0)
            mel = np.mean(librosa.feature.melspectrogram(y=segment, sr=sample_rate).T, axis=0)
            contrast = np.mean(librosa.feature.spectral_contrast(y=segment, sr=sample_rate).T, axis=0)
            tonnetz = np.mean(librosa.feature.tonnetz(y=librosa.effects.harmonic(segment), sr=sample_rate).T, axis=0)
            tempo, _ = librosa.beat.beat_track(y=segment, sr=sample_rate)

            stft = librosa.stft(segment)
            stft_magnitude, stft_phase = np.abs(stft), np.angle(stft)

            stft_magnitude_mean = np.mean(stft_magnitude, axis=1)
            stft_magnitude_var = np.var(stft_magnitude, axis=1)
            stft_phase_mean = np.mean(stft_phase, axis=1)
            stft_phase_var = np.var(stft_phase, axis=1)

            combined_features = np.hstack((
                mfccs.flatten(), chroma.flatten(), mel.flatten(), contrast.flatten(), tonnetz.flatten(),
                np.array([tempo]).flatten(),
                stft_magnitude_mean.flatten(), stft_magnitude_var.flatten(),
                stft_phase_mean.flatten(), stft_phase_var.flatten()
            ))

            all_features.append(combined_features)

        # Average the features across all segments
        aggregated_features = np.mean(all_features, axis=0)
        return aggregated_features

    except Exception as e:
        print(f"Error processing {file}: {e}")
        return None


# Load and extract features for each song in the training dataset
def load_training_songs(audio_dataset_path):
    training_songs = {}
    for genre in os.listdir(audio_dataset_path):
        genre_path = os.path.join(audio_dataset_path, genre)
        if os.path.isdir(genre_path):
            for file in os.listdir(genre_path):
                file_path = os.path.join(genre_path, file)
                features = feature_extractor(file_path)
                if features is not None:
                    training_songs[file] = features
    return training_songs


# Extract features for the DJ mix and predict which songs are present
def process_dj_mix(dj_mix_path, training_songs, segment_length=60):
    # Extract features from the DJ mix
    dj_mix_features = feature_extractor(dj_mix_path, segment_length)

    if dj_mix_features is None:
        print(f"Could not extract features from {dj_mix_path}")
        return

    # Fit the scaler using training song features
    all_features = np.array(list(training_songs.values()))
    scaler.fit(all_features)

    # Scale both training songs and DJ mix features
    scaled_training_songs = {song: scaler.transform([features])[0] for song, features in training_songs.items()}
    dj_mix_features_scaled = scaler.transform([dj_mix_features])

    # Predict song presence for each DJ mix segment
    predictions = []
    for segment in dj_mix_features_scaled:
        closest_match = None
        highest_similarity = -1

        # Compare the DJ mix segment to each training song using cosine similarity
        for song, features in scaled_training_songs.items():
            similarity = cosine_similarity([segment], [features])[0][0]
            if similarity > highest_similarity:
                highest_similarity = similarity
                closest_match = song

        predictions.append(closest_match)

    return predictions


# Main script execution
if __name__ == "__main__":
    # Load and prepare training songs
    print("Loading training songs...")
    training_songs = load_training_songs(audio_dataset_path)

    # Process the DJ mix and predict songs
    print("Processing the DJ mix...")
    predicted_songs = process_dj_mix(dj_mix_path, training_songs, segment_length=60)

    # Output the predictions
    print("Predicted songs in the DJ mix:")
    for song in predicted_songs:
        print(song)
