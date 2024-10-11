import os
import ffmpeg


def combine_wav_files(folder_path, output_file="H:/experiment_songs/combined_audio.wav"):
    # Get a list of all .wav files in the specified folder
    wav_files = [f for f in os.listdir(folder_path) if f.endswith('.wav')]

    # Sort files to combine them in alphabetical or any desired order
    wav_files.sort()

    if not wav_files:
        print("No WAV files found in the folder.")
        return

    # Create the full paths for the input files
    input_paths = [os.path.join(folder_path, f) for f in wav_files]

    # Create a temporary text file to list the input files for ffmpeg
    with open("input.txt", "w") as f:
        for file in input_paths:
            f.write(f"file '{file}'\n")

    # Use ffmpeg to concatenate the wav files
    try:
        ffmpeg.input("input.txt", format='concat', safe=0).output(output_file, c='copy').run(overwrite_output=True)
        print(f"Combined audio saved as {output_file}")
    except ffmpeg.Error as e:
        print(f"Error occurred: {e}")
    finally:
        # Clean up the temporary text file
        if os.path.exists("input.txt"):
            os.remove("input.txt")


# Example usage
folder_path = "H:/experiment_songs"  # Replace with the folder containing your wav files
combine_wav_files(folder_path)
