# 将网页内容转换为Markdown格式/Text格式并保存到文件

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import html2text
import getpass
import time
import sys
import argparse

def setup_driver():
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    # 设置并返回WebDriver
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def check_login_required(driver, url):
    driver.get(url)
    # 检查是否存在登录表单
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        return True
    except:
        return False

def get_content(driver, url, username=None, password=None):
    if check_login_required(driver, url):
        if username and password:
            return login_and_get_content(driver, url, username, password)
        else:
            print("该页面需要登录，但未提供登录信息。")
            return None
    else:
        driver.get(url)
        time.sleep(3)  # 等待页面加载
        return driver.page_source

def login_and_get_content(driver, url, username, password):
    driver.get(url)
    
    # 等待登录表单加载
    try:
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = driver.find_element(By.NAME, "password")
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        submit_button.click()
        
        # 等待页面加载完成
        time.sleep(5)  # 可以根据需要调整等待时间
        
        print("登录成功!")
        return driver.page_source
    except Exception as e:
        print(f"登录失败: {str(e)}")
        return None

# 将html转换为纯文本，方便后面让OpenAI进行总结
def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for img in soup.find_all('img'):
        alt_text = img.get('alt', '图片')
        img.replace_with(f"[图片: {alt_text}]")
    return soup.get_text(strip=False)

def html_to_markdown(html_content):
    # 使用BeautifulSoup清理HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 处理图片和表格
    for img in soup.find_all('img'):
        alt_text = img.get('alt', '图片')
        src = img.get('src', '')
        if src:
            img.replace_with(f"![{alt_text}]({src})")
        else:
            img.replace_with(f"[图片: {alt_text}]")
    
    for table in soup.find_all('table'):
        table_markdown = '\n\n|'
        for row in table.find_all('tr'):
            cells = row.find_all(['th', 'td'])
            row_string = ' | '.join(cell.get_text(strip=True) for cell in cells)
            table_markdown += f"{row_string} |\n"
        table_markdown += '\n'
        table.replace_with(table_markdown)
    
    # 使用html2text将HTML转换为Markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    markdown_content = h.handle(str(soup))
    
    return markdown_content

def save_to_file(content, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

# 主函数，通过参数输入Url和保存的文件的前缀
def main(url, prefix):    
    driver = setup_driver()
    try:
        if check_login_required(driver, url):
            username = input("请输入用户名: ")
            password = getpass.getpass("请输入密码: ")
        else:
            username = password = None
        
        html_content = get_content(driver, url, username, password)
        if html_content:
            markdown_content = html_to_markdown(html_content)
            save_to_file(markdown_content, f"{prefix}.md")
            save_to_file(html_to_text(html_content), f"{prefix}.txt")   
            #输出到错误流 
            print(f"内容已保存到{prefix}.md和{prefix}.txt", file=sys.stderr)
    finally:
        driver.quit()

#arg parser
#当没有设置prefix的时候，直接输出text到控制台
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将网页内容转换为Markdown格式并保存到文件")
    parser.add_argument("url", type=str, help="要转换的网页URL")
    parser.add_argument("prefix", type=str, nargs='?', default=None, help="保存的文件名前缀（可选）")
    args = parser.parse_args()
    
    if args.prefix:
        main(args.url, args.prefix)
    else:
        driver = setup_driver()
        try:
            if check_login_required(driver, args.url):
                username = input("请输入用户名: ")
                password = getpass.getpass("请输入密码: ")
            else:
                username = password = None
            
            html_content = get_content(driver, args.url, username, password)
            if html_content:
                print(html_to_text(html_content))
        finally:
            driver.quit()