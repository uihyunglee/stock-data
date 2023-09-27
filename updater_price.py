import ctypes
from datetime import datetime as dt
import win32com.client
import json

import numpy as np
import pandas as pd
import pymysql

cpStatus = win32com.client.Dispatch('CpUtil.CpCybos') # 시스템 상태 정보
cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil') # 주문 관련 도구
cpStockCode = win32com.client.Dispatch("CpUtil.CpStockCode")
cpCodeMgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")


class PriceUpdater:
    def __init__(self):
        self.check_creon_system()
        
        with open('db_info.json', 'r') as json_file:
            db_info = json.load(json_file)
        self.conn = pymysql.connect(**db_info)
        
        with self.conn.cursor() as curs:
            sql = """
            CREATE TABLE IF NOT EXISTS company_info (
                sh7code VARCHAR(10),
                name VARCHAR(40),
                full_code VARCHAR(20),
                ind_code VARCHAR(10),
                sec_code INT(10),
                listed_date INT(10),
                fiscal_month INT(10),
                arrg_sby INT(10),
                supervision INT(10),
                status INT(10),
                captial INT(10),
                updated_at TIMESTAMP,
                PRIMARY KEY (sh7code))
            """
            curs.execute(sql)
            sql = """
            CREATE TABLE IF NOT EXISTS daily_price (
                dateint INT(10),
                sh7code VARCHAR(10),
                open BIGINT(20),
                high BIGINT(20),
                low BIGINT(20),
                close BIGINT(20),
                vol BIGINT(20),
                trd_val BIGINT(20),
                listed_sh BIGINT(20),
                mc BIGINT(20),
                frg_holding BIGINT(20),
                adj_dateint INT(10),
                adj_ratio INT(10),
                org_na BIGINT(20),
                org_cum_na BIGINT(20),
                PRIMARY KEY (dateint, sh7code))
            """
            curs.execute(sql)
        self.conn.commit()
        
        self.listed_codes = self.get_listed_stocks()
        
    def check_creon_system(self):
        # 관리자 권한으로 프로세스 실행 여부
        if not ctypes.windll.shell32.IsUserAnAdmin():
            raise Exception('check_creon_system() : admin user -> FAILED')
        # 연결 여부 체크
        if (cpStatus.IsConnect == 0):
            raise Exception('check_creon_system() : connect to server -> FAILED')
        # 주문 관련 초기화
        if (cpTradeUtil.TradeInit(0) != 0):
            raise Exception('check_creon_system() : init trade -> FAILED')
    
    def get_listed_stocks(self):
        kospi_codes = cpCodeMgr.GetStockListByMarket(1)
        kosdaq_codes = cpCodeMgr.GetStockListByMarket(2)
        listed_codes = kospi_codes + kosdaq_codes
        return listed_codes

    def update_company_info(self):
        today = dt.now()
        finish = len(self.listed_codes)
        with self.conn.cursor() as curs:
            for cnt, code in enumerate(self.listed_codes, start=1):
                sh7code = code
                name = cpCodeMgr.CodeToName(code)
                full_code = cpStockCode.CodeToFullCode(code)
                ind_code = cpCodeMgr.GetStockIndustryCode(code)
                sec_code = cpCodeMgr.GetStockSectionKind(code)
                listed_date = cpCodeMgr.GetStockListedDate(code)
                fiscal_month = cpCodeMgr.GetStockFiscalMonth(code)
                arrg_sby = cpCodeMgr.IsStockArrgSby(code)
                supervision = cpCodeMgr.GetStockSupervisionKind(code)
                status = cpCodeMgr.GetStockStatusKind(code)
                capital = cpCodeMgr.GetStockCapital(code)

                sql = f"""
                REPLACE INTO company_info VALUES (
                    '{sh7code}', '{name}', '{full_code}', '{ind_code}', {sec_code}, {listed_date}
                    ,{fiscal_month}, {arrg_sby}, {supervision}, {status}, {capital}, '{today}')
                """
                curs.execute(sql)
                self.conn.commit()
                
                print(f'Company Info Update: {cnt} / {finish}', end='\r')
                
        print('Company information Update: Success')

