from pywinauto import application
import os, time
import json


with open(f"info.json", "r") as json_file:
    data = json.load(json_file)


os.system('taskkill /IM coStarter* /F /T')
os.system('taskkill /IM CpStart* /F /T')
os.system('wmic process where "name like \'%coStarter%\'" call terminate')
os.system('wmic process where "name like \'%CpStart%\'" call terminate')


time.sleep(5)
app = application.Application()
app.start(f"C:\CREON\STARTER\coStarter.exe /prj:cp /id:{data['id']} /pwd:{data['pwd']} /pwdcert:{data['pwdcert']} /autostart")
time.sleep(60)
