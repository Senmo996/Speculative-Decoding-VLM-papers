import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
import os

# Search and filtering configuration.
MUST_INCLUDE = "speculative decoding"
ANY_INCLUDE = ["multimodal", "vision-language", "vlm"]
DOMAIN_PATTERNS = [
    r"\bmultimodal\b",
    r"\bvision[-\s]+language\b",
    r"\bl?vlms?\b",
]
EXCLUDE_PATTERNS = [
    r"\bvla\b",
    r"\bvision[-\s]+language[-\s]+action\b",
]

START_MARKER = "<!-- PAPERS_START -->"
END_MARKER = "<!-- PAPERS_END -->"
README_FILE = "README.md"

def check_logic_strictly(title, summary=""):
    """Return True when a paper matches the repository topic."""
    full_text = title.lower()

    if any(re.search(pattern, full_text) for pattern in EXCLUDE_PATTERNS):
        return False

    if MUST_INCLUDE not in full_text:
        return False

    return any(re.search(pattern, full_text) for pattern in DOMAIN_PATTERNS)


def fetch_arxiv_papers():
    """Fetch the latest arXiv papers that match the configured topic."""
    base_url = 'http://export.arxiv.org/api/query?'

    term_core = f'all:"{MUST_INCLUDE}"'
    domain_query = " OR ".join([f'all:"{term}"' if " " in term else f'all:{term}' for term in ANY_INCLUDE])
    final_query = f'{term_core} AND ({domain_query})'

    params = {
        'search_query': final_query,
        'start': 0,
        'max_results': 50,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }

    url = base_url + urllib.parse.urlencode(params)

    try:
        response = urllib.request.urlopen(url, timeout=30)
        root = ET.fromstring(response.read())
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}

        papers = []
        for entry in root.findall('atom:entry', namespace):
            raw_title = entry.find('atom:title', namespace).text.replace('\n', ' ').strip()
            summary = entry.find('atom:summary', namespace).text.replace('\n', ' ').strip().lower()
            paper_id = entry.find('atom:id', namespace).text
            published = entry.find('atom:published', namespace).text[:10]
            link = paper_id

            if not check_logic_strictly(raw_title):
                continue

            papers.append({
                'date': published,
                'title': raw_title.replace('|', '-'),
                'link': link,
                'id': paper_id
            })
        return papers
    except Exception as e:
        print(f"Error fetching arXiv: {e}")
        return []


def arxiv_base_id(arxiv_id):
    """Return an arXiv ID without the version suffix."""
    return arxiv_id.split('/')[-1].split('v')[0]


def build_papers_block(existing_content, new_rows):
    """Insert new paper rows after the Markdown table separator."""
    lines = existing_content.strip('\n').splitlines()
    has_header = any("| Date | Title |" in line for line in lines)
    separator_index = next((i for i, line in enumerate(lines) if "|:---" in line), None)

    if not has_header or separator_index is None:
        lines = ["| Date | Title |", "|:---:|:---|"]
        separator_index = 1

    updated_lines = lines[:separator_index + 1] + new_rows + lines[separator_index + 1:]
    return "\n" + "\n".join(updated_lines) + "\n"


def update_readme():
    """Update README.md with newly discovered papers."""
    if not os.path.exists(README_FILE):
        print("README.md not found!")
        return

    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = re.compile(f'{re.escape(START_MARKER)}(.*?){re.escape(END_MARKER)}', re.DOTALL)
    match = pattern.search(content)
    if not match:
        print(f"README markers not found: {START_MARKER} and {END_MARKER}")
        return

    existing_content = match.group(1)
    existing_ids = set()
    links = re.findall(r'\(https?://arxiv.org/abs/([\d.]+)[v\d]*\)', existing_content)
    existing_ids.update(links)

    new_papers = fetch_arxiv_papers()
    unique_new_papers = [p for p in new_papers if arxiv_base_id(p['id']) not in existing_ids]

    if not unique_new_papers:
        print("No new papers found.")
        return

    print(f"Found {len(unique_new_papers)} new papers!")

    new_rows = []
    for p in unique_new_papers:
        row = f"| {p['date']} | [{p['title']}]({p['link']}) |"
        new_rows.append(row)

    updated_block = build_papers_block(existing_content, new_rows)
    updated_content = content[:match.start(1)] + updated_block + content[match.end(1):]

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(updated_content)

if __name__ == "__main__":
    update_readme()
