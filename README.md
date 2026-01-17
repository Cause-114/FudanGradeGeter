# FudanGradeGeter

复旦大学成绩查询工具，用于自动化获取和处理复旦大学学生的成绩信息。

## 功能特性

- 自动登录复旦大学教务系统
- 获取学期成绩信息

## 安装说明

1. 确保已安装Python 3.x版本
2. 安装依赖库：
   ```bash
   pip install -r requirements.txt
   ```
   或者你自己手动把那三个模块安装，如：
   ```bash
   pip install requests
   pip install beautifulsoup4
   pip install pycryptodome
   ```

## 使用说明
如果你懒得把整个仓库下下来，可以只选择copy main.py文件，安装好依赖后，在main.py文件中的最下面修改用户名和密码，运行main.py即可。

在GradeGeter.interface 中可以选择把 `self._save()` 取消注释，保存数据为`transcript.json`与`statis.json`。

预期按照以上的步骤使用会在终端打印你每个学期的绩点与课程门数以及总绩点与课程门数。
