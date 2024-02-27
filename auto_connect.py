# 크레온 자동 로그인 모듈
# 32비트에서 매일 20시 실행 예정
# 같은 경로에 로그인 정보를 담은 creon_info.json 필요 (id, pwd, pwdcert)

from pywinauto import application
import os, time
import json


with open(f"creon_info.json", "r") as json_file:
    data = json.load(json_file)

os.system('taskkill /IM coStarter* /F /T')
os.system('taskkill /IM CpStart* /F /T')
os.system('wmic process where "name like \'%coStarter%\'" call terminate')
os.system('wmic process where "name like \'%CpStart%\'" call terminate')

time.sleep(5)
app = application.Application()
app.start(f"C:\CREON\STARTER\coStarter.exe /prj:cp /id:{data['id']} /pwd:{data['pwd']} /pwdcert:{data['pwdcert']} /autostart")
time.sleep(60)