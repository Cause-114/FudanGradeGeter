from send import sendwechat, sendemail
from grade import GradeGeter
from message import message
from cryptography.fernet import Fernet
import json
import dotenv
import os

GRADES_FILE = "grades.enc"


def load_old_data(fernet: Fernet, path: str = GRADES_FILE):
    """读取并解密旧数据，文件不存在/为空/解密失败时返回 (None, None)"""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None, None
    try:
        with open(path, "rb") as file:
            decrypted = fernet.decrypt(file.read())
        payload = json.loads(decrypted)
        return payload.get("grades"), payload.get("stat")
    except Exception as e:
        return None, None


def save_data(fernet: Fernet, grades: dict, stat: dict, path: str = GRADES_FILE):
    """把 grades 和 stat 打包成一个 dict 整体加密保存"""
    payload = {"grades": grades, "stat": stat}
    data = json.dumps(payload, ensure_ascii=False).encode()
    encrypted = fernet.encrypt(data)
    with open(path, "wb") as file:
        file.write(encrypted)


if __name__ == "__main__":
    dotenv.load_dotenv() # 加载环境变量
    bot = GradeGeter(os.getenv("STUID"), os.getenv("PASSW")) # 构建 GradeGeter 实例
    grades, stat = bot.interface() # 获取成绩数据
    f = Fernet(os.environ["ENCRYPT"].encode()) # 获取加密器
    old_grades, old_stat = load_old_data(f) # 读取旧数据
    save_data(f, grades, stat) # 保存新数据
    update, title, msg = message(old_grades, grades, old_stat, stat)
    if update:
        if os.getenv("QQMAIL") and os.getenv("SMTPCODE"):
            sendemail(title, msg)
        elif (skey := os.getenv("SERVER_KEY", None)) is not None:
            sendwechat(title, msg, skey)
