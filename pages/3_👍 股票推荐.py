import datetime
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from ai_train import get_stock_data

st.set_page_config(page_title='👍 股票推荐', page_icon='📈', layout='wide')
st.header('👍 股票推荐')
st.sidebar.subheader("👍 股票推荐")