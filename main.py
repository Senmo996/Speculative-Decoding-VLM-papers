import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import datetime
import re
import os

# ================= 配置 =================
# 关键词逻辑
MUST_INCLUDE = "speculative decoding"
ANY_INCLUDE = ["multimodal", "vision-language", "vlm"]
MUST_EXCLUDE = "vision-language-action"

# 标记：README中内容的起始和结束位置
START_MARKER = ""
END_MARKER = ""
README_FILE = "README.md"
# =======================================
def check_logic_strictly(title):
    """本地严格逻辑过滤"""
    full_text = (title).lower() 
    
    if MUST_EXCLUDE in full_text:
        return False
    
    if MUST_INCLUDE not in full_text:
        return False
        
    has_domain = any(term in full_text for term in ANY_INCLUDE)
    if not has_domain:
        return False
        
    return True

def fetch_arxiv_papers():
    """获取符合逻辑的最新论文"""
    base_url = 'http://export.arxiv.org/api/query?'
    
    # 构造查询：all:"speculative decoding" AND (all:multimodal OR ...)
    term_core = f'all:"{MUST_INCLUDE}"'
    domain_query = " OR ".join([f'all:"{term}"' if " " in term else f'all:{term}' for term in ANY_INCLUDE])
    final_query = f'{term_core} AND ({domain_query})'
    
    params = {
        'search_query': final_query,
        'start': 0,
        'max_results': 50,  # 抓取更多以防遗漏
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
            # 获取原始信息
            raw_title = entry.find('atom:title', namespace).text.replace('\n', ' ').strip()
            summary = entry.find('atom:summary', namespace).text.replace('\n', ' ').strip().lower()
            paper_id = entry.find('atom:id', namespace).text
            published = entry.find('atom:published', namespace).text[:10] # 取 YYYY-MM-DD
            link = paper_id
            
            # 本地严格过滤：排除 VLA
            if not check_logic_strictly(raw_title):
                continue
                
            papers.append({
                'date': published,
                'title': raw_title.replace('|', '-'), # 防止破坏Markdown表格
                'link': link,
                'id': paper_id
            })
        return papers
    except Exception as e:
        print(f"Error fetching arXiv: {e}")
        return []

def update_readme():
    """更新 README.md 文件"""
    if not os.path.exists(README_FILE):
        print("README.md not found!")
        return

    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 提取旧内容（防止重复）
    # 使用正则找到 START 和 END 之间的内容
    pattern = re.compile(f'{re.escape(START_MARKER)}(.*?){re.escape(END_MARKER)}', re.DOTALL)
    match = pattern.search(content)
    
    existing_ids = set()
    if match:
        existing_content = match.group(1)
        # 从现有的 markdown 链接中提取 ID
        # 假设格式是 [Title](http://arxiv.org/abs/xxxx.xxxx)
        links = re.findall(r'\(http://arxiv.org/abs/([\d.]+)[v\d]*\)', existing_content)
        existing_ids.update(links)

    # 2. 获取新论文
    new_papers = fetch_arxiv_papers()
    unique_new_papers = [p for p in new_papers if p['id'].split('/')[-1].split('v')[0] not in existing_ids]

    if not unique_new_papers:
        print("No new papers found.")
        return

    print(f"Found {len(unique_new_papers)} new papers!")

    # 3. 生成新的表格行
    new_rows = []
    for p in unique_new_papers:
        # 格式: | YYYY-MM-DD | [Title](Link) |
        row = f"| {p['date']} | [{p['title']}]({p['link']}) |"
        new_rows.append(row)

    # 4. 组合内容：新行 + 旧内容 (去掉旧的表头，如果存在)
    # 简单的策略：我们重新生成整个表格块
    
    # 重新解析所有论文（为了统一排序）
    # 这里我们简化逻辑：把新论文插入到 START_MARKER 后面，保留旧的
    # 但为了保证顺序完美，我们最好是将新行加在旧行上面
    
    insert_content = "\n".join(new_rows) + "\n"
    
    # 如果原本中间没有内容（第一次运行），需要加表头
    if "| Date | Title |" not in match.group(1):
        header = "| Date | Title |\n|:---:|:---|\n"
        insert_content = header + insert_content
    
    # 替换内容
    # 注意：这里是将新行插入到旧行之前（在表格的第一行数据位置）
    # 但由于正则替换比较复杂，我们采用更简单的方法：
    # 将旧内容按行读取，找到表头后的第一行，插入新内容
    
    lines = content.split('\n')
    new_lines = []
    inside_block = False
    header_found = False
    
    for line in lines:
        if line.strip() == START_MARKER:
            new_lines.append(line)
            inside_block = True
            # 如果是空文件或第一次，加入表头
            if "| Date | Title |" not in content:
                new_lines.append("| Date | Title |")
                new_lines.append("|:---:|:---|")
                new_lines.extend(new_rows)
            continue
        
        if line.strip() == END_MARKER:
            inside_block = False
            new_lines.append(line)
            continue

        if inside_block:
            if "|:---" in line: # 表格分割线
                new_lines.append(line)
                new_lines.extend(new_rows) # 在分割线后立即插入新行
                header_found = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(new_lines))

if __name__ == "__main__":
    update_readme()