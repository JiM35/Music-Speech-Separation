import librosa
import numpy as np
import matplotlib.pyplot as plt
import datetime

import pandas as pd
from scipy.signal import savgol_filter

# Load the audio file
audio_path = "H:/experiment_songs/combined_audio.wav"
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

# Initialize an empty list to store the indices of detected transitions
filtered_transitions = []

# Find continuous low-energy segments
start_idx = low_energy_indices[0]
for i in range(1, len(low_energy_indices)):
    if low_energy_indices[i] - low_energy_indices[i - 1] > gap_frames:
        # End of a low-energy segment, find the minimum RMS energy point in this segment
        segment = rms_smooth[start_idx:low_energy_indices[i - 1] + 1]
        min_energy_idx = np.argmin(segment) + start_idx  # Find index of minimum RMS in the segment
        filtered_transitions.append(min_energy_idx)
        start_idx = low_energy_indices[i]  # Start new segment

# Make sure to add the last segment
segment = rms_smooth[start_idx:low_energy_indices[-1] + 1]
min_energy_idx = np.argmin(segment) + start_idx
filtered_transitions.append(min_energy_idx)

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
