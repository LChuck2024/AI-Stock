import datetime
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from ai_train import get_stock_data

st.set_page_config(page_title='📈 个股行情', page_icon='📈', layout='wide')
st.header('🔍 个股预测')
st.sidebar.subheader("🔍 个股预测")

# 当前日期
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
stock_info_sh_df = st.session_state.stock_info_sh_df
stock_info_sz_df = st.session_state.stock_info_sz_df

period_dict = {'1天': '1d',
               '5天': '5d',
               '1个月': '1mo',
               '3个月': '3mo',
               '6个月': '6mo',
               '1年': '1y',
               '2年': '2y',
               '5年': '5y',
               '10年': '10y',
               '年初至今': 'ytd',
               '最大': 'max'
               }


def get_start_date(period):
    today = datetime.datetime.now()
    if period == '1d':
        return (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif period == '5d':
        return (today - datetime.timedelta(days=5)).strftime("%Y-%m-%d")
    elif period == '1mo':
        return (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    elif period == '3mo':
        return (today - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
    elif period == '6mo':
        return (today - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
    elif period == '1y':
        return (today - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    elif period == '2y':
        return (today - datetime.timedelta(days=730)).strftime("%Y-%m-%d")
    elif period == '5y':
        return (today - datetime.timedelta(days=1825)).strftime("%Y-%m-%d")
    elif period == '10y':
        return (today - datetime.timedelta(days=3650)).strftime("%Y-%m-%d")
    elif period == 'ytd':
        return datetime.datetime(today.year, 1, 1).strftime("%Y-%m-%d")
    elif period == 'max':
        return '最早日期'
    else:
        raise ValueError(f"未知的周期: {period}")


ticker = st.text_input('请输入你要查询的股票代码')

# 如果还没输入代码，就直接显示所有股票代码
if ticker == '':
    st.write('你没有输入股票代码，请输入股票代码！')
    exit()
else:
    ticker, stock_info = get_stock_data.get_ticker(ticker)
    if ticker is None:
        st.write('你输入的股票代码有误，请重新输入！')
        exit()

# 展示股票信息
st.dataframe(stock_info)

# 设置按钮让用户选择按开始结束时间查或者直接选择范围
select_date_range = st.radio('选择查询日期范围', ('选择开始-结束日期', '直接选择范围'))
if select_date_range == '选择开始-结束日期':
    # 设置两列并排
    col1, col2 = st.columns(2)
    # 选择日期
    with col1:
        start = st.date_input('选择开始日期')
    with col2:
        end = st.date_input('选择结束日期')
    if start > end:
        st.write('开始日期不能大于结束日期')
        exit()
else:
    input_date = st.selectbox('选择日期范围', period_dict.keys())
    select_period = period_dict.get(input_date)
    # input_date转换为开始结束日期
    start = get_start_date(select_period)
    end = current_date

st.write(f'你选择的日期范围是{start}至{end}')

interval_list = {'1d': '日K', '1wk': '周K', '1mo': '月K', '5m': '5分钟', '15m': '15分钟', '30m': '30分钟', '60m': '60分钟'}

button = st.button('查询', key='button')

ticker_info_historical = {}

if button:

    i = 0
    progress_bar = st.progress(i)
    status_text = st.empty()

    # 查询股票代码
    status_text.text(f'正在查询{ticker}的行情信息...')
    ticker_info = yf.Ticker(ticker)
    if select_date_range == '选择开始-结束日期':
        for interval in interval_list.keys():
            # st.write(f'开始加载{interval_list.get(interval)}数据...')
            ticker_history_src = ticker_info.history(start=start, end=end, interval=interval)
            if ticker_history_src.size > 0:
                status_text.text(f'{interval_list.get(interval)}数据加载完成！共{ticker_history_src.size}行数据！')
            else:
                st.write(f'注意：{interval_list.get(interval)}数据加载失败！')
                continue
            if interval in ['5m', '15m', '30m', '60m']:
                ticker_history_src['Time'] = ticker_history_src.index.strftime("%Y-%m-%d %H:%M:%S")
            else:
                ticker_history_src['Time'] = ticker_history_src.index.strftime("%Y-%m-%d")
            ticker_info_historical[f'range_{interval}'] = ticker_history_src
            i += 10
            progress_bar.progress(i)
    else:
        for interval in interval_list.keys():
            # st.write(f'开始加载{interval_list.get(interval)}数据...')
            ticker_history_src = ticker_info.history(period=select_period, interval=interval)
            if ticker_history_src.size > 0:
                status_text.text(f'{interval_list.get(interval)}数据加载完成！共{ticker_history_src.size}行数据！')
            else:
                st.write(f'{interval_list.get(interval)}数据加载失败！')
                continue
            if interval in ['5m', '15m', '30m', '60m']:
                ticker_history_src['Time'] = ticker_history_src.index.strftime("%Y-%m-%d %H:%M:%S")
            else:
                ticker_history_src['Time'] = ticker_history_src.index.strftime("%Y-%m-%d")
            ticker_info_historical[f'range_{interval}'] = ticker_history_src
            i += 10
            progress_bar.progress(i)

    # 展示数据
    # col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    # for i, interval in zip(range(7), interval_list.keys()):
    #     with eval(f'col{i + 1}'):
    #         st.write(f'{interval_list.get(interval)}数据')
    #         st.dataframe(ticker_info_historical.get(f'range_{interval}'))

    # 绘制K线条
    status_text.text('正在绘制K线图...')
    # 横向选项卡选择
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(['日K', '周K', '月K', '5分钟', '15分钟', '30分钟', '60分钟'])
    # 使用字典存储 fig 对象
    figs = {}
    # 将 dict_keys 转换为列表
    intervals = list(interval_list.keys())

    for i, k in enumerate(intervals):
        with eval(f'tab{i + 1}'):
            try:
                # 创建一个新的 fig 对象
                fig = go.Figure(data=[go.Candlestick(x=ticker_info_historical[f'range_{k}'].index,
                                                     open=ticker_info_historical[f'range_{k}']['Open'],
                                                     high=ticker_info_historical[f'range_{k}']['High'],
                                                     low=ticker_info_historical[f'range_{k}']['Low'],
                                                     close=ticker_info_historical[f'range_{k}']['Close'])])
                fig.update_layout(title=f'{ticker}的K线图 ({interval_list[k]})', yaxis_title='价格', xaxis_rangeslider_visible=False)

                # 将 fig 对象存储在字典中
                figs[f'fig_{k}'] = fig

                # 在 Streamlit 中显示 fig
                st.plotly_chart(fig)
                # 绘制Volume的条形图
                fig2 = go.Figure(data=[go.Bar(x=ticker_info_historical[f'range_{k}'].index, y=ticker_info_historical[f'range_{k}']['Volume'])])
                fg2 = fig2.update_layout(title=f'{ticker}的成交量 ({interval_list[k]})', yaxis_title='成交量')
                st.plotly_chart(fig2)
            except:
                st.write(f'{interval_list.get(k)}数据绘制失败！')
                continue
    progress_bar.progress(100)
    status_text.text('查询成功！')
# # 用open和close绘制一张条形图
# st.bar_chart(ticker_info_historical[['Open', 'Close']])
