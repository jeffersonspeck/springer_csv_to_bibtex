import csv
import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

def extract_additional_info(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        data = {
            'title': None,
            'abstract': None,
            'pages': None,
            'month': None,
            'doi': None,
            'volume': None,
            'issue': None,
            'issn': None,
            'journal': None
        }
        meta_map = {
            'dc.title': 'title',
            'dc.description': 'abstract',
            'prism.startingPage': 'pages',
            'prism.publicationDate': 'month',
            'prism.doi': 'doi',
            'prism.volume': 'volume',
            'prism.number': 'issue',
            'prism.issn': 'issn',
            'prism.publicationName': 'journal'
        }
        for meta_name, field in meta_map.items():
            meta = soup.find('meta', {'name': meta_name})
            if meta and meta.get('content'):
                data[field] = meta['content']
        starting_page = soup.find('meta', {'name': 'prism.startingPage'})
        ending_page = soup.find('meta', {'name': 'prism.endingPage'})
        if starting_page and ending_page:
            data['pages'] = f"{starting_page['content']}-{ending_page['content']}"
        if data['month'] and '-' in data['month']:
            data['month'] = data['month'].split('-')[1]
        return data
    except Exception:
        return {}

def csv_to_bibtex():
    keys = {}
    current_directory = os.getcwd()
    csv_files = [file for file in os.listdir(current_directory) if file.endswith('.csv')]
    unique_entries = set()
    duplicate_count = 0

    print("\nProcessing the following CSV files:")
    for csv_file in csv_files:
        print(f" - {csv_file}")
        with open(os.path.join(current_directory, csv_file), 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                identifier = row.get('Item DOI', '').strip() or f"{row.get('Item Title', '').strip()}_{row.get('Authors', '').strip()}"
                if identifier in unique_entries:
                    duplicate_count += 1
                else:
                    unique_entries.add(identifier)

    total_items = len(unique_entries)
    print(f"\nTotal unique entries: {total_items}")
    print(f"Total duplicates found: {duplicate_count}")

    output_name = input("\nEnter the output file name (without extension, press Enter for default): ").strip()
    if not output_name:
        output_name = "SearchResults"
    bibtex_file = f"{output_name}.bib"

    with open(bibtex_file, 'w', encoding='utf-8') as bibfile:
        for csv_file in csv_files:
            with open(os.path.join(current_directory, csv_file), 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                with tqdm(total=total_items, desc="Processing unique entries", unit="entry") as pbar:
                    for row in rows:
                        identifier = row.get('Item DOI', '').strip() or f"{row.get('Item Title', '').strip()}_{row.get('Authors', '').strip()}"
                        if identifier not in unique_entries:
                            continue
                        unique_entries.remove(identifier)

                        if row.get('Authors') and row.get('Publication Year'):
                            first_author_full = row['Authors'].split(',')[0].strip()
                            first_author_surname = first_author_full.split()[-1]
                            base_key = f"{first_author_surname}_{row['Publication Year']}"
                        else:
                            continue

                        key = base_key
                        counter = 97
                        while key in keys:
                            key = f"{base_key}{chr(counter)}"
                            counter += 1
                        keys[key] = True

                        additional_info = extract_additional_info(row.get('URL', '')) if row.get('URL') else {}
                        if additional_info.get('title'):
                            print(f"\nConsulting: {additional_info['title']}")

                        bibfile.write(f"@article{{{key},\n")
                        if additional_info.get('title'):
                            bibfile.write(f"  title={{ {additional_info['title']} }},\n")
                        if row.get('Journal Volume') or additional_info.get('volume'):
                            bibfile.write(f"  volume={{ {additional_info.get('volume', row.get('Journal Volume'))} }},\n")
                        if additional_info.get('doi'):
                            bibfile.write(f"  DOI={{ {additional_info['doi']} }},\n")
                        if additional_info.get('journal'):
                            bibfile.write(f"  journal={{ {additional_info['journal']} }},\n")
                        if row.get('Authors'):
                            bibfile.write(f"  author={{ {row['Authors']} }},\n")
                        if row.get('Publication Year'):
                            bibfile.write(f"  year={{ {row['Publication Year']} }},\n")
                        if additional_info.get('pages'):
                            bibfile.write(f"  pages={{ {additional_info['pages']} }},\n")
                        if additional_info.get('month'):
                            bibfile.write(f"  month={{ {additional_info['month']} }},\n")
                        if additional_info.get('abstract'):
                            bibfile.write(f"  abstract={{ {additional_info['abstract']} }},\n")
                        if additional_info.get('issn'):
                            bibfile.write(f"  issn={{ {additional_info['issn']} }},\n")
                        bibfile.write("}\n\n")
                        pbar.update(1)

    print(f"\nBibTeX file generated: {bibtex_file}")

csv_to_bibtex()
