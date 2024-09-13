import json
import webbrowser
import keyboard

# Paths to the JSON files
file_path = 'JSON files/audio_identification_results.json'
output_path = 'JSON files/unique_audio_pairs.json'

# Recursive function to find a key in nested dictionaries
def find_key(data, target_key):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                return value
            found = find_key(value, target_key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = find_key(item, target_key)
            if found is not None:
                return found
    return None

# Function to extract information from a segment
def extract_info(segment):
    try:
        artist = find_key(segment, "artist")
        title = find_key(segment, "title")
        genre_names = find_key(segment, "genreNames")
        duration_ms = find_key(segment, "duration_ms")  # Extracting the duration in ms

        # Include segment if at least one of the fields is found
        if artist or title or genre_names:
            return {
                "artist": artist,
                "title": title,
                "genreNames": genre_names,
                "duration_ms": duration_ms  # Adding duration to the output
            }
        else:
            return None
    except Exception as e:
        # Print error details if needed for debugging
        print(f"Error extracting info: {e}")
        return None

# Read and parse the JSON file
with open(file_path, 'r') as file:
    data = json.load(file)

# Ask user if they want to search the entire file regardless of 'searched' flag
search_all = input("Do you want to search the entire file regardless of whether they were searched? (y/n): ").strip().lower()

# Check if the data is a list of segments
if isinstance(data, list):
    # Use a set to collect unique (artist, title, genreNames, duration_ms) tuples
    unique_pairs = set()
    search_queries = []

    for segment in data:
        # Only skip segments if user chose not to search all
        if not search_all == 'y' and segment.get("searched"):
            continue
        info = extract_info(segment)
        if info is not None:
            # Convert genreNames to a tuple to make it hashable
            genre_names_tuple = tuple(info['genreNames']) if info['genreNames'] else ()
            pair = (info['artist'], info['title'], genre_names_tuple, info['duration_ms'])
            if pair not in unique_pairs:
                unique_pairs.add(pair)
                search_queries.append(f"{info['artist']} {info['title']}")

    # Convert the set to a list of dictionaries for JSON serialization
    unique_pairs_list = [{
        "artist": artist,
        "title": title,
        "genreNames": list(genre_names),
        "duration_ms": duration_ms
    } for artist, title, genre_names, duration_ms in unique_pairs]

    # Save the unique pairs to a new JSON file
    with open(output_path, 'w') as output_file:
        json.dump(unique_pairs_list, output_file, indent=4)

    # Print the unique pairs to the console
    print("Unique (artist, title, genreNames, duration_ms) pairs:")
    for artist, title, genre_names, duration_ms in unique_pairs:
        print(f"Artist: {artist}, Title: {title}, Genre Names: {genre_names}, Duration: {duration_ms} ms")

    # Prompt the user to choose whether to perform YouTube search or not
    perform_search = input("Do you want to perform a YouTube search on the unique pairs? (y/n): ").strip().lower()

    if perform_search == 'y':
        # Function to open a YouTube search and mark the segment as searched
        def open_search():
            if search_queries:
                search_query = search_queries.pop(0)
                url = f"https://www.youtube.com/results?search_query={search_query}"
                webbrowser.open(url)
                print(f"Opened search for: {search_query}")

                # Mark all matching segments as searched
                for segment in data:
                    artist = find_key(segment, "artist")
                    title = find_key(segment, "title")
                    if artist and title and f"{artist} {title}" == search_query:
                        segment["searched"] = True

                # Save the updated JSON file
                with open(file_path, 'w') as file:
                    json.dump(data, file, indent=4)

                # Update the unique pairs file
                unique_pairs = set()
                for segment in data:
                    if segment.get("searched"):
                        info = extract_info(segment)
                        if info is not None:
                            genre_names_tuple = tuple(info['genreNames']) if info['genreNames'] else ()
                            unique_pairs.add((info['artist'], info['title'], genre_names_tuple, info['duration_ms']))

                unique_pairs_list = [{
                    "artist": artist,
                    "title": title,
                    "genreNames": list(genre_names),
                    "duration_ms": duration_ms
                } for artist, title, genre_names, duration_ms in unique_pairs]

                with open(output_path, 'w') as output_file:
                    json.dump(unique_pairs_list, output_file, indent=4)

                # Print updated unique pairs to verify
                print("Updated unique (artist, title, genreNames, duration_ms) pairs:")
                for artist, title, genre_names, duration_ms in unique_pairs:
                    print(f"Artist: {artist}, Title: {title}, Genre Names: {genre_names}, Duration: {duration_ms} ms")

            else:
                print("No more search queries available. Press 'esc' to exit the script.")

        # Set up the keyboard shortcut (e.g., "ctrl+shift+s")
        keyboard.add_hotkey('ctrl+shift+s', open_search)
        print("Press 'ctrl+shift+s' to open the next YouTube search.")

        # Keep the script running to listen for the keyboard shortcut
        keyboard.wait('esc')  # Press 'esc' to exit the script

else:
    print("The JSON data does not contain a list of segments.")
