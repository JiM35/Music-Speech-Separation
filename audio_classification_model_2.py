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
dj_mix_path = "H:/(Temporary) Radio Recordings/Rema, Shallipopi - BENIN BOYS.wav"


# Function to split the large MP3 file into overlapping smaller segments using ffmpeg and save them in a new folder
def split_audio(input_file, segment_length=180, overlap=0.5):
    # Create a new folder for the segments based on the original file name
    file_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.join(os.path.dirname(input_file), f"{file_name}_wav_segments")

    # Check if the output directory already exists and has files in it
    if os.path.exists(output_dir) and len(os.listdir(output_dir)) > 0:
        print(f"Segments for {file_name} already exist. Skipping splitting.")
        return output_dir

    os.makedirs(output_dir, exist_ok=True)

    try:
        # Calculate segment start times based on overlap
        segment_offset = int(segment_length * (1 - overlap))  # Overlap as a fraction of the segment length
        segment_duration_str = str(segment_length)
        segment_offset_str = str(segment_offset)

        # Command to split the file using ffmpeg and save directly to WAV with overlapping segments
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


# Extract features from a song or DJ mix segment based on its actual length
def feature_extractor(file, sample_rate=44100):
    try:
        audio, sample_rate = librosa.load(file, sr=sample_rate, res_type='kaiser_fast')

        # Extract features
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

        # Combine features
        combined_features = np.hstack((
            mfccs.flatten(), chroma.flatten(), mel.flatten(), contrast.flatten(), tonnetz.flatten(),
            np.array([tempo]).flatten(),
            stft_magnitude_mean.flatten(), stft_phase_mean.flatten()
        ))

        return combined_features

    except Exception as e:
        print(f"Error processing {file}: {e}")
        return None


# Process the DJ mix and predict which songs are present
def process_dj_mix(dj_mix_path, training_songs):
    # Split the DJ mix into smaller segments
    segment_dir = split_audio(dj_mix_path)

    if segment_dir is None:
        print("Audio splitting failed.")
        return

    # Extract features from each segment of the DJ mix
    predictions = []
    segment_number = 1  # Start segment numbering from 1
    for segment_file in sorted(os.listdir(segment_dir)):
        segment_path = os.path.join(segment_dir, segment_file)
        dj_mix_features = feature_extractor(segment_path)

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

        predictions.append((segment_number, closest_match))
        segment_number += 1  # Increment segment number

    return predictions


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


# Main script execution
if __name__ == "__main__":
    # Load and prepare training songs
    print("Loading training songs...")
    training_songs = load_training_songs(audio_dataset_path)

    # Process the DJ mix and predict songs
    print("Processing the DJ mix...")
    predicted_songs = process_dj_mix(dj_mix_path, training_songs)

    # Output the predictions
    if predicted_songs:
        print("Predicted songs in the DJ mix:")
        for segment_number, song in predicted_songs:
            print(f"Segment {segment_number} was predicted to have the song: {song}")
    else:
        print("No songs were predicted.")
