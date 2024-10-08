# convert_videos_to_MP3.py

import ffmpeg
import os


def convert_to_mp3(input_file, output_file):
    try:
        # Run ffmpeg to convert video file to mp3
        ffmpeg.input(input_file).output(output_file, **{'q:a': 0, 'map': 'a'}).run()
        print(f"Successfully converted {input_file} to {output_file}")
    except ffmpeg.Error as e:
        print(f"An error occurred: {e.stderr.decode()}")


def convert_files_in_directory(input_directory, output_directory, extensions=['.mkv', '.mp4']):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for filename in os.listdir(input_directory):
        # Check if the file has the correct extension
        if any(filename.lower().endswith(ext) for ext in extensions):
            input_file = os.path.join(input_directory, filename)
            output_file = os.path.join(output_directory, os.path.splitext(filename)[0] + ".mp3")

            # Check if the output file already exists
            if os.path.exists(output_file):
                print(f"File {output_file} already exists. Skipping conversion.")
                continue

            convert_to_mp3(input_file, output_file)


if __name__ == "__main__":
    # path/to/video/files
    input_directory = "I:/Tutorials/Radio Music Speech Separation/datasets/music (1)"
    # path/to/output/directory
    output_directory = "H:/datasets/music (1)"

    convert_files_in_directory(input_directory, output_directory)