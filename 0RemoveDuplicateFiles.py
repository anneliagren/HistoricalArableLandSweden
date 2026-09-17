import os
import hashlib

def file_hash(filepath):
    """Compute the MD5 hash of the specified file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def remove_duplicates(folder_path):
    """Remove duplicate files in the specified folder, keeping the most recent one."""
    hashes = {}
    for root, _, files in os.walk(folder_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            print(f"Processing file: {filepath}")  # Print the name of the file being processed
            filehash = file_hash(filepath)
            file_mtime = os.path.getmtime(filepath)
            if filehash in hashes:
                existing_file, existing_mtime = hashes[filehash]
                if file_mtime > existing_mtime:
                    print(f"Duplicate found: {existing_file} (keeping {filepath})")
                    os.remove(existing_file)
                    hashes[filehash] = (filepath, file_mtime)
                else:
                    print(f"Duplicate found: {filepath} (keeping {existing_file})")
                    os.remove(filepath)
            else:
                hashes[filehash] = (filepath, file_mtime)

# Define the folder path
folder_path = '/workspace/data/AllMapsInOneFolder/'

# Remove duplicates
remove_duplicates(folder_path)