import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import dotenv
import requests


def sendwechat(title, message, key=None):
    """
    发送成绩数据到微信（Server酱），desp 字段支持 Markdown 渲染
    :param title: 消息标题
    :param message: 要发送的消息
    :param key: 微信推送Key
    :return: None
    """
    base_url = "https://sctapi.ftqq.com/"
    key = key or os.getenv("SERVER_KEY", None)
    if key is None:
        raise ValueError("请提供微信推送Key")
    wechat_url = f"{base_url}{key}.send"

    desp = format_markdown(message)
    # print(desp)  # 调试输出，查看 Markdown 格式是否正确
    payload = {"title": title, "desp": desp}
    response = requests.post(wechat_url, json=payload)

    if response.status_code == 200:
        print("成绩数据已成功发送到微信！")
    else:
        print(f"发送失败，状态码: {response.status_code}, 响应内容: {response.text}")


def format_markdown(content: str) -> str:
    """
    把 message.py 拼出的纯文本内容转换成 Markdown，供 Server酱 desp 字段渲染
    """
    lines = content.splitlines()
    idx = lines.index("成绩单摘要:")
    change_lines = [l for l in lines[1:idx] if l.strip()]
    summary_lines = [l for l in lines[idx + 1:] if l.strip()]

    md = []

    # 课程变动部分：按 "新课程" / "成绩变动" / "课程被删除" 给不同的前缀符号
    md.append("### 📋 课程变动\n")
    if change_lines:
        for line in change_lines:
            if line.startswith("新课程"):
                emoji = "🆕"
            elif line.startswith("成绩变动"):
                emoji = "✏️"
            elif line.startswith("课程被删除"):
                emoji = "🗑️"
            else:
                emoji = "•"
            md.append(f"- {emoji} {line}")
    else:
        md.append("- 无课程级别的变动")

    md.append("\n---\n")

    # 成绩单摘要部分：用 Markdown 表格呈现，比纯列表更易读
    md.append("### 📊 成绩单摘要\n")
    md.append("| 学期 | GPA | 课程数 |")
    md.append("|---|---|---|")
    for line in summary_lines:
        try:
            sem_part, rest = line.split(" GPA: ")
            gpa_part, num_part = rest.split(" 课程数: ")
            md.append(f"| {sem_part} | {gpa_part} | {num_part} |")
        except ValueError:
            # 解析失败（比如 "Total" 行格式略有不同）就原样降级展示，不丢数据
            md.append(f"| {line} | | |")

    return "\n".join(md)


def sendemail(subject: str, content: str, to_addr: str = None):
    """
    发送邮件
    """
    from_addr = os.environ["QQMAIL"]
    auth_code = os.environ["SMTPCODE"]  # 不指定收件人就默认发给自己
    to_addr = to_addr or os.getenv("TOMAIL", None) or from_addr

    msg = MIMEMultipart("alternative")
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = Header(subject, "utf-8")

    lines = content.splitlines()
    idx = lines.index("成绩单摘要:")
    html_content = "<html><body style='font-family: sans-serif;'>"
    html_content += f"<h2>{subject}</h2>"
    html_content += "<details>"
    html_content += "<summary>点击查看详情......................................................................................</summary>"  # 折叠时唯一可见的文字
    html_content += "<h3>课程变动</h3><ul>"
    for line in lines[1:idx]:
        if line.strip():  # 忽略空行
            html_content += f"<li>{line}</li>"
    html_content += "</ul>"
    html_content += "<h3>成绩单摘要</h3><ul>"
    for line in lines[idx + 1:]:
        if line.strip():  # 忽略空行
            html_content += f"<li>{line}</li>"
    html_content += "</ul>"
    html_content += "</details>"
    html_content += "</body></html>"
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    try:
        # QQ邮箱 SMTP 服务器，465端口走 SSL
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(from_addr, auth_code)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败：{e}")


if __name__ == "__main__":
    dotenv.load_dotenv()
    content = """课程变动详情:
新课程：2025-2026学年2学期 摸鱼学导论 4.0 3.0
成绩变动：2025-2026学年1学期 哲学 4.0 2.0
成绩单摘要:
2025-2026学年2学期 GPA: 1.145 课程数: 114514
2025-2026学年1学期 GPA: 1.419 课程数: 1919
Total GPA: 1.9810 课程数: 810
"""
    sendemail("喜！", content)
    sendwechat("喜！", content)  # 本地测试需要先在 .env 配置 SERVER_KEY