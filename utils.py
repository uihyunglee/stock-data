import json
import re

import numpy as np
import pandas as pd

import pymysql


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
        theme_data_df = pd.read_sql(sql, self.conn)
        theme_data_df['stock_code'] = theme_data_df['stock_code'].apply(lambda str_: str_.split(','))
        theme_data_df.set_index('theme_code', drop=True, inplace=True)
        return theme_data_df