
import os
import hashlib
from collections import defaultdict

def get_file_hash(filepath):
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while True:
                buf = f.read(65536)
                if not buf:
                    break
                hasher.update(buf)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error hashing {filepath}: {e}")
        return None

def find_duplicate_files(search_dirs):
    hash_map = defaultdict(list)
    print(f"Scanning directories: {search_dirs}")
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            print(f"Directory not found: {search_dir}")
            continue
            
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.lower().endswith('.dxf'):
                    path = os.path.join(root, file)
                    print(f"Hashing: {path}")
                    file_hash = get_file_hash(path)
                    if file_hash:
                        hash_map[file_hash].append(path)
                        
    return {k: v for k, v in hash_map.items() if len(v) > 1}

if __name__ == "__main__":
    duplicates = find_duplicate_files(['cad', 'output'])
    
    if duplicates:
        print("\nFound duplicate files:")
        for h, paths in duplicates.items():
            print(f"Hash: {h}")
            for p in paths:
                print(f"  - {p}")
    else:
        print("\nNo duplicate files found.")
