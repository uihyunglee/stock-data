# 크레온 자동 로그인 모듈
# 32비트에서 매일 20시 실행 예정
# 같은 경로에 로그인 정보를 담은 creon_info.json 필요 (id, pwd, pwdcert)

from pywinauto import application
import os, time
from config import CREON_INFO


os.system('taskkill /IM coStarter* /F /T')
os.system('taskkill /IM CpStart* /F /T')
os.system('wmic process where "name like \'%coStarter%\'" call terminate')
os.system('wmic process where "name like \'%CpStart%\'" call terminate')

time.sleep(5)
app = application.Application()
app_path = 'C:\CREON\STARTER\coStarter.exe'
login_info = f"/id:{CREON_INFO['id']} /pwd:{CREON_INFO['pwd']} /pwdcert:{CREON_INFO['pwdcert']}"
app.start(f"{app_path} /prj:cp {login_info} /autostart")
time.sleep(60)