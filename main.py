import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re
import os

# Search and filtering configuration.
MUST_INCLUDE = "speculative decoding"
ANY_INCLUDE = ["multimodal", "vision-language", "vlm", "video"]
MULTIMODAL_PATTERNS = [
    r"\bmultimodal\b",
    r"\bvision[-\s]+language\b",
    r"\bl?vlms?\b",
]
VIDEO_PATTERNS = [
    r"\bvideo[-\s]+llms?\b",
    r"\bvideo[-\s]+large[-\s]+language[-\s]+models?\b",
    r"\bvid[-\s]*llms?\b",
]
DOMAIN_PATTERNS = MULTIMODAL_PATTERNS + VIDEO_PATTERNS
EXCLUDE_PATTERNS = [
    r"\bvla\b",
    r"\bvision[-\s]+language[-\s]+action\b",
]

START_MARKER = "<!-- PAPERS_START -->"
END_MARKER = "<!-- PAPERS_END -->"
VIDEO_START_MARKER = "<!-- VIDEO_PAPERS_START -->"
VIDEO_END_MARKER = "<!-- VIDEO_PAPERS_END -->"
README_FILE = "README.md"

def check_logic_strictly(title, summary=""):
    """Return True when a paper matches the repository topic."""
    full_text = title.lower()

    if any(re.search(pattern, full_text) for pattern in EXCLUDE_PATTERNS):
        return False

    if MUST_INCLUDE not in full_text:
        return False

    return any(re.search(pattern, full_text) for pattern in DOMAIN_PATTERNS)


def is_video_paper(title):
    """Return True when the title identifies a video-focused paper."""
    title_text = title.lower()
    return any(re.search(pattern, title_text) for pattern in VIDEO_PATTERNS)


def build_search_query():
    """Build the broad arXiv query; local regexes perform strict filtering."""
    domain_query = " OR ".join(f'all:"{term}"' for term in ANY_INCLUDE)
    return f'all:"{MUST_INCLUDE}" AND ({domain_query})'


def fetch_arxiv_papers():
    """Fetch the latest arXiv papers that match the configured topic."""
    base_url = 'http://export.arxiv.org/api/query?'

    params = {
        'search_query': build_search_query(),
        'start': 0,
        'max_results': 200,
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
            summary = entry.find('atom:summary', namespace).text.replace('\n', ' ').strip()
            paper_id = entry.find('atom:id', namespace).text
            published = entry.find('atom:published', namespace).text[:10]
            link = paper_id

            if not check_logic_strictly(raw_title, summary):
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

    marker_pairs = {
        'multimodal': (START_MARKER, END_MARKER),
        'video': (VIDEO_START_MARKER, VIDEO_END_MARKER),
    }
    table_matches = {}
    for category, (start_marker, end_marker) in marker_pairs.items():
        pattern = re.compile(
            f'{re.escape(start_marker)}(.*?){re.escape(end_marker)}',
            re.DOTALL,
        )
        match = pattern.search(content)
        if not match:
            print(f"README markers not found: {start_marker} and {end_marker}")
            return
        table_matches[category] = match

    existing_ids = set()
    for match in table_matches.values():
        links = re.findall(
            r'\(https?://arxiv.org/abs/([\d.]+)[v\d]*\)',
            match.group(1),
        )
        existing_ids.update(links)

    new_papers = fetch_arxiv_papers()
    unique_new_papers = [p for p in new_papers if arxiv_base_id(p['id']) not in existing_ids]

    if not unique_new_papers:
        print("No new papers found.")
        return

    papers_by_category = {'multimodal': [], 'video': []}
    for p in unique_new_papers:
        category = 'video' if is_video_paper(p['title']) else 'multimodal'
        papers_by_category[category].append(p)

    print(
        f"Found {len(papers_by_category['multimodal'])} new multimodal papers "
        f"and {len(papers_by_category['video'])} new video papers!"
    )

    updated_content = content
    for category, papers in papers_by_category.items():
        if not papers:
            continue

        start_marker, end_marker = marker_pairs[category]
        pattern = re.compile(
            f'{re.escape(start_marker)}(.*?){re.escape(end_marker)}',
            re.DOTALL,
        )
        match = pattern.search(updated_content)
        new_rows = [
            f"| {p['date']} | [{p['title']}]({p['link']}) |"
            for p in papers
        ]
        updated_block = build_papers_block(match.group(1), new_rows)
        updated_content = (
            updated_content[:match.start(1)]
            + updated_block
            + updated_content[match.end(1):]
        )

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(updated_content)

if __name__ == "__main__":
    update_readme()
