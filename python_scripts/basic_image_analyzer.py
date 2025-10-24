import os
import re
from pathlib import Path
from PIL import Image
import numpy as np
import binascii

# Create results directory
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

# Supported image extensions
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}

def list_images():
    """Scan current directory for image files."""
    return [f for f in Path('.').glob('*') if f.suffix.lower() in IMAGE_EXTS]

def select_image(images):
    """Prompt user to select an image."""
    print("Available images:")
    for i, img in enumerate(images, 1):
        print(f"{i}. {img.name}")
    while True:
        try:
            choice = int(input("Select image number: ")) - 1
            if 0 <= choice < len(images):
                return images[choice]
            print("Invalid choice.")
        except ValueError:
            print("Enter a number.")

def decode_pixels(image_path):
    """Decode pixel values to hex and binary."""
    img = Image.open(image_path).convert('RGB')
    pixels = np.array(img)
    height, width, _ = pixels.shape

    # Get first 100 pixels or less for brevity
    pixel_subset = pixels[:min(10, height), :min(10, width), :].reshape(-1, 3)
    hex_output = []
    bin_output = []
    for r, g, b in pixel_subset:
        hex_val = f'{r:02x}{g:02x}{b:02x}'
        bin_val = f'{r:08b}{g:08b}{b:08b}'
        hex_output.append(hex_val)
        bin_output.append(bin_val)

    # Save pixel values
    with open(results_dir / f"{image_path.stem}_pixels.txt", 'w') as f:
        f.write("Hex Pixels:\n" + "\n".join(hex_output) + "\n\nBinary Pixels:\n" + "\n".join(bin_output))
    return hex_output, bin_output, pixels

def search_words(image_path):
    """Search for meaningful ASCII words in hex representation."""
    with open(image_path, 'rb') as f:
        data = f.read()
    hex_data = binascii.hexlify(data).decode('ascii')
    # Find ASCII strings (4+ characters)
    words = re.findall(r'[a-zA-Z0-9]{4,}', binascii.unhexlify(hex_data).decode('ascii', errors='ignore'))
    with open(results_dir / f"{image_path.stem}_words.txt", 'w') as f:
        f.write("Found Words:\n" + "\n".join(set(words)) if words else "No meaningful words found.")
    return words

def analyze_steganography(pixels, image_path):
    """Analyze for hidden messages or images using LSB."""
    height, width, _ = pixels.shape
    lsb_data = ""
    # Extract LSB from red channel of first 1000 pixels
    flat_pixels = pixels.reshape(-1, 3)[:1000]
    for r, _, _ in flat_pixels:
        lsb_data += str(r & 1)  # Get least significant bit
    # Try to decode as ASCII
    try:
        lsb_text = ''.join(chr(int(lsb_data[i:i+8], 2)) for i in range(0, len(lsb_data), 8))
        lsb_text = ''.join(c for c in lsb_text if c.isprintable())
        lsb_result = lsb_text if lsb_text.strip() else "No readable LSB message found."
    except:
        lsb_result = "No readable LSB message found."

    # Save LSB analysis
    with open(results_dir / f"{image_path.stem}_lsb.txt", 'w') as f:
        f.write(f"LSB Analysis (Red channel):\n{lsb_result}")

    # Check for hidden image patterns (e.g., high-frequency noise)
    pixel_diffs = np.abs(pixels[1:, :, :] - pixels[:-1, :, :]).mean()
    anomaly = "Possible hidden image" if pixel_diffs > 50 else "No obvious hidden image patterns."
    with open(results_dir / f"{image_path.stem}_anomaly.txt", 'w') as f:
        f.write(f"Pixel Difference Analysis:\n{anomaly}")

    return lsb_result, anomaly

def recolor_image(pixels, image_path):
    """Recolor image to amplify LSB differences."""
    modified = pixels.copy()
    # Amplify LSB by setting pixel to 255 if LSB is 1, else 0 (red channel)
    modified[:, :, 0] = np.where(pixels[:, :, 0] & 1, 255, 0)
    modified_img = Image.fromarray(modified)
    output_path = results_dir / f"{image_path.stem}_recolored.png"
    modified_img.save(output_path)
    return output_path

def main():
    images = list_images()
    if not images:
        print("No images found in directory.")
        return

    image_path = select_image(images)
    print(f"Processing {image_path}...")

    # Decode pixels
    hex_vals, bin_vals, pixels = decode_pixels(image_path)
    print(f"Pixel values saved to {results_dir / f'{image_path.stem}_pixels.txt'}")

    # Search for words
    words = search_words(image_path)
    print(f"Words found: {len(words)}. Saved to {results_dir / f'{image_path.stem}_words.txt'}")

    # Analyze steganography
    lsb_result, anomaly = analyze_steganography(pixels, image_path)
    print(f"LSB Analysis: {lsb_result}")
    print(f"Anomaly Analysis: {anomaly}")
    print(f"Results saved to {results_dir / f'{image_path.stem}_lsb.txt'} and {results_dir / f'{image_path.stem}_anomaly.txt'}")

    # Recolor image
    recolored_path = recolor_image(pixels, image_path)
    print(f"Recolored image saved to {recolored_path}")

if __name__ == "__main__":
    main()