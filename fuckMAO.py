from pathlib import Path
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


QUESTION_HEADER_RE = re.compile(r"^\d+\.(?:单选题|多选题|判断题)\s*\(\d+分\)$", re.M)
QUESTION_BLOCK_RE = re.compile(
    r"(?ms)^(\d+)\.(单选题|多选题|判断题)\s*\((\d+)分\)\n(.*?)(?=^\d+\.(?:单选题|多选题|判断题)\s*\(\d+分\)|\Z)"
)


def connect_driver():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    return webdriver.Chrome(options=options)


def wait_for_answer_page(driver, timeout=20):
    wait = WebDriverWait(driver, timeout)
    wait.until(lambda d: "正确答案" in d.find_element(By.TAG_NAME, "body").text)


def scroll_until_stable(driver, pause=0.8, stable_rounds=3, max_rounds=20):
    last_height = -1
    stable_count = 0

    for _ in range(max_rounds):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        current_height = driver.execute_script("return document.body.scrollHeight")

        if current_height == last_height:
            stable_count += 1
            if stable_count >= stable_rounds:
                break
        else:
            stable_count = 0
            last_height = current_height

    driver.execute_script("window.scrollTo(0, 0);")


def extract_question_blocks(page_text):
    header_match = QUESTION_HEADER_RE.search(page_text)
    if not header_match:
        raise RuntimeError("当前页面未识别到题目内容，请先打开题目和答案页面。")

    content = page_text[header_match.start():].strip()
    results = []

    for match in QUESTION_BLOCK_RE.finditer(content):
        number = int(match.group(1))
        question_type = match.group(2)
        score = int(match.group(3))
        block = f"{number}.{question_type} ({score}分)\n{match.group(4).strip()}"
        answer_match = re.search(r"(?m)^正确答案[:：]\s*(.+)$", block)
        answer = answer_match.group(1).strip() if answer_match else ""
        results.append({
            "number": number,
            "type": question_type,
            "score": score,
            "answer": answer,
            "block": block,
        })

    if not results:
        raise RuntimeError("页面已打开，但未成功解析出题目块。")

    return results


def save_questions(results, output_path):
    file_exists = output_path.exists()
    has_existing_content = file_exists and output_path.stat().st_size > 0
    mode = "a" if file_exists else "w"

    with output_path.open(mode, encoding="utf-8") as file:
        if has_existing_content:
            file.write("\n")
        for item in results:
            file.write(f"【第 {item['number']} 题】\n")
            file.write(item["block"])
            file.write("\n")
            file.write("-" * 30)
            file.write("\n\n")

    return "append" if file_exists else "create"


def scrape_current_page():
    driver = connect_driver()
    print("✅ 成功连接浏览器，正在提取当前答案页内容...")
    print(f"当前页面: {driver.current_url}")

    wait_for_answer_page(driver)
    scroll_until_stable(driver)

    page_text = driver.find_element(By.TAG_NAME, "body").text
    questions = extract_question_blocks(page_text)

    output_path = Path(__file__).with_name("题库.txt")
    save_mode = save_questions(questions, output_path)

    action_text = "追加到" if save_mode == "append" else "保存到"
    print(f"✅ 已将 {len(questions)} 道题{action_text}: {output_path}")


if __name__ == "__main__":
    scrape_current_page()