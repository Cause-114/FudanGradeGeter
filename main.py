import requests
import re
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5


class FudanLogin:
    def __init__(self, username: str, password: str, target_url):
        self.username = username
        self.password = password
        self.session = requests.Session()
        # 设置通用 headers
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            }
        )
        self.params = {"lck": "", "entityId": "", "PubKey": "", "authChainCode": ""}
        self.tg_url = target_url
        self.cas_base = "https://id.fudan.edu.cn"

    def _get_params(self):
        """获取登录必要参数"""
        # Step 1: 触发重定向，获取参数
        resp = self.session.get(self.tg_url, allow_redirects=True)
        try:
            self.params["lck"] = resp.url.split("lck=")[1].split("&")[0]
            self.params["entityId"] = resp.url.split("entityId=")[1].split("&")[0]
        except Exception:
            print("Failed to get params lck or entityId")

        # Step 2: 获取公钥并加密密码
        self.params["PubKey"] = self.session.post(
            f"{self.cas_base}/idp/authn/getJsPublicKey"
        ).json()["data"]
        self._encrypt_password()

        # step3: 获取用户密码对应的认证链编号
        auth_resp = self.session.post(
            f"{self.cas_base}/idp/authn/queryAuthMethods",
            json={"lck": self.params["lck"], "entityId": self.params["entityId"]},
        )
        for method in auth_resp.json()["data"]:
            if method["moduleCode"] == "userAndPwd":
                self.params["authChainCode"] = method["authChainCode"]
                break

    def _encrypt_password(self):
        """使用 RSA 公钥加密密码"""
        der = base64.b64decode(self.params["PubKey"])
        key = RSA.import_key(der)
        cipher = PKCS1_v1_5.new(key)
        encrypted = cipher.encrypt(self.password.encode("utf-8"))
        self.password = base64.b64encode(encrypted).decode("utf-8")

    def _auth_execute(self):
        """执行账号密码认证"""
        # step1: 执行账号密码认证
        payload = {
            "authModuleCode": "userAndPwd",
            "authChainCode": self.params["authChainCode"],
            "entityId": self.params["entityId"],
            "requestType": "chain_type",
            "lck": self.params["lck"],
            "authPara": {
                "loginName": self.username,
                "password": self.password,
                "verifyCode": "",
            },
        }
        resp = self.session.post(f"{self.cas_base}/idp/authn/authExecute", json=payload)
        if resp.status_code != 200:
            print("Login failed! Check your password or username")

        # step2: 解析loginToken并从中获取跳转地址
        login_token = resp.json()["loginToken"]
        resp = self.session.post(
            f"{self.cas_base}/idp/authCenter/authnEngine",
            params={"locale": "zh-CN"},
            data={"loginToken": login_token},
        )
        match = re.search(r'locationValue\s*=\s*"([^"]+)"', resp.text)
        location_value = match.group(1).replace("&amp;", "&")
        print("解析出的跳转地址:", location_value)

        # step3: 跳转目标地址
        resp = self.session.get(location_value, allow_redirects=True)
        if resp.status_code == 200:
            print(f"AUTH EXECUTE SUCCESS at {resp.url}")
        else:
            print("failed with response status code:", resp.status_code)
        return resp.url

    def login(self):
        """重定向至认证->获取必要参数与cookies->执行登录返回session"""
        self._get_params()
        url = self._auth_execute()
        return self.session, url


class GradeGeter:
    def __init__(self, username: str, password: str):
        self.jw_url = "https://fdjwgl.fudan.edu.cn/student"
        self.session, _ = FudanLogin(username, password, f"{self.jw_url}/home").login()
        self.stuid = ""
        self.semesters = {}
        self.allgrades = {}
        self.statis = {}

    def _get_StuSemesterId(self):
        """从成绩界面中提取学生ID与学期信息"""
        from bs4 import BeautifulSoup

        resp = self.session.get(f"{self.jw_url}/for-std/grade/sheet/")
        self.stuid = resp.url.split("index/")[1]
        soup = BeautifulSoup(resp.text, "html.parser")

        # 查找学期选择下拉框
        semester_select = soup.find("select", id="semester")
        if semester_select:
            for option in semester_select.find_all("option"):
                value = option.get("value")
                text = option.get_text(strip=True)
                if value and text and text != "...":
                    self.semesters[int(value)] = text

    def _get_grade(self):
        """获取成绩数据"""
        url = f"{self.jw_url}/for-std/grade/sheet/info/{self.stuid}"
        data = self.session.get(url).json()
        grades_by_semester = data.get("semesterId2studentGrades", {})

        tolgp, tolcre, tolnum = 0, 0, 0  # 总学分绩、总学分、课程数
        for sem_id, sem_name in self.semesters.items():
            curgp, curcre = 0, 0
            courses = grades_by_semester.get(str(sem_id), [])
            self.allgrades[sem_name] = []
            for course in courses:
                cre = course.get("credits", 0)
                gp = course.get("gp", 0)
                cre = float(cre) if cre != None else 0
                gp = float(gp) if gp != None else 0
                self.allgrades[sem_name].append(
                    {
                        "credits": cre,
                        "gp": gp,  # 学分、绩点
                        "lessonCode": course.get("lessonCode", ""),  # 课程序号
                        "courseName": course.get("courseName", ""),  # 课程名
                    }
                )
                if cre >= 0.01 and gp >= 0.01:
                    curgp += gp * cre
                    curcre += cre
            self.statis[f"{sem_name}"] = {
                "GPA": curgp / curcre if curcre >= 0.01 else 0,
                "num": len(courses),
            }
            tolgp += curgp
            tolcre += curcre
            tolnum += len(courses)
        self.statis["Total"] = {
            "GPA": tolgp / tolcre if tolcre >= 0.01 else 0,
            "num": tolnum,
        }

    def _print(self):
        """打印成绩单摘要"""
        print("\n成绩单摘要:")
        for name, stat in self.statis.items():
            print(f"{name}\tGPA:{stat["GPA"]:.4f}\t{stat["num"]}门课程")

    def _save(self):
        """保存成绩数据为JSON"""
        import json

        with open("transcript.json", "w", encoding="utf-8") as f:
            json.dump(self.allgrades, f, ensure_ascii=False, indent=2)
        with open("statis.json", "w", encoding="utf-8") as f:
            json.dump(self.statis, f, ensure_ascii=False, indent=2)

    def interface(self):
        """对外接口，可选择是否保存为文件"""
        self._get_StuSemesterId()
        self._get_grade()
        self._print()
        # self._save()

if __name__ == "__main__":
    USERNAME = ""  # 学号
    PASSWORD = ""  # 密码
    # 你不应该直接调用'_'开头的函数
    bot = GradeGeter(USERNAME, PASSWORD)
    session = bot.interface()