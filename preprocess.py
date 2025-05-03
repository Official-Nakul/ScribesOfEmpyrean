import re
import json
from unicodedata import normalize
from typing import Dict, List, Any
from bs4 import BeautifulSoup


def clean_text(text: str) -> str:
    """
    Comprehensive text cleaning function that handles:
    - Spoiler warnings
    - [Biography] and similar tags
    - Special characters
    - Whitespace normalization
    - HTML remnants
    """
    if not text or not isinstance(text, str):
        return ""

    # Remove spoiler warnings (multiple variations)
    spoiler_patterns = [
        r"This is a high-traffic page containing major spoilers for.*?proceed with caution!",
        r"Warning: This page contains spoilers for.*?",
        r"SPOILER ALERT:.*?"
    ]
    for pattern in spoiler_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Remove [Biography] and similar wiki markup tags
    text = re.sub(r'\[[^\]]+\]', '', text)

    # Remove HTML tags if any remain
    text = BeautifulSoup(text, "html.parser").get_text()

    # Normalize unicode characters
    text = normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    # Remove special characters except basic punctuation
    text = re.sub(r'[^\w\s.,!?\'\";:()-]', '', text)

    # Normalize whitespace and line breaks
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def process_infobox(infobox: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes and normalizes infobox data:
    - Cleans keys and values
    - Handles nested structures
    - Converts all values to consistent formats
    """
    normalized = {}

    for section, content in infobox.items():
        if not content:
            continue

        # Clean section name
        section_clean = re.sub(r'[^\w\s]', '', str(section)).lower().replace(' ', '_')

        if isinstance(content, dict):
            # Process nested infobox items
            normalized_section = {}
            for key, value in content.items():
                key_clean = re.sub(r'[^\w\s]', '', str(key)).lower().replace(' ', '_')

                if isinstance(value, list):
                    normalized_section[key_clean] = [clean_text(str(item)) for item in value]
                else:
                    normalized_section[key_clean] = clean_text(str(value))

            if normalized_section:
                normalized[section_clean] = normalized_section

        elif isinstance(content, (str, int, float)):
            normalized[section_clean] = clean_text(str(content))

    return normalized


def split_into_paragraphs(text: str) -> List[str]:
    """
    Splits text into logical paragraphs based on punctuation.
    """
    if not text:
        return []

    # Split on sentence-ending punctuation followed by whitespace
    paragraphs = re.split(r'(?<=[.!?])\s+', text)

    # Filter out empty paragraphs and clean each one
    return [clean_text(p) for p in paragraphs if p.strip()]


def process_content_sections(content_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes all content sections (main content and subsections):
    - Cleans text
    - Splits into paragraphs
    - Preserves section hierarchy
    """
    processed = {}

    for section_name, section_content in content_data.items():
        if not section_content:
            continue

        cleaned_name = clean_text(section_name)
        cleaned_content = clean_text(section_content)

        if cleaned_content:
            processed[cleaned_name] = {
                "full_text": cleaned_content,
                "paragraphs": split_into_paragraphs(cleaned_content)
            }

    return processed


def preprocess_character(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complete preprocessing pipeline for a single character entry.
    Now with separated image and reference URLs.
    """
    # Basic cleaning of top-level fields
    processed = {
        "name": clean_text(raw_data.get("name", "")),
        "ref_url": raw_data.get("url", ""),  # Renamed from 'url' to 'ref_url'
        "source": "empyrean_wiki"
    }

    # Process infobox if present
    if "infobox" in raw_data:
        processed["infobox"] = process_infobox(raw_data["infobox"])

    # Process images - now stored in img_urls array
    if "images" in raw_data:
        processed["img_urls"] = [  # Renamed from 'images' to 'img_urls'
            {
                "url": img.get("src", ""),
                "alt_text": clean_text(img.get("alt", ""))
            }
            for img in raw_data.get("images", [])
            if img.get("src")
        ]

    # Process all content sections
    content_sections = {}

    # Process main content if exists
    if "content" in raw_data:
        content_sections["main"] = clean_text(raw_data["content"])

    # Add subsection content
    if "sections" in raw_data:
        for section_name, section_content in raw_data["sections"].items():
            content_sections[section_name] = clean_text(section_content)

    # Apply processing to all content
    if content_sections:
        processed["content"] = process_content_sections(content_sections)

    return processed


def save_processed_data(data: Dict[str, Any], filename: str) -> None:
    """
    Saves processed data to JSON file with proper formatting.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main(input_file: str, output_file: str) -> None:
    """
    Main preprocessing workflow.
    """
    print(f"Loading raw data from {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"Processing {len(raw_data)} characters...")
    processed_data = {}

    for char_name, char_data in raw_data.items():
        try:
            processed_data[char_name] = preprocess_character(char_data)
            print(f"Processed: {char_name}")
        except Exception as e:
            print(f"Error processing {char_name}: {str(e)}")
            processed_data[char_name] = {
                "name": char_name,
                "error": str(e),
                "raw_data": char_data
            }

    print(f"Saving processed data to {output_file}...")
    save_processed_data(processed_data, output_file)
    print("Preprocessing complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="empyrean_characters.json", help="Input JSON file")
    parser.add_argument("--output", default="empyrean_characters_processed.json", help="Output JSON file")
    args = parser.parse_args()

    main(args.input, args.output)