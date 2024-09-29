import os
import re
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv
from openai import OpenAI
import openai
import json

import openai
import frontmatter
from pathlib import Path

# 加载环境变量
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

# 初始化Notion客户端
notion = Client(auth=os.getenv("NOTION_TOKEN"))
database_id = os.getenv("NOTION_DATABASE_ID")
open_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 初始化OpenAI客户端

def read_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        post = frontmatter.load(file)
        content = post.content
        metadata = post.metadata
    return content, metadata

def extract_title(content, metadata):
    if 'title' in metadata:
        return metadata['title']
    match = re.search(r'^# (.+)$', content, re.MULTILINE)
    return match.group(1) if match else "Untitled"

def extract_tags(metadata):
    return metadata.get('tags', [])

def generate_summary_tags(content):
    json_format = "{'Summary': '摘要', 'Tags': ['tag1', 'tag2', 'tag3']}"
    prompt = f"请为以下内容生成一个简短的摘要Summary，并给出5~8个多样化而具体的TAG，严格用json格式{json_format}返回:\n\n{content[:1000]}..."
    result = None
    try:
        response = open_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
            response_format={ "type": "json_object" }
        )
        print("response=",response)
        result = response.choices[0].message.content.strip()
        print("result=",result)
    except Exception as e:
        print(f"生成摘要时出错: {e}")
        return "SUMMARY_ERROR","TAG_ERROR"
    # result是字符串，转化为词典
    try:
        result_dict = json.loads(result)
        summary = result_dict['Summary']
        tags = result_dict['Tags']
    except Exception as e:
        print(f"生成摘要时出错: {e}")
        return "SUMMARY_ERROR","TAG_ERROR"
    return summary, tags

def create_notion_page(title, content, summary, tags, created_at, last_modified):
    properties = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Content": {"rich_text": [{"text": {"content": content[:2000]}}]},
        "Summary": {"rich_text": [{"text": {"content": summary}}]},
        "Tags": {"multi_select": [{"name": tag} for tag in tags]},
        "Created At": {"date": {"start": created_at.isoformat()}},
        "Last Modified": {"date": {"start": last_modified.isoformat()}},
        "Status": {"select": {"name": "未读"}}
    }

    page = notion.pages.create(
        parent={"database_id": database_id},
        properties=properties
    )
    return page


def update_notion_page(page_id, title, content, summary, tags, last_modified):
    properties = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Content": {"rich_text": [{"text": {"content": content[:2000]}}]},
        "Summary": {"rich_text": [{"text": {"content": summary}}]},
        "Tags": {"multi_select": [{"name": tag} for tag in tags]},
        "Last Modified": {"date": {"start": last_modified.isoformat()}}
    }

    notion.pages.update(
        page_id=page_id,
        properties=properties
    )
def sync_markdown_to_notion(markdown_folder, debug=False):
    print("开始同步Markdown文件到Notion")
    for file_path in Path(markdown_folder).glob('*.md'):
        if debug:
            print(f"Processing file: {file_path}")
        content, metadata = read_markdown_file(file_path)
        if debug:
            print(f"Content read: {content[:100]}...")  # 仅显示前100个字符
            print(f"Metadata: {metadata}")

        title = extract_title(content, metadata)
        if debug:
            print(f"Extracted title: {title}")

        summary,tags = generate_summary_tags(content)
        if debug:
            print(f"Generated summary: {summary}")
            print(f"Generated tags: {tags}")
        created_at = datetime.fromtimestamp(file_path.stat().st_ctime)
        last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
        if debug:
            print(f"File created at: {created_at}, last modified at: {last_modified}")

        # 检查是否已存在同名页面
        existing_pages = notion.databases.query(
            database_id=database_id,
            filter={"property": "Title", "title": {"equals": title}}
        ).get("results")

        if existing_pages:
            page_id = existing_pages[0]["id"]
            if debug:
                print(f"Existing page found with ID: {page_id}")
            update_notion_page(page_id, title, content, summary, tags, last_modified)
            if debug:
                print(f"Updated: {title}")
        else:
            if debug:
                print(f"No existing page found for title: {title}")
            create_notion_page(title, content, summary, tags, created_at, last_modified)
            if debug:
                print(f"Created: {title}")

if __name__ == "__main__":
    markdown_folder = "/Users/bytedance/Code/weread_to_notion/mdfiles"
    print("开始同步Markdown文件到Notion")
    sync_markdown_to_notion(markdown_folder,debug=True)
    print("同步完成")