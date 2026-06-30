import base64
import re
import requests
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
