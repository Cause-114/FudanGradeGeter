from login import FudanLogin


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
        return self.allgrades, self.statis
        # self._print()