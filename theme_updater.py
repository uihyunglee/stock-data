from datetime import datetime as dt
import json
import sys

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests


def get_last_page(html):
    bs = BeautifulSoup(html, 'lxml')
    pgrr = bs.find('td', class_='pgRR')
    s = str(pgrr.a["href"]).split('=')
    lastpage = s[-1]
    return int(lastpage)
    
    
def read_today_theme():
    url = "https://finance.naver.com/sise/theme.naver"
    html = requests.get(url, headers={'User-agent' : 'Mozilla/5.0'}).text
    pages = get_last_page(html)
    
    total_theme_name = []
    total_theme_code = []
    total_theme_rtn = []
    
    for p in range(1, pages+1):
        url = f"https://finance.naver.com/sise/theme.naver?&page={p}"
        html = requests.get(url,  headers={'User-agent' : 'Mozilla/5.0'}).text
        bs = BeautifulSoup(html, 'lxml')
        
        col_type1 = bs.findAll('td', class_='col_type1')
        theme_name = list(map(lambda x: x.getText(), col_type1))
        theme_code = list(map(lambda x: x.a['href'].split('=')[-1], col_type1))

        col_type2 = bs.findAll('td', class_='number col_type2')
        theme_rtn = list(map(lambda x: x.getText()[6:-7], col_type2))
        
        total_theme_name += theme_name
        total_theme_code += theme_code
        total_theme_rtn += theme_rtn
        
    theme_df = pd.DataFrame(index=total_theme_code, columns=['name', 'rtn'], data = np.array([total_theme_name, total_theme_rtn]).T)
    
    try:
        theme_df['rtn'] = theme_df['rtn'].astype(np.float64)
    except ValueError:
        theme_df['rtn'][theme_df['rtn'] == ''] = '0'
        theme_df['rtn'] = theme_df['rtn'].astype(np.float64)
    return theme_df


def get_theme_stocks(today_theme_code):
    theme_stocks = dict()
    finish = len(today_theme_code)

    for cnt, theme_code in enumerate(today_theme_code, start=1):
        url = f'https://finance.naver.com/sise/sise_group_detail.naver?type=theme&no={theme_code}'
        html = requests.get(url, headers={'User-agent' : 'Mozilla/5.0'}).text
        bs = BeautifulSoup(html, 'lxml')
        
        name_area = bs.findAll('div', class_='name_area')
        stock_codes = list(map(lambda x: 'A' + x.a['href'].split('=')[-1], name_area))
        theme_stocks[theme_code] = stock_codes
        
        print(f'Theme Update: {cnt} / {finish}', end='\r')
    return theme_stocks
    

def update_today_theme_info():
    # 추후 NoSQL로 쌓을 예정
    today_theme = read_today_theme()
    today_theme_code = today_theme.index.values
    theme_stocks = get_theme_stocks(today_theme_code)
    
    today = dt.now().strftime('%Y%m%d')
    with open(f"daily_theme_data/{today}.json", "w") as json_file:
        json.dump(theme_stocks, json_file, indent=4)
        
    print('Theme Data Update: Success')
    

# 평일 오전 8시 30분 실행 예정
if __name__ == '__main__':  
    today = dt.today().weekday
    if today == 5 or today == 6:
        sys.exit(0)
    
    update_today_theme_info()
    sys.exit(0)