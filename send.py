import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from turtle import title
import dotenv
import requests


def sendwechat(title, message, key=None):
    """
    发送成绩数据到微信
    :param title: 消息标题
    :param message: 要发送的消息
    :param key: 微信推送Key
    :return: None
    """
    # 微信推送的URL和Token
    # server chan API URL
    base_url = "https://sctapi.ftqq.com/"
    key = key or os.getenv("SERVER_KEY", None)
    if key is None:
        raise ValueError("请提供微信推送Key")
    wechat_url = f"{base_url}{key}.send"
    payload = {"title": title, "desp": message}
    # 发送POST请求到微信接口
    response = requests.post(wechat_url, json=payload)

    # 检查响应状态
    if response.status_code == 200:
        print("成绩数据已成功发送到微信！")
    else:
        print(f"发送失败，状态码: {response.status_code}, 响应内容: {response.text}")


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
    html_content += "<summary>点击查看详情......................................................................................</summary>" 
    # 折叠时唯一可见的文字，来屏蔽细节，让你点进去才能看到具体成绩。
    html_content += "<h3>课程变动</h3><ul>"
    for line in lines[1:idx]:
        html_content += f"<li>{line}</li>"
    html_content += "</ul>"
    html_content += "<h3>成绩单摘要</h3><ul>"
    for line in lines[idx + 1:]:
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
xxx  yyy
zzz  www
成绩单摘要:
XXX YYY
ZZZ WWW
"""
    sendemail("喜！", content)