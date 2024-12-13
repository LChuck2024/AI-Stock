import datetime
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from ai_train import utils
from ai_train import stock_process

st.set_page_config(page_title='👍 股票推荐', page_icon='📈', layout='wide', initial_sidebar_state="expanded")
st.header('👍 股票推荐')
st.sidebar.subheader("👍 股票推荐")

st.markdown(
    """<div style="background-color:#f5f5f5;padding:10px;">
                <p style="color:#999999;">
                “股票推荐” 页面，以智能算法为镜，映照股票走势周期之美。依短期活跃度、中期成长潜力、长期价值优势，为您筛选适配不同投资周期的个股。无论您偏好快进快出的短线博弈，还是志在长远的价值投资，皆能在此获取专属推荐，拓宽投资视野，发掘更多财富机遇。
                需知，股票市场波谲云诡，本网站预测与推荐仅供参考。投资决策时，请综合考量自身风险偏好与投资目标，审慎抉择，方能在股市风云中从容驾驭，驶向财富彼岸。
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

# a股
# stock_info_a_code = st.session_state.stock_info_a_code_name_df
# 上证
stock_info_sh = st.session_state.stock_info_sh_df  # choice of {"主板A股", "主板B股", "科创板"}
# 深证
stock_info_sz = st.session_state.stock_info_sz_df  # choice of {"A股列表", "B股列表", "AB股列表", "上市公司列表", "主板", "中小企业板", "创业板"}

col1, col2, col3, col4 = st.columns(4)
with col1:
    channel_input = st.selectbox('选择股票市场', ("上证", "深证"))
with col2:
    if channel_input == '上证':
        division_list = ["主板A股", "主板B股", "科创板"]
        index_name = '证券代码'
    else:
        division_list = ["A股列表", "B股列表", "AB股列表"]
    division_input = st.selectbox('选择股票市场', division_list)
    index_name = 'B股代码' if division_input == 'B股列表' else 'A股代码'

with col3:
    pred_date_input = st.date_input('选择出售日期')
with col4:
    kpi_input = st.selectbox('选择评价指标', ("mae", "mse", "mape", "rmse", 'All'))

pred_date_str = pred_date_input.strftime("%Y-%m-%d")
st.write(f'您选择的出售日期是:{pred_date_str}')

# 判断输入的日期是否是周末或预测未来日期
if pred_date_input.weekday() in [5, 6]:
    st.write('你选择的日期是周末，请重新选择！')

button = st.button('开始推荐')
if button:
    stock_infos = utils.get_all_tickers(channel_input, division_input)
    # ticker_list = stock_infos[index_name].tolist()
    # ticker_list = ['600999', '600998', '600997', '600996']
    # st.write(stock_infos.iterrows())
    ticker_pred_dict = {}  # {'600999': {'2024-12-14':['','','',''] ,'2024-12-15':['','','',''] }
    for stock_info in stock_infos.head(3).iterrows():
        # 获取股票代码
        ticker_code, ticker_name = stock_info[1]['证券代码'], stock_info[1]['证券简称']
        st.write(ticker_code, ticker_name)
        # 转换为股票代码
        ticker, stock_info = utils.get_ticker(ticker_code, source='sina')
        st.write(ticker)
        st.dataframe(stock_info)

        # # 实例化单个股票预测类
        # ssp = stock_process.single_stock_prediction(ticker, pred_date_str, 'saved', kpi_input)
        # # 训练模型
        # [col_models, kpis] = ssp.single_train()
        # # 预测数据
        # [final_pred, col_pred, ticker_history_new] = ssp.single_pred()
        # # 存储预测结果
        # ticker_pred_dict[ticker] = {pred_date_str: final_pred}
        #
        # ticker_history_future = ticker_history_new #[ticker_history_new.index.strftime("%Y-%m-%d") >= ssp.ticker_max_date]
        # # 绘制图表
        # fig = go.Figure(data=[go.Candlestick(x=ticker_history_future.index,
        #                                      open=ticker_history_future['target_open'],
        #                                      high=ticker_history_future['target_high'],
        #                                      low=ticker_history_future['target_low'],
        #                                      close=ticker_history_future['target_close'])])
        # fig.update_layout(title=f'{ticker} 股票价格走势', xaxis_title='日期', yaxis_title='价格')
        #
        # # 显示当前预测结果和图表
        # st.dataframe(final_pred)
        # st.plotly_chart(fig)
