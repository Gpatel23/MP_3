import json
import re
import requests
import gzip
import os
from urlextract import URLExtract

user_id = 'bfitzpa8'
base_links = {
    'model': 'https://huggingface.co/',
    'data': 'https://huggingface.co/datasets/',
    'source': 'https://github.com/'
}
default_suffix = '/raw/main/README.md'
github_suffix = 'blob/main/README.md'
output_folder = 'output'
compressed_file = f"{output_folder}/{user_id}.json.gz"

# Ensure output directory exists
os.makedirs(output_folder, exist_ok=True)

# Initialize URL extractor and DOI regex pattern
url_finder = URLExtract()
doi_pattern = r'\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b'

def get_urls(text):
    return url_finder.find_urls(text)

def get_dois(text):
    return re.findall(doi_pattern, text, re.IGNORECASE)

def get_bib_entries(text):
    return re.findall(r'@(?:article|book|inproceedings){[^}]*}', text, re.DOTALL)

def fetch_and_process_readme(type_key, identifier, suffix):
    full_url = f"{base_links[type_key]}{identifier}{suffix}"
    response = requests.get(full_url)

    # Handle unsuccessful request or GitHub redirects
    if response.status_code != 200:
        if 'github.com' in full_url and 'blob/master/' in full_url:
            full_url = full_url.replace('blob/master/', 'blob/main/')
            response = requests.get(full_url)
            if response.status_code != 200:
                return None
        else:
            return None

    content = response.text
    urls = get_urls(content)
    dois = get_dois(content)
    bib_entries = get_bib_entries(content)

    processed_entry = {
        'id': identifier,
        'type': type_key,
        'url': full_url,
        'content': content.replace("\n", " "),
        'links': urls,
        'dois': dois,
        'bibs': bib_entries
    }
    return processed_entry

def process_type(type_key):
    suffix = default_suffix
    input_file_path = f"input/{user_id}_{type_key}"
    collected_data = []

    with open(input_file_path, 'r', encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if type_key == 'source':
                _, line = line.split(';', 1)
                suffix = github_suffix

            data_entry = fetch_and_process_readme(type_key, line, suffix)
            if data_entry:
                collected_data.append(json.dumps(data_entry, ensure_ascii=False))

    return collected_data

# Write data to compressed output file
with gzip.open(compressed_file, 'wt', encoding="utf-8") as compressed_output:
    for type_key in ['model', 'data', 'source']:
        extracted_entries = process_type(type_key)
        compressed_output.write("\n".join(extracted_entries) + "\n")

print("Done", compressed_file)                                              