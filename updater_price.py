import ctypes
import json
from datetime import datetime as dt
from datetime import timedelta as td

import pymysql
import win32com.client

cpStatus = win32com.client.Dispatch('CpUtil.CpCybos') # 시스템 상태 정보
cpTradeUtil = win32com.client.Dispatch('CpTrade.CpTdUtil') # 주문 관련 도구
cpStockCode = win32com.client.Dispatch("CpUtil.CpStockCode")
cpCodeMgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")
cpStockChart = win32com.client.Dispatch("CpSysDib.StockChart")


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
                updated_at TIMESTAMP,
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

    def get_start_date(self):
        with self.conn.cursor() as curs:
            sql = "SELECT max(dateint) FROM daily_price"
            curs.execute(sql)
            rs = curs.fetchone()
            last_date = rs[0]
        if last_date == None:
            start_date = 20130101
        else:
            next_day = dt.strptime(str(last_date), '%Y%m%d') + td(days=1)
            start_date = int(next_day.strftime('%Y%m%d'))
        return start_date
    
    def update_daily_price_info(self):
        today = dt.now()
        start_date = self.get_start_date()
        end_date = int(today.strftime('%Y%m%d'))
        finish = len(self.listed_codes)
        with self.conn.cursor() as curs:
            for cnt, code in enumerate(self.listed_codes, start=1):
                cpStockChart.SetInputValue(0, code)  # 종목 코드 - 삼성전자
                cpStockChart.SetInputValue(1, ord('1'))  # 기간
                cpStockChart.SetInputValue(2, end_date)  # end
                cpStockChart.SetInputValue(3, start_date)  # start
                cpStockChart.SetInputValue(5, [0,2,3,4,5,8,9,12,13,17,18,19,20,21])
                # 0:날짜, 23458:OHLCV, 9:거래대금, 12:상장주식수, 13:시가총액, 17:외인보유비율
                # 18:수정일자, 19:수정주가비율,20:기관순매수, 21:기관누적순매수
                cpStockChart.SetInputValue(6, ord('D'))  # 일봉
                cpStockChart.SetInputValue(9, ord('1')) # 수정
                cpStockChart.BlockRequest()

                idx_len = cpStockChart.GetHeaderValue(3)
                for i in range(idx_len):
                    dateint = cpStockChart.GetDataValue(0, i)
                    sh7code = code
                    open  = cpStockChart.GetDataValue(1, i)
                    high = cpStockChart.GetDataValue(2, i)
                    low = cpStockChart.GetDataValue(3, i)
                    close = cpStockChart.GetDataValue(4, i)
                    vol = cpStockChart.GetDataValue(5, i)
                    trd_val = cpStockChart.GetDataValue(6, i)
                    listed_sh = cpStockChart.GetDataValue(7, i)
                    mc = cpStockChart.GetDataValue(8, i)
                    frg_holding = cpStockChart.GetDataValue(9, i)
                    adj_dateint = cpStockChart.GetDataValue(10, i)
                    adj_ratio = cpStockChart.GetDataValue(11, i)
                    org_na = cpStockChart.GetDataValue(12, i)
                    org_cum_na = cpStockChart.GetDataValue(13, i)

                    sql = f"""
                    REPLACE INTO daily_price VALUES (
                        {dateint}, '{sh7code}', {open}, {high}, {low}, {close},{vol}, {trd_val}, {listed_sh}
                        , {mc}, {frg_holding}, {adj_dateint}, {adj_ratio}, {org_na}, {org_cum_na}, '{today}')
                    """
                    curs.execute(sql)
                self.conn.commit()
                
                print(f'Daily Price Info Update: {cnt} / {finish}', end='\r')
                
        print('Daily Price Information Update: Success')


# 평일 오후 20시 실행 예정        
if __name__ == '__main__':
    today = dt.today().weekday
    if today != 5 and today != 6:
        pu = PriceUpdater()
        pu.check_creon_system()
        pu.update_company_info()
        pu.update_daily_price_info()