import datetime
import streamlit as st
import pandas as pd
from ai_train import utils
import plotly.express as px
import plotly.graph_objects as go
from ai_train import stock_process

st.set_page_config(page_title='🔍 个股预测', page_icon='📈', layout='wide', initial_sidebar_state="expanded")
st.header('🔍 个股预测')
st.sidebar.subheader("🔍 个股预测")

st.markdown(
    """<div style="background-color:#f5f5f5;padding:10px;">
                <p style="color:#999999;">
                “个股预测” 页面，依托机器学习的强大力量，解锁股票未来密码。综合多年历史价格、成交量、宏观经济与行业趋势等多元数据，模型经深度训练与优化，精准预测个股未来特定日期的开盘、收盘、最高及最低价格区间。虽市场无常，但此预测可为您提前布局投资策略提供科学参考，指引您在股价涨跌间抢占先机。
        </div>
    """, unsafe_allow_html=True)

# 设置红色字体提醒
st.markdown(
    """<div padding:10px;">
                <p style="color:#ff0000;">
                * 需知，股票市场波谲云诡，本网站预测与推荐仅供参考。<br/>
                * 投资决策时，请综合考量自身风险偏好与投资目标，审慎抉择，方能在股市风云中从容驾驭，驶向财富彼岸。
        </div>
    """, unsafe_allow_html=True)

# 当前日期
current_date = st.session_state.current_date
stock_info_sh_df = st.session_state.stock_info_sh_df
stock_info_sz_df = st.session_state.stock_info_sz_df
stock_info = None
col1, col2, col3, col4 = st.columns(4)

with col1:
    ticker = st.text_input('请输入你要预测的股票代码', '600999')
# 如果还没输入代码，就直接显示所有股票代码
if ticker == '':
    st.write('你没有输入股票代码，请输入股票代码！')
else:
    ticker, stock_info = utils.get_ticker(ticker)
    if ticker is None:
        st.write('你输入的股票代码有误，请重新输入！')
        exit()

with col2:
    pred_date = st.date_input('选择预测日期')

with col3:
    kpi = st.selectbox('选择评价指标', ("mae", "mse", "mape", "rmse", 'All'))
with col4:
    re_train = st.selectbox('是否重新训练模型', ("否", "是"))

if re_train == '是':
    re_train_path = pred_date
else:
    re_train_path = 'saved'

button = st.button('开始预测')

pred_date_str = pred_date.strftime("%Y-%m-%d")
st.write(f'您选择的预测日期是:{pred_date_str}')
ssp = stock_process.single_stock_prediction(ticker, pred_date_str, re_train_path, kpi)
# try:
#     ssp = stock_process.single_stock_prediction(ticker, pred_date_str, re_train_path, kpi)
# except Exception as e:
#     st.write(f'预测中出现问题，请联系管理员！{e}')
#     exit()

future_flag = True if pd.to_datetime(pred_date) > pd.to_datetime(ssp.ticker_max_date) else False

st.write(f'当前获取到的行情日期:{ssp.ticker_min_date}至{ssp.ticker_max_date}')

# 判断输入的日期是否是周末或预测未来日期
if pred_date.weekday() in [5, 6]:
    st.write('你选择的日期是周末，请重新选择！')

# 展示股票基础信息
st.dataframe(stock_info)

if button:

    i = 0
    progress_bar = st.progress(i)
    status_text = st.empty()
    start_time = datetime.datetime.now()
    status_text.text(f'开始预测{ticker} {pred_date_str} 数据，请耐心等待...')

    # 训练模型
    [col_models, kpis] = ssp.single_train()
    progress_bar.progress(50)
    # 预测数据
    [final_pred, col_pred, ticker_history_new] = ssp.single_pred()
    # st.dataframe(final_pred)

    progress_bar.progress(100)
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    status_text.text(f'预测完毕，总耗时{duration}秒')

    # 黑体标题
    st.markdown(f'<h3 style="color:black;">{ticker} {pred_date_str} 预测结果：</h3>', unsafe_allow_html=True)
    col_model = pd.DataFrame(col_models, index=['最优模型']).T
    col_pred = pd.DataFrame(col_pred, index=['预测值']).T
    kpis = pd.DataFrame(kpis, index=[kpi]).T

    if future_flag:
        df = pd.concat([col_model, col_pred, kpis], axis=1)
        # 预测结果比对
        st.dataframe(df)
    else:
        # st.dataframe(ssp.ticker_history)
        target_data_row = ssp.ticker_history[ssp.ticker_history.index.strftime("%Y-%m-%d") == pred_date_str]
        col_true = pd.DataFrame(target_data_row.T)
        # st.dataframe(col_true)
        # # 修改col_true的列名为真实值
        col_true.columns = ['真实值']
        # st.dataframe(kpis)
        df = pd.concat([col_model, col_true, col_pred, kpis], axis=1)
        # 预测结果比对
        st.dataframe(df)

        # 绘制价格预测偏差
        df = df.drop('target_volume', axis=0)
        fig = px.line(df, x=df.index, y=['真实值', '预测值'], title=f'{ticker} {pred_date} {kpi}评估指标预测结果')
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        # st.markdown(f'{ticker} {pred_date} {kpi}值预测结果')
        st.write(fig)
        # st.plotly_chart(fig)

    st.markdown('---')
    st.markdown('<h3 style="color:black;">预测记录：</h3>', unsafe_allow_html=True)
    st.dataframe(final_pred)

    ticker_history_future = ticker_history_new[ticker_history_new.index.strftime("%Y-%m-%d") >= ssp.ticker_max_date]
    # st.dataframe(ticker_history_future)
    # 创建一个新的 fig 对象
    fig = go.Figure(data=[go.Candlestick(x=ticker_history_future.index,
                                         open=ticker_history_future['target_open'],
                                         high=ticker_history_future['target_high'],
                                         low=ticker_history_future['target_low'],
                                         close=ticker_history_future['target_close'])])
    fig.update_layout(title=f'{ticker}的未来预测走势图', yaxis_title='价格', xaxis_rangeslider_visible=False)

    # 在第一个和第二个蜡烛中添加一条竖线
    fig.add_vline(x=ticker_history_future.index[0], line_width=1, line_dash="dash", line_color="black")

    # 在 Streamlit 中显示 fig
    st.plotly_chart(fig)
    # 绘制Volume的条形图
    fig2 = go.Figure(data=[go.Bar(x=ticker_history_future.index, y=ticker_history_future['target_volume'])])
    fg2 = fig2.update_layout(title=f'{ticker}的未来预测成交量', yaxis_title='成交量')
    # 在第一个中添加一条竖线
    fig2.add_vline(x=ticker_history_future.index[0], line_width=1, line_dash="dash", line_color="black")
    # 在 Streamlit 中显示 fig
    st.plotly_chart(fig2)

