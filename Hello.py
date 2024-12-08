import streamlit as st
import os
import sys
import akshare as ak
import datetime

# st.session_state.clear()

# 设置默认模型算法
session_state = st.session_state
st.session_state.current_date = datetime.datetime.now().strftime("%Y-%m-%d")
st.session_state.model = 'LGBM'
st.session_state.path = os.path.dirname(os.path.abspath(sys.argv[0]))

# a股
st.session_state.stock_info_a_code_name_df = ak.stock_info_a_code_name()
# 上证
st.session_state.stock_info_sh_df = ak.stock_info_sh_name_code() # choice of {"主板A股", "主板B股", "科创板"}
# 深证
st.session_state.stock_info_sz_df = ak.stock_info_sz_name_code() # choice of {"A股列表", "B股列表", "AB股列表", "上市公司列表", "主板", "中小企业板", "创业板"}

st.write('欢迎使用')