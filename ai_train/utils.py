import akshare as ak
import joblib
import streamlit as st
import yfinance as yf
import os
import pandas as pd

stock_info_sh_df = st.session_state.stock_info_sh_df
stock_info_sz_df = st.session_state.stock_info_sz_df


def get_ticker(ticker):
    stock_info = None
    if ticker in stock_info_sh_df['证券代码'].to_list():
        stock_info = stock_info_sh_df[stock_info_sh_df['证券代码'] == ticker]
        print(stock_info)
        stock_info = stock_info.reset_index(drop=True)
        ticker = ticker + '.SS'
    elif ticker in stock_info_sz_df['A股代码'].to_list():
        stock_info = stock_info_sz_df[stock_info_sz_df['A股代码'] == ticker]
        print(stock_info)
        stock_info = stock_info.reset_index(drop=True)
        ticker = ticker + '.SZ'
    else:
        ticker = None
    return ticker, stock_info


def get_data(ticker, period='max', interval='1d'):
    # 如果文件已存在，则直接跳过
    if os.path.exists(f'data/src/{ticker}_ticker_info_src.pkl') and joblib.load(f'data/src/{ticker}_ticker_info_src.pkl') is not None:
        return joblib.load(f'data/src/{ticker}_ticker_info_src.pkl')
    # 获得个股数据
    print(f'正在获取【{ticker}】的全部历史行情信息...')
    ticker_info = yf.Ticker(ticker)
    ticker_info_src = ticker_info.history(period=period, interval=interval)
    ticker_info_src = ticker_info_src.drop(columns=['Dividends', 'Stock Splits'])
    # 如果目录不存在则创建
    if not os.path.exists('data/src/'):
        os.makedirs('data/src/')
    # 保存文件
    joblib.dump(ticker_info_src, f'data/src/{ticker}_ticker_info_src.pkl')
    return ticker_info_src


def build_data(ticker, data, category='build'):
    build_col = [3, 5, 10, 15, 30, 60, 90, 120, 180, 240, 360, 480, 720]
    # 如果文件已存在，则直接跳过
    if os.path.exists(f'data/{category}/{ticker}_ticker_info_build.pkl') and joblib.load(f'data/{category}/{ticker}_ticker_info_build.pkl') is not None:
        print('数据集已存在')
        return joblib.load(f'data/build/{ticker}_ticker_info_build.pkl')
    # for i in (3, 5, 10, 15, 30, 60, 90, 120, 180, 240, 360, 480, 720):
    print('开始构建数据集')
    data_column = data.columns
    for i in build_col:
        print(f'生成{i}天列')
        for col in data_column:
            # print(f'生成{i}天列{col}平均数据...')
            data[f'{col}_avg_{i}'] = data[col].rolling(i).mean()
            # print(f'生成{i}天列{col}最大数据...')
            data[f'{col}_max_{i}'] = data[col].rolling(i).max()
            # print(f'生成{i}天列{col}最小数据...')
            data[f'{col}_min_{i}'] = data[col].rolling(i).min()
            # print(f'生成{i}天列{col}方差数据...')
            data[f'{col}_std_{i}'] = data[col].rolling(i).std()
            # print(f'生成{i}天列{col}中位数数据...')
            data[f'{col}_median_{i}'] = data[col].rolling(i).median()
    # 增加日期对应的星期列
    data['trans_date'] = data.index.weekday
    print('完成构建数据集')
    # 如果目录不存在则创建
    if not os.path.exists('data/build/'):
        os.makedirs('data/build/')
    # 保存文件
    joblib.dump(data, f'data/{category}/{ticker}_ticker_info_build.pkl')
    return data


def get_last_workday(date):
    """获取指定日期的上一个工作日"""
    return date - pd.offsets.BDay(1)


def get_next_workday(date):
    """获取指定日期的下一个工作日"""
    return date + pd.offsets.BDay(1)