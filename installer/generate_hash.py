
import hashlib
import sys
import os

def calculate_sha256(filepath):
    """Calculates the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest().lower()

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_hash.py <file_path>")
        return

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return

    hash_val = calculate_sha256(filepath)
    filename = os.path.basename(filepath)
    
    # Output in standard format: <hash>  <filename>
    output = f"{hash_val}  {filename}"
    print(output)
    
    # Save to file
    output_file = filepath + ".sha256.txt"
    with open(output_file, "w") as f:
        f.write(output)
    
    print(f"Hash saved to: {output_file}")

if __name__ == "__main__":
    main()
