import re
import requests
from notion_client import Client
import markdown
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置Notion API客户端
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
notion = Client(auth=NOTION_TOKEN)
parent_page_id = "110d4c313c3e80388002d9d7e7350d35"

def read_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def markdown_to_blocks(markdown_content):
    # 将Markdown转换为HTML
    html = markdown.markdown(markdown_content)
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html, 'html.parser')
    
    blocks = []
    for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol']):
        if element.name == 'p':
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": element.get_text()}}]
                }
            })
        elif element.name.startswith('h'):
            blocks.append({
                "object": "block",
                "type": "heading_" + element.name[-1],
                "heading_" + element.name[-1]: {
                    "rich_text": [{"type": "text", "text": {"content": element.get_text()}}]
                }
            })
        elif element.name in ['ul', 'ol']:
            list_items = []
            for li in element.find_all('li'):
                list_items.append({
                    "rich_text": [{"type": "text", "text": {"content": li.get_text()}}]
                })
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item" if element.name == 'ul' else "numbered_list_item",
                "bulleted_list_item" if element.name == 'ul' else "numbered_list_item": list_items[0]
            })
            for item in list_items[1:]:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item" if element.name == 'ul' else "numbered_list_item",
                    "bulleted_list_item" if element.name == 'ul' else "numbered_list_item": item
                })
    
    return blocks

def create_notion_page(title, blocks):
    new_page = notion.pages.create(
    parent={"database_id": parent_page_id},
    properties={
        "Name": {"title": [{"text": {"content": "新页面标题"}}]},
        "Description": {"rich_text": [{"text": {"content": "这是一个新页面的描述"}}]},
        "Status": {"select": {"name": "进行中"}}
    }
    )
    print(f"创建的新页面 ID: {new_page['id']}")

    return new_page

def import_markdown_to_notion(file_path):
    # 读取Markdown文件
    markdown_content = read_markdown_file(file_path)
    
    # 将Markdown转换为Notion块
    blocks = markdown_to_blocks(markdown_content)
    
    # 创建新的Notion页面
    title = os.path.basename(file_path).split('.')[0]
    new_page = create_notion_page(title, blocks)
    
    print(f"成功创建新页面：{new_page['url']}")

# 使用示例
if __name__ == "__main__":
    markdown_file = "/Users/bytedance/Code/weread_to_notion/mdfiles/output.md"
    notion_page_url = import_markdown_to_notion(markdown_file)
    print(f"Notion页面已创建: {notion_page_url}")