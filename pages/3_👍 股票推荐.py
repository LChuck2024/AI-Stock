import datetime
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from ai_train import utils

st.set_page_config(page_title='👍 股票推荐', page_icon='📈', layout='wide')
st.header('👍 股票推荐')
st.sidebar.subheader("👍 股票推荐")


pred_date = st.date_input('选择日期')
last_work_day = utils.get_last_workday(pred_date).strftime("%Y-%m-%d")
st.write(last_work_day)