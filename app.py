import requests
import yfinance as yf
import pandas as pd
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from datetime import date
from flask import Flask, render_template, request
from io import BytesIO
import base64
from datetime import datetime, timedelta
import calendar
import json
import jpholiday
from bs4 import BeautifulSoup
from urllib.request import urlopen
import os
import re

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def main_stock():

    if request.method == 'POST':
        stock_code = None
        stock_name = None

        with open('data/data.json', encoding='utf-8') as f:
            previous_data = json.load(f)

        if ((request.form.get('input_code') == None) and (request.form.get('input_name') == None) and (previous_data['stock_name'] == "")):

          return render_template('index.html')


        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(APP_ROOT, 'static', 'data_j.xls')

        if not os.path.isfile(file_path):
            url = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
            r = requests.get(url)
            with open(file_path, 'wb') as output:
                output.write(r.content)

        stocklist = pd.read_excel(file_path)

        stocklist.loc[stocklist["市場・商品区分"]=="市場第一部（内国株）",
                    ["コード","銘柄名","33業種コード","33業種区分","規模コード","規模区分"]
                    ]
                  
        if(request.form.get('input_name') != None):
           


            stock_name = request.form['input_name']  
            if not stock_name in stocklist['銘柄名'].values:
              if(stock_name == None):
                    return render_template('index.html')
              else:    
                stock_code = previous_data['stock_code']
                stock_name = previous_data['stock_name']
            else:
                desired_index = stocklist[stocklist['銘柄名'] == stock_name].index[0]  # 'ニッソウ'に一致する最初の行のインデックスを取得します
                stock_code = str(stocklist.loc[desired_index, 'コード'])  # 指定したインデックスの'コード'列の値を取得します
                data_json = {
                    'stock_name': stock_name,
                    'stock_code': stock_code
                }
                with open('data/data.json', 'w') as f:
                    json.dump(data_json, f, indent=2)


    

        enddate= date.today()

        if(request.form.get('years1') != None):
            today = datetime.now()
            startdate = today - timedelta(days=30 * 12)
            time_period = "1年間の変動"
        elif(request.form.get('years5') != None):
            today = datetime.now()
            startdate = today - timedelta(days=30 * 60)
            time_period = "5年間の変動"
        elif(request.form.get('years10') != None):
            today = datetime.now()
            startdate = today - timedelta(days=30 * 120)
            time_period = "10年間の変動"
        elif(request.form.get('months6') != None):
            today = datetime.now()
            startdate = today - timedelta(days=30 * 6)   
            time_period = "6か月間の変動"   
        elif(request.form.get('months1') != None):
            today = datetime.now()
            _, days_in_last_month = calendar.monthrange(today.year, today.month - 1)
            startdate = today - timedelta(days=days_in_last_month)
            time_period = "1か月間の変動"
        elif(request.form.get('days5') != None):
            today = datetime.now()
            startdate = today - timedelta(days=5)   
            time_period = "5日間の変動"
     
            while(enddate.weekday() >= 5 or jpholiday.is_holiday(enddate)):

                enddate = enddate - timedelta(days=1)
                startdate = startdate - timedelta(days=1) 
            
        elif(request.form.get('days1') != None):
            today = datetime.now()
            startdate = today - timedelta(days=1)   
            time_period = "1日の変動"

            while(enddate.weekday() >= 5 or jpholiday.is_holiday(enddate)):
   
                enddate = enddate - timedelta(days=1)
                startdate = startdate - timedelta(days=1)  
          

        elif(request.form.get('year_first') != None):
            startdate =  str(datetime.today().year) + '-01-01'
            time_period = "年初来"
        elif((request.form.get('end_input') != None) and (request.form.get('start_input') != None)):
            startdate = datetime.strptime(request.form["start_input"], '%Y-%m-%d')
            enddate = datetime.strptime(request.form["end_input"], '%Y-%m-%d')
            today = datetime.now() 


            if((enddate > startdate) and (enddate <= today)):
                time_period = f"{startdate.year}年{startdate.month}月{startdate.day}日 ~ {enddate.year}年{enddate.month}月{enddate.day}日"
                startdate = str(startdate.date())
                enddate= date.today()
                
            else:
                 time_period = "年初来"
                 startdate = str(datetime.today().year) + '-01-01'
                 enddate= date.today()


        else:
            time_period = "年初来"
            startdate = str(datetime.today().year) + '-01-01'



        if(request.form.get('input_code') != None):
            stock_code = str(request.form['input_code'])
            if not stock_code in stocklist['コード'].astype(str).values:
              if(stock_name == None):
                    return render_template('index.html')
              else:    
                stock_code = previous_data['stock_code']
                stock_name = previous_data['stock_name']
            else:
 
                desired_index = stocklist[stocklist['コード'].astype(str) == stock_code].index[0]  # 'ニッソウ'に一致する最初の行のインデックスを取得します
                stock_name = stocklist.loc[desired_index, '銘柄名']  # 指定したインデックスの'コード'列の値を取得します

                data_json = {
                    'stock_name': stock_name,
                    'stock_code': stock_code
                }
                with open('data/data.json', 'w') as f:
                    json.dump(data_json, f, indent=2)


        if(stock_code == None):
                stock_code = previous_data['stock_code']
                stock_name = previous_data['stock_name']

        stock_code_T = stock_code + ".T"
        # startdate = str(startdate)
        enddate = str(enddate)

        stock_info = yf.Ticker(stock_code_T)

        #時価総額の取得
        market_cap = stock_info.info['marketCap']
        market_cap = int(market_cap/10**8) #億円
        market_cap = "{:,}".format(market_cap)

        cashflow_df = pd.DataFrame()
        cashflow_df = stock_info.cashflow.transpose()
        cashflow_df = cashflow_df[['Free Cash Flow',  'Operating Cash Flow', 'Investing Cash Flow', 'Financing Cash Flow']]/10**6
        cashflow_df = cashflow_df.astype(int)
        cashflow_df['日付'] = cashflow_df.index.strftime('%Y/%m')
        cashflow_df = cashflow_df[['日付', 'Free Cash Flow', 'Operating Cash Flow', 'Investing Cash Flow', 'Financing Cash Flow']]
        cashflow_df = cashflow_df.rename(columns={'Free Cash Flow': 'フリーキャッシュフロー', 'Operating Cash Flow': '営業キャッシュフロー', 'Investing Cash Flow': '投資キャッシュフロー', 'Financing Cash Flow':'財務キャッシュフロー'})
        for col in cashflow_df.columns[1:]:
            cashflow_df[col] = cashflow_df[col].apply(lambda x: '{:,}'.format(x))

        cashflow_df = cashflow_df[::-1]
        cashflow_df.reset_index(drop=True, inplace=True)

        stock_data = yf.download(stock_code_T, start=startdate, end=enddate)
        n225_data = yf.download("^N225", start=startdate, end=enddate)

        df = pd.DataFrame(stock_data)
        n225_df = pd.DataFrame(n225_data)
        fig = Figure()
        ax = fig.subplots()
        ax.plot(df.index, df['Close'], color='white', linewidth=1.2)
        # プロットのラベルやタイトルを設定
        
        ax.tick_params(axis='x', rotation=25, colors='white')
        ax.tick_params(axis='y', colors='white') 
        ax.grid(True, linestyle='--', color='white')
        ax.set_title("Fluctuation of Stock Prices", color="white", fontweight='bold')
        ax.set_facecolor('black')
        fig.patch.set_facecolor('black') 
        buf = BytesIO()
        fig.savefig(buf, format="png")
        graph_data = base64.b64encode(buf.getbuffer()).decode("ascii")

        fig2 = Figure()
        ax2 = fig2.subplots()
        ax2.plot(n225_df.index, n225_df['Close'], color='white', linewidth=1.2)
        # プロットのラベルやタイトルを設定

        ax2.tick_params(axis='x', rotation=25, colors='white')
        ax2.tick_params(axis='y', colors='white') 
        ax2.grid(True,  linestyle='--', color='white')

        ax2.set_title("N225", color="white", fontweight='bold')


        # 解像度の調整
        plt.tight_layout() 
        ax2.set_facecolor('black')
        fig2.patch.set_facecolor('black') 
        buf = BytesIO()
        fig2.savefig(buf, format="png")
        n225_graph = base64.b64encode(buf.getbuffer()).decode("ascii")
  

        url = "https://www.nikkei.com/nkd/company/kessan/?scode="+stock_code
  
        response = requests.get(url)
        html = response.text

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.findAll(["script", "p"]):
            # タグとその内容の削除
            tag.decompose()
        soup2 = soup.select('td', class_='m-tableType01.a-mb12.m-tableType01_table.w668.bgcGray.a-taR.a-wordBreakAll') 
        data_list = []
        for td_tag in soup2:
            data_list.append(td_tag.text)
        cleaned_list = [item for item in data_list if item != '\n\n\n\n']

        n = 5
        data_chunks = [cleaned_list[i:i + n] for i in range(0, len(cleaned_list), n)]

        # DataFrameに変換する
        df = pd.DataFrame(data_chunks)
        index_to_drop = list(range(7,17))+ list(range(21, len(df)))
        df = df.drop(index_to_drop)
        df.reset_index(drop=True, inplace=True)
        new_column = ['日付', '売上高', '営業利益', '経常利益', '当期利益', '1株利益', '1株配当', '1株純利益', 'ROE', '営業利益率', '自己資本比率']
        df.insert(0, 'New Column', new_column)
        df.columns = df.iloc[0]
        df = df.drop(0)

        df.columns = [label.replace('連I', '').replace('連S', '') for label in df.columns]

        df = df.transpose()
        df.columns = df.iloc[0]

        # 1行目を削除
        df = df[1:]
                # インデックスにある '日付' 列を一時的に新しい列に移動
        df['日付'] = df.index

        # インデックスをリセットして、'日付' 列が通常の列となるようにする
        df.reset_index(drop=True, inplace=True)



        # 列の順序を調整する
        df = df[['日付', '売上高', '営業利益', '経常利益', '当期利益', '1株利益', '1株配当', '1株純利益', 'ROE', '営業利益率', '自己資本比率']]

        html_qoq     = urlopen("https://www.nikkei.com/markets/kigyo/money-schedule/kessan/?ResultFlag=3&kwd="+str(stock_code))
        bsObj        = BeautifulSoup(html_qoq, "html.parser")
        table        = bsObj.find("div", {"class":"m-newpresSearchResults"}).find("tr",{"class":"tr2"})
        kessan_day   = table.find("th").find(text=True)
        
        kessanki_info = table.find_all("td")
        for item in range(len(kessanki_info)):
            if "期" in kessanki_info[item].find(text=True):
                kessanki       = kessanki_info[item].find(text=True)
                kessan_syubetu = kessanki_info[item+1].find(text=True).replace("\xa0","")+"決算"


        # =====================================================
        # 結果出力
        # =====================================================
        
        closing_schedule = pd.DataFrame()
        # df["銘柄コード"] = pd.Series(meigara_code)
        # df["銘柄名"]     = pd.Series(meigara_name)
        closing_schedule["決算発表日"] = pd.Series(kessan_day)
        closing_schedule["決算期"]    = pd.Series(kessanki)
        closing_schedule["決算種別"]  = pd.Series(kessan_syubetu)


        html_qoq     = urlopen(f"https://kabutan.jp/stock/finance?code={stock_code}#hanki_name")
        bsObj        = BeautifulSoup(html_qoq, "html.parser")
        table        = bsObj.find("div", {"class":"fin_year_t0_d fin_year_result_d"})
        table
        for tag in table.findAll(["img"]):
            # タグとその内容の削除
            tag.decompose()
        predict_list = []
        for td_tag in table:
            predict_list.append(td_tag.text.replace('\n', '~').replace('\xa0', '~'))
        predict_list = predict_list[1].split('~')
        print(predict_list)
        predict_list = [item for item in predict_list if item.replace('.', '', 1).replace(',', '').replace('-', '').isdigit() or item == '－' or re.match(r'^[-+]?[\d,\.]+(\*)?(倍)?$', item.strip())
        or item == "赤縮" or item=="赤拡" or re.match(r'\d{2}/\d{2}/\d{2}', item.strip()) ]

        print(predict_list)


        subset_list = [
            predict_list[0:6],
            predict_list[8:14],
            predict_list[16:22],
            predict_list[24:30],
            predict_list[32:38],
            predict_list[39:]
        ]
        predict_data = pd.DataFrame(subset_list)
        predict_data = predict_data[[0,1, 2, 3, 4, 5]]

        # columns属性を設定廃
        predict_data.columns = ["決算期", "売上高", "営業益", "経常利益", "最終益", "修正1株益"]
        predict_data.loc[predict_data.index[-1], '決算期'] = "前期比"
        predict_data['決算期'] = predict_data['決算期'].apply(lambda x: x.replace('.', '/'))        
 
         # url、パラメータを設定してリクエストを送る
        res = requests.get(f'https://news.yahoo.co.jp/search?p={stock_name}&ei=utf-8&aq=0')
        soup = BeautifulSoup(res.content, "html.parser")

        soup = soup.find_all('a', {'class': 'sc-hZiVAQ iJQlOJ newsFeed_item_link'})
        soup_list = [element for element in soup]

        link_list = []
        content_list = []

        for tag in soup_list:
            link_list.append(tag.get('href'))
            tag = str(tag.find_all('div', {'class':'newsFeed_item_title'}))
            content_list.append(re.sub(r'<[^>]*>', '', tag))
        content_list = [string.strip('[]') for string in content_list]
 
        html = render_template('index.html', graph_data=graph_data, n225_graph=n225_graph, stock_name_show=stock_name,
                                time_period=time_period, table=df, closing_schedule=closing_schedule, market_cap=market_cap,
                                cashflow_df=cashflow_df, predict_data=predict_data, link_list=link_list, content_list=content_list)





    else:
     
        html = render_template('index.html',table=None, graph_data=None, closing_schedule=None, cashflow_df=None, predict_data=None, link_list=None, content_list=None)
    return html

    # # return html

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=4444)
