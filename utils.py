import json

import numpy as np
import pandas as pd

import pymysql


class DBmgr:
    def __init__(self):
        with open('db_info.json', 'r') as json_file:
            db_info = json.load(json_file)
        self.conn = pymysql.connect(**db_info)
        
    def get_table_names(self):
        sql = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        table_name = pd.read_sql(sql, self.conn)
        return list(table_name.values.reshape(-1))
