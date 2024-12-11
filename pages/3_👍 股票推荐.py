import datetime
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from ai_train import utils

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

pred_date = st.date_input('选择日期')
last_work_day = utils.get_last_workday(pred_date).strftime("%Y-%m-%d")
st.write(last_work_day)
