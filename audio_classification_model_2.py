import os
import librosa
import numpy as np
import subprocess
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# Initialize the scaler
scaler = StandardScaler()

# Path to your audio dataset (songs used for training)
audio_dataset_path = 'H:\\genre folders'
# Path to the 20-hour DJ mix
dj_mix_path = "H:/(Temporary) Radio Recordings/Joshua Baraka - NANA Remix (Feat. Joeboy, King Promise & BIEN) (Official Video).wav"


# Function to split the large MP3 file into smaller segments using ffmpeg and save them in a new folder
def split_audio(input_file, segment_length=180):
    # Create a new folder for the segments based on the original file name
    file_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.join(os.path.dirname(input_file), f"{file_name}_wav_segments")

    # Check if the output directory already exists and has files in it
    if os.path.exists(output_dir) and len(os.listdir(output_dir)) > 0:
        print(f"Segments for {file_name} already exist. Skipping splitting.")
        return output_dir

    os.makedirs(output_dir, exist_ok=True)

    try:
        # Command to split the file using ffmpeg and save directly to WAV
        ffmpeg_command = [
            'ffmpeg', '-i', input_file, '-f', 'segment', '-segment_time', str(segment_length),
            '-c', 'pcm_s16le', '-ar', '44100', os.path.join(output_dir, 'segment_%03d.wav')
        ]
        subprocess.run(ffmpeg_command, check=True)
        print(f"Audio split into {segment_length // 60} minute WAV segments and saved in {output_dir}")
        return output_dir
    except subprocess.CalledProcessError as e:
        print(f"Error splitting audio: {e}")
        return None


# Extract features from a song or DJ mix segment
def feature_extractor(file, segment_length=180, sample_rate=44100):
    try:
        audio, sample_rate = librosa.load(file, sr=sample_rate, res_type='kaiser_fast')

        # Split the audio into segments
        segment_length = segment_length * sample_rate  # segment_length is in seconds
        num_segments = int(len(audio) / segment_length)
        all_features = []

        for i in range(num_segments):
            start = i * segment_length
            end = start + segment_length
            segment = audio[start:end]

            # Extract features
            mfccs = np.mean(librosa.feature.mfcc(y=segment, sr=sample_rate, n_mfcc=40).T, axis=0)
            chroma = np.mean(librosa.feature.chroma_stft(y=segment, sr=sample_rate).T, axis=0)
            mel = np.mean(librosa.feature.melspectrogram(y=segment, sr=sample_rate).T, axis=0)
            contrast = np.mean(librosa.feature.spectral_contrast(y=segment, sr=sample_rate).T, axis=0)
            tonnetz = np.mean(librosa.feature.tonnetz(y=librosa.effects.harmonic(segment), sr=sample_rate).T, axis=0)
            tempo, _ = librosa.beat.beat_track(y=segment, sr=sample_rate)

            stft = librosa.stft(segment)
            stft_magnitude, stft_phase = np.abs(stft), np.angle(stft)

            stft_magnitude_mean = np.mean(stft_magnitude, axis=1)
            stft_phase_mean = np.mean(stft_phase, axis=1)

            # Combine features
            combined_features = np.hstack((
                mfccs.flatten(), chroma.flatten(), mel.flatten(), contrast.flatten(), tonnetz.flatten(),
                np.array([tempo]).flatten(),
                stft_magnitude_mean.flatten(), stft_phase_mean.flatten()
            ))

            all_features.append(combined_features)

        if len(all_features) == 0:
            return None
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
def process_dj_mix(dj_mix_path, training_songs, segment_length=180):
    # Split the DJ mix into smaller segments
    segment_dir = split_audio(dj_mix_path, segment_length)

    if segment_dir is None:
        print("Audio splitting failed.")
        return

    # Extract features from each segment of the DJ mix
    predictions = []
    for segment_file in sorted(os.listdir(segment_dir)):
        segment_path = os.path.join(segment_dir, segment_file)
        dj_mix_features = feature_extractor(segment_path, segment_length)

        if dj_mix_features is None:
            print(f"Could not extract features from {segment_path}")
            continue

        # Fit the scaler using training song features
        all_features = np.array(list(training_songs.values()))

        # Ensure that all features are the same length
        if not all(len(f) == len(all_features[0]) for f in all_features):
            print("Inconsistent feature lengths found in training data.")
            return None

        scaler.fit(all_features)

        # Scale both training songs and DJ mix features
        scaled_training_songs = {song: scaler.transform([features])[0] for song, features in training_songs.items()}
        dj_mix_features_scaled = scaler.transform([dj_mix_features])

        # Predict song presence for each DJ mix segment
        closest_match = None
        highest_similarity = -1

        # Compare the DJ mix segment to each training song using cosine similarity
        for song, features in scaled_training_songs.items():
            similarity = cosine_similarity([dj_mix_features_scaled[0]], [features])[0][0]
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
    predicted_songs = process_dj_mix(dj_mix_path, training_songs, segment_length=180)

    # Output the predictions
    print("Predicted songs in the DJ mix:")
    for song in predicted_songs:
        print(song)
