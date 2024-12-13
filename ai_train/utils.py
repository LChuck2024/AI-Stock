import akshare as ak
import joblib
import streamlit as st
import yfinance as yf
import os
import pandas as pd
import requests

stock_info_sh_df = st.session_state.stock_info_sh_df
stock_info_sz_df = st.session_state.stock_info_sz_df
current_date = st.session_state.current_date.strftime("%Y-%m-%d")


def get_ticker(ticker, source='yinance'):
    stock_info = None
    if ticker in stock_info_sh_df['证券代码'].to_list():
        stock_info = stock_info_sh_df[stock_info_sh_df['证券代码'] == ticker]
        print(stock_info)
        stock_info = stock_info.reset_index(drop=True)
        ticker = ticker + '.SS' if source == 'yinance' else 'sh' + ticker
    elif ticker in stock_info_sz_df['A股代码'].to_list():
        stock_info = stock_info_sz_df[stock_info_sz_df['A股代码'] == ticker]
        print(stock_info)
        stock_info = stock_info.reset_index(drop=True)
        ticker = ticker + '.SZ' if source == 'yinance' else 'sz' + ticker
    else:
        ticker = None
    return ticker, stock_info


def get_all_tickers(channel, division):
    if channel == '上证':
        stock_info = ak.stock_info_sh_name_code(division)
    else:
        stock_info = ak.stock_info_sz_name_code(division)
    return stock_info


def get_data(ticker, period='max', interval='1d'):
    # 获得个股数据
    print(f'[yfinance]正在获取【{ticker} {current_date}】的全部历史行情信息...')
    # 如果文件已存在，则直接跳过
    if os.path.exists(f'data/src/yfinance/{ticker}_{current_date}.pkl') and joblib.load(f'data/src/yfinance/{ticker}_{current_date}.pkl') is not None:
        print(f'{ticker} {current_date}行情信息已存在，直接读取文件!')
        ticker_info_src = joblib.load(f'data/src/yfinance/{ticker}_{current_date}.pkl')
        print(ticker_info_src.shape)
        return ticker_info_src
    print(f'未检测到文件，正在重新获取【{ticker} {current_date}】的全部历史行情...')
    ticker_info = yf.Ticker(ticker)
    ticker_info_src = ticker_info.history(period=period, interval=interval)
    # try:
    #     ticker_info_src = ticker_info_src.drop(columns=['Dividends', 'Stock Splits'])
    # except Exception as e:
    #     print(f'没有获取到 dividends 和 stock splits,{e}')
    # 如果目录不存在则创建
    if not os.path.exists('data/src/yfinance/'):
        os.makedirs('data/src/yfinance/')
    # 保存文件
    print(f'获取完成{ticker_info_src.shape}')
    joblib.dump(ticker_info_src, f'data/src/yfinance/{ticker}_{current_date}.pkl')
    return ticker_info_src


def get_data_sina(ticker):
    # 获得个股数据
    print(f'[sina]正在获取【{ticker} {current_date}】的全部历史行情信息...')
    # 如果文件已存在，则直接跳过
    if os.path.exists(f'data/src/sina/{ticker}_{current_date}.pkl') and joblib.load(f'data/src/sina/{ticker}_{current_date}.pkl') is not None:
        print(f'{ticker} {current_date}行情信息已存在，直接读取文件!')
        ticker_info_src = joblib.load(f'data/src/sina/{ticker}_{current_date}.pkl')
        print(ticker_info_src.shape)
        return ticker_info_src
    print(f'未检测到文件，正在重新获取【{ticker} {current_date}】的全部历史行情...')
    ticker_info = ak.stock_zh_a_daily(symbol=ticker)
    print(ticker_info.shape)
    # 将date字段转为index,并命名为Date
    ticker_info.index = pd.to_datetime(ticker_info['date'])
    ticker_info = ticker_info.rename(index={'date': 'Date'})
    ticker_info = ticker_info.drop(columns=['date'])
    # print(ticker_info.index)
    # 如果目录不存在则创建
    if not os.path.exists('data/src/sina/'):
        os.makedirs('data/src/sina/')
    # 保存文件
    print(f'获取完成{ticker_info.shape}')
    joblib.dump(ticker_info, f'data/src/sina/{ticker}_{current_date}.pkl')
    return ticker_info


def build_data(ticker, data, build_data_date, category='build'):
    build_col = [3, 5, 10, 15, 30, 60, 90, 120, 180, 240, 360, 480, 720]
    print(f'正在构建【{ticker} {build_data_date}】的数据集...')
    # 如果文件已存在，则直接跳过
    if category == 'build' and os.path.exists(f'data/build/{ticker}_{build_data_date}.pkl') and joblib.load(f'data/build/{ticker}_{build_data_date}.pkl') is not None:
        print('数据集已存在')
        return joblib.load(f'data/build/{ticker}_{build_data_date}.pkl')

    print('开始构建数据集')
    data_column = data.columns
    output_data = data.copy()

    new_columns = {}
    for i in build_col:
        # print(f'生成{i}天列')
        for col in data_column:
            new_columns[f'{col}_avg_{i}'] = data[col].rolling(i).mean()
            new_columns[f'{col}_max_{i}'] = data[col].rolling(i).max()
            new_columns[f'{col}_min_{i}'] = data[col].rolling(i).min()
            new_columns[f'{col}_std_{i}'] = data[col].rolling(i).std()
            new_columns[f'{col}_median_{i}'] = data[col].rolling(i).median()

    # 使用 pd.concat 一次性合并所有新列
    new_df = pd.DataFrame(new_columns)
    output_data = pd.concat([output_data, new_df], axis=1)

    # 增加日期对应的星期列
    output_data['trans_date'] = data.index.weekday
    # print('完成构建数据集')
    # 如果目录不存在则创建
    if not os.path.exists('data/build/'):
        os.makedirs('data/build/')

    if category == 'build':
        # 保存文件
        joblib.dump(output_data, f'data/{category}/{ticker}_{build_data_date}.pkl')
    return output_data


def get_last_workday(date):
    """获取指定日期的上一个工作日"""
    return date - pd.offsets.BDay(1)


def get_next_workday(date):
    """获取指定日期的下一个工作日"""
    return date + pd.offsets.BDay(1)



def check_google_connectivity():
    try:
        response = requests.get('https://www.google.com', timeout=5)
        if response.status_code == 200:
            print("网络可以连通谷歌网站")
            return True
        else:
            print(f"无法连通谷歌网站，状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"无法连通谷歌网站，错误信息: {e}")
        return False

check_google_connectivity()
