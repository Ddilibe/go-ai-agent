#!/usr/bin/env python3

class IllegalMoveError(Exception):
    
    def __init__(self, *args: object) -> None:
        message = ["Illegal Move", *args]
        super().__init__(*message)
        
class MusicFileNotFoundError(FileNotFoundError):
    """
    Custom exception raised when an attempt is made to load a music file
    that does not exist at the specified path.
    """
    def __init__(self, file_path, message="Music file not found at the specified path"):
        self.file_path = file_path
        # You can customize the message to be more specific
        full_message = f"{message}: '{file_path}'"
        
        # Call the base class constructor
        super().__init__(full_message)

# # --- Example Usage ---

# def load_music_file(filename):
#     """Simulates trying to load a file."""
#     # In a real application, you would use os.path.exists(filename) here
#     is_file_missing = True # Force the error for demonstration
    
#     if is_file_missing:
#         # Raise the custom exception
#         raise MusicFileNotFoundError(filename)
    
#     return f"Successfully loaded {filename}"

# # Handle the specific custom exception
# try:
#     file_to_load = "my_favorite_song.mp3"
#     print(f"Attempting to load: {file_to_load}")
#     load_music_file(file_to_load)
    
# except MusicFileNotFoundError as e:
#     # Handle the custom error gracefully
#     print("\n--- ERROR ---")
#     print(f"Failed to load music file: {e}")
#     print(f"Checked Path: {e.file_path}")
#     print("Please check your file path and try again.")
#     print("-------------")