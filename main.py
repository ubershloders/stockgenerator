import base64
import csv
import sys
from pathlib import Path
from typing import List

import requests

# API Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3-vl:4b"

# Output files
ADOBE_CSV_OUTPUT = "adobe_stock_upload.csv"
SHUTTERSTOCK_CSV_OUTPUT = "shutterstock_upload.csv"


# Shutterstock category keywords for automatic classification
SHUTTERSTOCK_CATEGORY_KEYWORDS = {
    "Nature": {
        "nature", "forest", "mountain", "sky", "tree", "trees", "water",
        "river", "sea", "ocean", "lake", "landscape", "sunset", "sunrise",
    },
    "People": {
        "person", "people", "man", "woman", "child", "children",
        "face", "portrait", "human",
    },
    "Technology": {
        "technology", "computer", "ai", "robot", "digital",
        "network", "data", "software", "hardware",
    },
    "Business/Finance": {
        "business", "finance", "office", "corporate",
        "money", "startup", "marketing", "economy",
    },
    "Food and drink": {
        "food", "drink", "meal", "coffee", "tea",
        "fruit", "vegetable", "restaurant", "cuisine",
    },
    "Animals/Wildlife": {
        "animal", "animals", "wildlife", "dog", "cat",
        "bird", "fish", "horse", "pet",
    },
    "Buildings/Landmarks": {
        "building", "buildings", "architecture", "city",
        "urban", "landmark", "skyscraper", "house",
    },
    "Backgrounds/Textures": {
        "background", "texture", "pattern", "wallpaper", "abstract",
    },
    "Sports/Recreation": {
        "sport", "sports", "fitness", "exercise",
        "training", "gym", "game",
    },
    "Healthcare/Medical": {
        "medical", "health", "doctor", "hospital",
        "medicine", "healthcare",
    },
}


def infer_shutterstock_categories(tags: List[str]) -> str:
    """Infer Shutterstock categories from image tags."""
    scores = {}
    for category, keywords in SHUTTERSTOCK_CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for tag in tags if tag in keywords)

    matched = [cat for cat, score in scores.items() if score > 0]
    matched.sort(key=lambda c: scores[c], reverse=True)

    return ", ".join(matched[:2])


def load_image(image_path: str) -> str:
    """Load and encode image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_image_keywords(image_path: str) -> List[str]:
    """Generate keywords for an image using vision model."""
    image_base64 = load_image(image_path)

    prompt = (
        "Analyze this image and generate between 15 and 40 relevant keywords. "
        "Keywords must be lowercase, single words or short compound words. "
        "Do not repeat words. Do not include camera info, brands, or unrelated concepts. "
        "Include both concrete elements and abstract concepts or moods if relevant. "
        "Return only a comma-separated list."
    )

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=550)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        raise

    raw = response.json().get("response", "")
    keywords = [k.strip() for k in raw.split(",") if k.strip()]

    # If we got very few or no keywords, try generating from description as fallback
    if len(keywords) < 5:
        keywords = generate_keywords_from_description(image_path)
    
    # Deduplicate and apply hard limit
    unique = list(dict.fromkeys(keywords))
    return unique[:50]


def generate_keywords_from_description(image_path: str) -> List[str]:
    """Generate keywords from image description as fallback."""
    description = generate_image_description(image_path)
    
    # Extract meaningful words from description
    # Remove common words and split
    common_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "is", "are", "was", "were", "be", "been", "have", "has",
        "this", "that", "these", "those", "it", "its", "as", "by", "from",
        "about", "into", "through", "during", "before", "after", "above",
        "below", "between", "under", "again", "further", "then", "once",
    }
    
    words = description.lower().split()
    keywords = [w.strip(".,!?;:") for w in words if w.lower().strip(".,!?;:") not in common_words and len(w) > 2]
    
    return list(dict.fromkeys(keywords))  # Remove duplicates while preserving order


def generate_image_description(image_path: str) -> str:
    """Generate a descriptive title for an image using vision model."""
    image_base64 = load_image(image_path)

    prompt = (
        "Write a single, clear, descriptive title for this stock image. "
        "It should read like a short headline or sentence, not a list of keywords. "
        "Describe who or what is shown, the setting, and the mood or concept if relevant. "
        "Do not include camera details, brands, or hashtags."
    )

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=180)
    response.raise_for_status()

    return response.json().get("response", "").strip() or "Stock image"


def main() -> None:
    """Main entry point: process images and generate CSV files."""
    image_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    # Collect all image files
    image_files = []
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp"):
        image_files.extend(sorted(image_dir.glob(ext)))

    adobe_rows = []
    shutterstock_rows = []

    # Process each image
    for idx, image_path in enumerate(image_files, 1):
        print(f"[{idx}/{len(image_files)}] {image_path.name}")

        try:
            keywords_list = generate_image_keywords(str(image_path))
            description = generate_image_description(str(image_path))
            categories = infer_shutterstock_categories(keywords_list)

            keywords = ", ".join(keywords_list)

            adobe_rows.append({
                "Filename": image_path.name,
                "Title": description,
                "Keywords": keywords,
                "Category": "3",
                "Releases": "Ivan Karpenko",
            })

            shutterstock_rows.append({
                "Filename": image_path.name,
                "Description": description,
                "Keywords": keywords,
                "Categories": categories,
                "Editorial": "no",
                "Mature content": "no",
                "illustration": "no",
            })

            print(f"  ✓ {description}")
            print(f"    Categories: {categories or 'none'}")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Write Adobe CSV
    with open(image_dir / ADOBE_CSV_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Filename", "Title", "Keywords", "Category", "Releases"],
        )
        writer.writeheader()
        writer.writerows(adobe_rows)

    # Write Shutterstock CSV
    with open(image_dir / SHUTTERSTOCK_CSV_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Filename",
                "Description",
                "Keywords",
                "Categories",
                "Editorial",
                "Mature content",
                "illustration",
            ],
        )
        writer.writeheader()
        writer.writerows(shutterstock_rows)

    print("✓ CSV files generated successfully")


if __name__ == "__main__":
    main()
