import json
from datetime import datetime as dt

import numpy as np
import pandas as pd
import pymysql
import requests
from bs4 import BeautifulSoup


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
    if (theme_df.index.value_counts() > 1).sum() != 0:
        theme_df = read_today_theme()
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
        
        print(f'Theme Read: {cnt} / {finish}', end='\r')
    return theme_stocks
    

def update_today_theme_info():
    with open('db_info.json', 'r') as json_file:
        db_info = json.load(json_file)
    conn = pymysql.connect(**db_info)

    with conn.cursor() as curs:
        sql = """
        CREATE TABLE IF NOT EXISTS theme (
            dateint INT(10),
            theme_code VARCHAR(10),
            theme_name VARCHAR(40),
            prev_day_rtn FLOAT,
            stock_code LONGTEXT,
            updated_at TIMESTAMP,
            PRIMARY KEY (dateint, theme_code))
        """
        curs.execute(sql)
    conn.commit()
    
    today_theme = read_today_theme()
    today_theme_code = today_theme.index.values
    theme_stocks = get_theme_stocks(today_theme_code)
    
    today = dt.now()
    today_int = int(today.strftime('%Y%m%d'))
    finish = len(theme_stocks)
    with conn.cursor() as curs:
        for cnt, k in enumerate(theme_stocks, start=1):
            theme_name = today_theme.loc[k,'name']
            theme_rtn = today_theme.loc[k,'rtn']
            stock_code = ','.join(theme_stocks[k])
            
            sql = f"""
            REPLACE INTO theme VALUES (
                {today_int}, '{k}', '{theme_name}', {theme_rtn}, '{stock_code}', '{today}')
            """
            curs.execute(sql)
            conn.commit()
            
            print(f'Theme Update: {cnt} / {finish}', end='\r')
        
    print('Theme Data Update: Success')
    

# 평일 오전 8시 30분 실행 예정
if __name__ == '__main__':  
    today = dt.today().weekday
    if today != 5 and today != 6:
        update_today_theme_info()