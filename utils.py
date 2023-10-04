from datetime import datetime as dt
import json
import re

import numpy as np
import pandas as pd

import pymysql

TODAY = dt.now.strftime('%Y%m%d')

class DBmgr:
    def __init__(self):
        with open('db_info.json', 'r') as json_file:
            db_info = json.load(json_file)
        self.conn = pymysql.connect(**db_info)
        
    def get_all_theme_data(self):
        sql = "SELECT * FROM theme"
        theme_df = pd.read_sql(sql, self.conn)
        theme_df['stock_code'] = theme_df['stock_code'].apply(lambda str_: str_.split(','))
        return theme_df

    def get_theme_data(self, date, code=None):
        date = int(re.sub(r'[^0-9]', '', date))
        if code:
            code = f"('{code}')" if isinstance(code, str) else tuple(code)
            and_code = f"AND theme_code IN {code}"
        else:
            and_code = ''
        sql = f"SELECT theme_code, stock_code FROM theme WHERE dateint = {date} {and_code}"
        theme_df = pd.read_sql(sql, self.conn)
        theme_df['stock_code'] = theme_df['stock_code'].apply(lambda str_: str_.split(','))
        theme_df.set_index('theme_code', drop=True, inplace=True)
        return theme_df
    
    def get_stock_data(self, code=None, start_date=None, end_date=None, only_ohlcv=False):
        if start_date == None:
            start_date = '1980_01_01'
        if end_date == None:
            end_date = TODAY
        start_date = int(re.sub(r'[^0-9]', '', start_date))
        end_date = int(re.sub(r'[^0-9]', '', end_date))
        
        ohlcv_cond = 'dateint, sh7code, open, high, low, close, vol' if only_ohlcv else '*'
        
        if code == None:
            sql = f"""
            SELECT {ohlcv_cond} FROM daily_price
            WHERE dateint BETWEEN {start_date} AND {end_date}
            """
        else:
            target_code = f"('{code}')" if isinstance(code, str) else tuple(code)
            sql = f"""
            SELECT {ohlcv_cond} FROM daily_price
            WHERE (sh7code IN {target_code}) AND (dateint BETWEEN '{start_date}' AND '{end_date}')
            """
        df = pd.read_sql(sql, self.conn)
        return df