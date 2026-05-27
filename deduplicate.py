import re
import sys

INPUT_FILE = r"c:\Users\Justin Zhou\Desktop\大二下\毛概\题库.txt"
OUTPUT_FILE = r"c:\Users\Justin Zhou\Desktop\大二下\毛概\题库_去重.md"

SEPARATOR = "------------------------------"

def parse_questions(text):
    """将文本分割成题目块列表"""
    blocks = []
    current = []
    for line in text.splitlines():
        if line.strip() == SEPARATOR:
            if current:
                blocks.append("\n".join(current).strip())
                current = []
        else:
            current.append(line)
    if current:
        stripped = "\n".join(current).strip()
        if stripped:
            blocks.append(stripped)
    return blocks

def get_question_key(block):
    """提取题目正文作为去重键（跳过题号行和题型行）"""
    lines = block.splitlines()
    # 跳过 【第 X 题】 行
    content_lines = [l for l in lines if not re.match(r"^【第\s*\d+\s*题】", l.strip())]
    # 跳过 "N.单选题 (1分)" 这类题型行
    content_lines = [l for l in content_lines if not re.match(r"^\d+\.(单选题|多选题|判断题)", l.strip())]
    # 用第一行非空内容作为 key（即题目正文）
    for line in content_lines:
        if line.strip():
            return line.strip()
    return block.strip()

def format_question_md(block, index):
    """将题目块格式化为 Markdown"""
    lines = block.splitlines()
    result = []
    result.append(f"## 第 {index} 题")
    result.append("")

    skip_header = True
    for line in lines:
        # 跳过原始题号行
        if skip_header and re.match(r"^【第\s*\d+\s*题】", line.strip()):
            continue
        # 跳过题型行（重新生成）
        m = re.match(r"^\d+\.(单选题|多选题|判断题)\s*\((\d+分)\)", line.strip())
        if m:
            skip_header = False
            result.append(f"**{m.group(1)}**（{m.group(2)}）")
            result.append("")
            continue
        skip_header = False

        # 得分行
        if line.strip().startswith("本题得分："):
            continue
        # 正确答案行
        if line.strip().startswith("正确答案："):
            ans = line.strip().replace("正确答案：", "").strip()
            result.append("")
            result.append(f"> **正确答案：{ans}**")
            continue
        # 选项行
        if re.match(r"^[A-Z]$", line.strip()):
            continue  # 单独的选项字母行（选项内容在下一行）
        # 选项内容行（前面有单独字母行的情况）
        # 实际上选项字母和内容在相邻行，需要合并
        result.append(line)

    return "\n".join(result)

def format_question_md_v2(block, index):
    """
    更健壮的格式化：将选项字母行与下一行内容合并为 'A. 内容' 形式
    """
    lines = block.splitlines()
    result = []
    result.append(f"## 第 {index} 题")
    result.append("")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 跳过原始题号行
        if re.match(r"^【第\s*\d+\s*题】$", line):
            i += 1
            continue

        # 题型行
        m = re.match(r"^\d+\.(单选题|多选题|判断题)\s*\((\d+分)\)", line)
        if m:
            result.append(f"**{m.group(1)}**（{m.group(2)}）")
            result.append("")
            i += 1
            continue

        # 得分行（跳过）
        if line.startswith("本题得分："):
            i += 1
            continue

        # 正确答案行
        if line.startswith("正确答案："):
            ans = line.replace("正确答案：", "").strip()
            result.append("")
            result.append(f"> **正确答案：{ans}**")
            i += 1
            continue

        # 单独的选项字母行（A/B/C/D/E）- 与下一行合并
        if re.match(r"^[A-Z]$", line) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # 确保下一行不是另一个选项字母或特殊行
            if next_line and not re.match(r"^[A-Z]$", next_line) \
                    and not next_line.startswith("本题得分") \
                    and not next_line.startswith("正确答案"):
                result.append(f"- **{line}.** {next_line}")
                i += 2
                continue

        # 普通内容行
        if line:
            result.append(line)
        i += 1

    return "\n".join(result)

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    blocks = parse_questions(text)
    print(f"共读取到 {len(blocks)} 道题目（含重复）")

    seen_keys = {}
    unique_blocks = []
    dup_count = 0

    for block in blocks:
        key = get_question_key(block)
        if key not in seen_keys:
            seen_keys[key] = True
            unique_blocks.append(block)
        else:
            dup_count += 1

    print(f"重复题目：{dup_count} 道，去重后剩余：{len(unique_blocks)} 道")

    md_lines = [
        "# 题库（去重版）",
        "",
        f"> 共 {len(unique_blocks)} 道题目（已去除 {dup_count} 道重复题）",
        "",
        "---",
        "",
    ]

    for idx, block in enumerate(unique_blocks, start=1):
        md_lines.append(format_question_md_v2(block, idx))
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"已保存到：{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
