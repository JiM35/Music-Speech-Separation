import librosa
import numpy as np
import matplotlib.pyplot as plt
import datetime

import pandas as pd
from scipy.signal import savgol_filter

# Load the audio file
audio_path = "H:/(Temporary) Radio Recordings/soundcityfmnrb started 04-53-30 am ended 9-59-39 am.mp3"
y, sr = librosa.load(audio_path)

# Define the frame length and hop length
frame_length = 512  # Increased frame length for more smoothing
hop_length = 2048  # Increased hop length for fewer transitions

# Calculate the RMS energy
rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

# Compute time frames corresponding to RMS values
frames = range(len(rms))
t = librosa.frames_to_time(frames, sr=sr, hop_length=hop_length)

# Smooth the RMS energy using a Savitzky-Golay filter
rms_smooth = savgol_filter(rms, window_length=51, polyorder=2)

# Set a threshold for detecting low-energy segments (gaps)
energy_threshold = np.median(rms_smooth) * 0.5  # Adjust depending on audio characteristics
low_energy_indices = np.where(rms_smooth < energy_threshold)[0]

# Group consecutive low-energy indices as one transition
min_gap_duration = 10  # Minimum gap duration between songs in seconds
gap_frames = librosa.time_to_frames(min_gap_duration, sr=sr, hop_length=hop_length)

filtered_transitions = [low_energy_indices[0]]
for i in range(1, len(low_energy_indices)):
    if low_energy_indices[i] - low_energy_indices[i - 1] > gap_frames:
        filtered_transitions.append(low_energy_indices[i])

# Convert frames to times
transition_times = librosa.frames_to_time(filtered_transitions, sr=sr, hop_length=hop_length)


# Function to convert seconds to hh:mm:ss
def seconds_to_hms(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))


# Print the timings of the detected transitions in hh:mm:ss format
print("Filtered transition times (hh:mm:ss):")
for time in transition_times:
    print(seconds_to_hms(time))

# Plot the RMS energy and detected transitions
plt.figure(figsize=(10, 6))
plt.plot(t, rms, label='RMS Energy')
plt.scatter(librosa.frames_to_time(filtered_transitions, sr=sr, hop_length=hop_length),
            rms[filtered_transitions], color='red', label='Detected Transitions', zorder=2)
plt.xlabel('Time (s)')
plt.ylabel('RMS Energy')
plt.title('RMS Energy with Detected Gaps (Transitions)')
plt.legend()
plt.show()

# --------------------------------------
# Tempo/Beat Detection
# --------------------------------------
# Detect tempo and beats
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)

# Compute time values for each beat
beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop_length)

# Compute the time intervals between consecutive beats
beat_intervals = np.diff(beat_times)

# Convert beat intervals to tempo (BPM)
# (60 seconds / beat interval in seconds) gives the BPM at each beat interval
tempo_over_time = 60.0 / beat_intervals

# Define a threshold for significant tempo changes
tempo_change_threshold = 100  # Adjust as necessary
significant_tempo_changes = np.where(np.abs(np.diff(tempo_over_time)) > tempo_change_threshold)[0]

# Print detected tempo changes
print("\nDetected tempo changes (BPM):")
for change in significant_tempo_changes:
    print(f"Time: {seconds_to_hms(beat_times[change])}, BPM: {tempo_over_time[change]}")

# Plot the raw tempo changes over time
plt.figure(figsize=(10, 6))
if len(tempo_over_time) > 0:
    plt.plot(beat_times[1:], tempo_over_time, label='Raw BPM Changes')
else:
    print("No significant tempo changes detected.")
plt.axhline(y=tempo_change_threshold, color='red', linestyle='--', label='Significant Change Threshold')
plt.xlabel('Time (s)')
plt.ylabel('BPM')
plt.title('Tempo Changes Over Time')
plt.legend()
plt.show()

# --------------------------------------
# Harmonic/Key Changes (Chroma)
# --------------------------------------
chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop_length)
chroma_diff = np.sum(np.abs(np.diff(chroma, axis=1)), axis=0)  # Sum of changes between frames

# Detect significant harmonic/key changes
key_change_threshold = np.median(chroma_diff) * 1.5  # Adjust based on audio characteristics
significant_key_changes = np.where(chroma_diff > key_change_threshold)[0]

# Convert chroma frames to time
key_change_times = librosa.frames_to_time(significant_key_changes, sr=sr, hop_length=hop_length)

# Calculate magnitude of change
change_magnitude = chroma_diff[significant_key_changes]

# Calculate frequency of changes
change_frequency = len(significant_key_changes) / (len(chroma_diff) * (hop_length / sr))

# Calculate average magnitude of changes
average_change_magnitude = np.mean(change_magnitude)

# Calculate duration of stability before each change
stability_durations = np.diff(significant_key_changes, prepend=0) * (hop_length / sr)

# Prepare data for printing
data = {
    'Time (hh:mm:ss)': [seconds_to_hms(time) for time in key_change_times],
    'Magnitude': change_magnitude,
    'Stability Duration (s)': stability_durations[:len(change_magnitude)]  # Adjust to match the number of changes
}

# Create a DataFrame
df = pd.DataFrame(data)

# Print detected key changes and additional metrics
print("\nDetected harmonic/key changes:")
print(df.to_string(index=False))  # Print DataFrame without index

# Print additional metrics
print(f"\nTotal significant key changes: {len(significant_key_changes)}")
print(f"Average change magnitude: {average_change_magnitude:.4f}")
print(f"Change frequency (per minute): {change_frequency * 60:.4f} changes/min")

# Plot chroma changes and detected key changes
plt.figure(figsize=(10, 6))
plt.plot(librosa.frames_to_time(range(len(chroma_diff)), sr=sr, hop_length=hop_length), chroma_diff,
         label='Chroma Change')
plt.scatter(key_change_times, change_magnitude, color='orange', label='Detected Key Changes',
            zorder=2)
plt.axhline(y=key_change_threshold, color='green', linestyle='--', label='Key Change Threshold')
plt.xlabel('Time (s)')
plt.ylabel('Chroma Change Magnitude')
plt.title('Harmonic/Key Changes Over Time')
plt.legend()
plt.show()

