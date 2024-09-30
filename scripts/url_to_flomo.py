import os
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
import requests
from url_to_file import url_to_markdown  # 假设这是 url_to_file.py 中的函数名

# 设置 OpenAI API 密钥
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"

# 设置 Flomo API 密钥
FLOMO_API_KEY = ""

def summarize_and_tag(text):
    chat = ChatOpenAI(temperature=0)
    response = chat([HumanMessage(content=f"请总结以下文本,并提供3-5个具体而不宽泛的五个字以内的标签:\n\n{text}")])
    summary, tags = response.content.split("\n\n标签:")
    tags = [tag.strip() for tag in tags.split(",")]
    return summary.strip(), tags

def send_to_flomo(content):
    url = "https://flomoapp.com/iwh/MzU2NDQ2/e563d723e19d62650e6aa8c911eb2e81/"
    data = {
        "content": content,
        "image_urls": tags
    }
    response = requests.post(url, json=data)
    return response.status_code == 200

def process_url(url):
    # 获取网页内容
    markdown_content = url_to_markdown(url)
    
    # 分段处理长文本
    max_chunk_size = 4000  # OpenAI API 的最大输入长度约为 4096 tokens
    chunks = [markdown_content[i:i+max_chunk_size] for i in range(0, len(markdown_content), max_chunk_size)]
    
    all_summaries = []
    all_tags = set()
    
    for chunk in chunks:
        summary, tags = summarize_and_tag(chunk)
        all_summaries.append(summary)
        all_tags.update(tags)
    
    final_summary = " ".join(all_summaries)

    #tags用“#”开头，空格连接
    tags = "#" + " #".join(all_tags)
    # 构建 Flomo 内容
    flomo_content = f" {tags} 连接: {url}\n\n总结: {final_summary}\n\n"
    
    # 发送到 Flomo
    success = send_to_flomo(flomo_content[:5000])
    
    if success:
        print("成功发送到 Flomo!")
    else:
        print("发送到 Flomo 失败。")

if __name__ == "__main__":
    url = input("请输入要处理的 URL: ")
    process_url(url)