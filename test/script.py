from pathlib import Path  # Import the object-oriented filesystem library

# Get the current working directory where the script is being run
current_dir = Path.cwd() 

# Get the name of the script currently being executed (e.g., 'myscript.py')
current_file = Path(__file__).name 

print(f"Files in {current_dir}:")

# Iterate through every file and folder in the current directory
for filepath in current_dir.iterdir():
    
    # Check if the current item is the script itself; if so, skip it
    if filepath.name == current_file:
        continue

    # Print the name of the found file or folder
    print(f"  - {filepath.name}")

    # Check if the item is a regular file (not a folder)
    if filepath.is_file():
        # Read the file's content as a string using UTF-8 encoding
        content = filepath.read_text(encoding='utf-8')
        print(f"    Content: {content}")
