def diff_grades(old_grades: dict, new_grades: dict) -> dict:
    """
    返回结构:
    new_courses: [{semester, courseName, gp, credits, mark}, ...]
    """
    changes = []

    for semester, courses in new_grades.items():
        if semester not in old_grades: # 新学期
            for course in courses:
                changes.append(
                    {
                        "semester": semester,
                        "courseName": course["courseName"],
                        "gp": course["gp"],
                        "credits": course["credits"],
                        "mark": 0,
                    }
                )
            continue
        lesson_pld = {course["lessonCode"]: course["gp"] for course in old_grades[semester]}
        for course in courses:
            if course["lessonCode"] not in lesson_pld: # 新课程
                changes.append(
                    {
                        "semester": semester,
                        "courseName": course["courseName"],
                        "gp": course["gp"],
                        "credits": course["credits"],
                        "mark": 0,
                    }
                )
            elif lesson_pld[course["lessonCode"]] != course["gp"]: # 成绩变动
                changes.append(
                    {
                        "semester": semester,
                        "courseName": course["courseName"],
                        "gp": course["gp"],
                        "credits": course["credits"],
                        "mark": 1,
                    }
                )
        lesson_pld = {course["lessonCode"]: course["gp"] for course in courses}
        for course in old_grades[semester]:
            if course["lessonCode"] not in lesson_pld: # 课程被删除
                changes.append(
                    {
                        "semester": semester,
                        "courseName": course["courseName"],
                        "gp": course["gp"],
                        "credits": course["credits"],
                        "mark": 2,
                    }
                )
    return changes

def good_or_bad(oldsummary: dict, newsummary: dict) -> str:
    """
    返回值:
    "喜！": 总GPA上升
    "没变！": 总GPA无变化
    "悲！": 总GPA下降
    """
    if oldsummary is None:
        return "首次获取成绩"
    oldgpa = oldsummary["Total"]["GPA"]
    newgpa = newsummary["Total"]["GPA"]
    if newgpa > oldgpa:
        return "喜！"
    elif newgpa == oldgpa:
        return "没变！"
    else:
        return "悲！"


def message(old_grades: dict, new_grades: dict, oldsummary: dict, newsummary: dict) -> tuple:
    """
    返回值:
    (bool, str): (是否有变动, 成绩变动消息)
    """
    changes = diff_grades(old_grades, new_grades) if old_grades is not None else []
    title = f"{good_or_bad(oldsummary, newsummary)}\n"
    msg="课程变动详情:\n"
    for change in changes:
        if change["mark"] == 0:
            msg += f"新课程：{change['semester']}, {change['courseName']}。GPA: {change['gp']}, 学分：{change['credits']}\n"
        elif change["mark"] == 1:
            msg += f"成绩变动：{change['semester']}, {change['courseName']}。GPA: {change['gp']}, 学分：{change['credits']}\n"
        elif change["mark"] == 2:
            msg += f"课程被删除：{change['semester']}, {change['courseName']}。GPA: {change['gp']}, 学分：{change['credits']}\n"
    msg+="\n\n成绩单摘要:\n"
    for sem, stat in newsummary.items():
        msg += f"{sem} GPA: {stat['GPA']:.4f} 课程数: {stat['num']}\n"
    if not changes and old_grades is not None:
        return False, "", ""
    return True, title, msg