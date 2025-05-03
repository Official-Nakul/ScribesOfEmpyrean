from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import json
import os
import re

BRAVE_PATH = "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"
BASE_URL = "https://the-empyrean-series.fandom.com"
OUTPUT_FILE = "../empyrean/empyrean_characters.json"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=BRAVE_PATH, headless=False)
    page = browser.new_page()

    # Create a dictionary to store all character data
    all_characters = {}

    try:
        # Load the category page
        page.goto(f"{BASE_URL}/wiki/Category:Characters", wait_until="domcontentloaded")

        # First collect all character links
        character_links = []
        ul_elements = page.query_selector_all(".mw-category-group ul, .mw-content-ltr ul")

        for ul in ul_elements:
            links = ul.query_selector_all("li > a")
            for link in links:
                try:
                    href = link.get_attribute("href")
                    text = link.inner_text()

                    # Make sure we have a full URL
                    if href and href.startswith("/"):
                        full_url = BASE_URL + href
                        character_links.append((text, full_url))
                except Exception as e:
                    print(f"Error getting link info: {e}")

        # Now process each link separately
        for character_name, character_url in character_links:
            try:
                # Visit the character page
                page.goto(character_url, wait_until="domcontentloaded")

                # Wait for content to load
                page.wait_for_selector("div.mw-parser-output", timeout=5000)

                # Extract content
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                character_data = {
                    "name": character_name,
                    "url": character_url,
                    "infobox": {},
                    "images": [],
                    "content": "",
                    "sections": {}
                }

                # Get the main content div
                content_div = soup.find("div", class_="mw-parser-output")
                if content_div:
                    # Process infobox if it exists
                    infobox = soup.find("aside", class_="portable-infobox")
                    if infobox:
                        # Extract title
                        title_element = infobox.find("h2", class_="pi-title")
                        if title_element:
                            character_data["infobox"]["title"] = title_element.get_text(strip=True)

                        # Extract images
                        image_elements = infobox.find_all("img")
                        for img in image_elements:
                            if img.get('src'):
                                character_data["images"].append({
                                    "src": img.get('src'),
                                    "alt": img.get('alt', ''),
                                    "width": img.get('width', ''),
                                    "height": img.get('height', '')
                                })

                        # Extract sections
                        sections = infobox.find_all("section", class_="pi-item pi-group")
                        for section in sections:
                            section_header = section.find("h2", class_="pi-header")
                            if section_header:
                                section_name = section_header.get_text(strip=True)
                                character_data["infobox"][section_name] = {}

                                # Get all data items in this section
                                data_items = section.find_all("div", class_="pi-item pi-data")
                                for item in data_items:
                                    label = item.find("h3", class_="pi-data-label")
                                    value = item.find("div", class_="pi-data-value")

                                    if label and value:
                                        label_text = label.get_text(strip=True)

                                        # Handle lists in values
                                        if value.find("ul"):
                                            list_items = []
                                            for li in value.find_all("li"):
                                                list_items.append(li.get_text(strip=True))
                                            character_data["infobox"][section_name][label_text] = list_items
                                        else:
                                            character_data["infobox"][section_name][label_text] = value.get_text(
                                                strip=True)

                    # Remove navigation elements and scripts
                    for element in content_div.select(".navbox, .toc, script, style, .navigation-not-searchable"):
                        element.decompose()

                    # Extract all text content
                    current_section = "main"
                    character_data["sections"][current_section] = ""

                    # Skip the infobox which we've already processed
                    if content_div.aside:
                        content_div.aside.decompose()

                    # Process all elements to extract text
                    for element in content_div.find_all(
                            ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'table', 'blockquote']):
                        # Check if it's a heading (new section)
                        if element.name and element.name.startswith('h') and element.name[1].isdigit():
                            current_section = element.get_text(strip=True)
                            character_data["sections"][current_section] = ""

                        # For tables
                        elif element.name == 'table':
                            table_text = ""
                            for row in element.find_all('tr'):
                                cells = []
                                for cell in row.find_all(['th', 'td']):
                                    cells.append(cell.get_text(strip=True))
                                if cells:
                                    table_text += " | ".join(cells) + "\n"

                            if current_section in character_data["sections"]:
                                character_data["sections"][current_section] += table_text + "\n"

                        # For lists
                        elif element.name in ['ul', 'ol']:
                            list_text = ""
                            for li in element.find_all('li'):
                                list_text += "• " + li.get_text(strip=True) + "\n"

                            if current_section in character_data["sections"]:
                                character_data["sections"][current_section] += list_text + "\n"

                        # For other elements
                        else:
                            text = element.get_text(strip=True)
                            if text and current_section in character_data["sections"]:
                                character_data["sections"][current_section] += text + "\n"

                    # Combine all section text for the full content
                    character_data["content"] = "\n".join(
                        f"{section}:\n{content}"
                        for section, content in character_data["sections"].items()
                        if content.strip()
                    )

                    # Add to our collection
                    all_characters[character_name] = character_data

                    print(f"Processed: {character_name}")
                else:
                    print(f"No content found for: {character_name}")

                # Be respectful to the server
                time.sleep(2)

            except Exception as e:
                print(f"Error with {character_name} ({character_url}): {e}")
                # Still add the character with error information
                all_characters[character_name] = {
                    "name": character_name,
                    "url": character_url,
                    "error": str(e)
                }

        # Save all data to JSON file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_characters, f, ensure_ascii=False, indent=2)

        print(f"\nData saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error loading category page: {e}")

        # Still save any data we've collected so far
        if all_characters:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_characters, f, ensure_ascii=False, indent=2)
            print(f"Partial data saved to {OUTPUT_FILE}")

    finally:
        browser.close()