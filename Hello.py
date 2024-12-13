import streamlit as st
import os
import sys
import akshare as ak
import datetime
from ai_train import utils

# 设置页面配置
st.set_page_config(page_title="🏠项目主页",
                   layout="wide",
                   page_icon="📈",
                   initial_sidebar_state="expanded"
                   )
st.title("AI股票 A股预测平台")
st.header("🏠 项目主页")

st.sidebar.success("在上方选择一个演示。")
st.sidebar.subheader("🏠 项目主页")

# 设置默认模型算法
session_state = st.session_state
st.session_state.current_date = datetime.datetime.now()
st.session_state.model = 'LGBM'
st.session_state.path = os.path.dirname(os.path.abspath(sys.argv[0]))
st.session_state.google_connectivity = utils.check_google_connectivity()

# a股
st.session_state.stock_info_a_code_name_df = ak.stock_info_a_code_name()
# 上证
st.session_state.stock_info_sh_df = ak.stock_info_sh_name_code()  # choice of {"主板A股", "主板B股", "科创板"}
# 深证
st.session_state.stock_info_sz_df = ak.stock_info_sz_name_code()  # choice of {"A股列表", "B股列表", "AB股列表", "上市公司列表", "主板", "中小企业板", "创业板"}

# 平台功能介绍
st.markdown(
    """
    - 在当今复杂多变的金融市场中，股票投资既是机遇也是挑战。为了帮助投资者更精准地把握股票市场动态，我们精心打造了这个基于机器学习技术的股票预测网站。
    - 本网站整合了海量的历史股票数据，并运用先进的机器学习算法进行深度分析与模型训练，旨在为广大投资者提供可靠、实用的股票分析与预测服务。
    - 无论您是经验丰富的专业投资者，还是初涉股市的新手，我们的网站都将成为您投资决策过程中的得力助手，助力您在股票市场中发现潜在的投资机会，有效降低投资风险，实现财富的稳健增长。
    """
)

st.markdown(
    """<div style="background-color:#f5f5f5;padding:10px;">
                <p style="color:#999999;">
                    In today's complex and ever-changing financial markets, stock investment represents both opportunities and challenges. To assist investors in grasping the dynamics of the stock market more accurately, we have meticulously developed this stock prediction website based on machine learning technology.
                This website has integrated a vast amount of historical stock data and employs advanced machine learning algorithms for in-depth analysis and model training. It aims to provide reliable and practical stock analysis and prediction services for a wide range of investors. 
                Whether you are an experienced professional investor or a novice just entering the stock market, our website will become a powerful assistant in your investment decision-making process, helping you discover potential investment opportunities in the stock market, effectively reducing investment risks, and achieving steady growth of wealth.
                <br/>
        </div>
    """, unsafe_allow_html=True)

# 使用自定义 CSS 样式使图片自动缩放
st.markdown(
    """
    <style>
    .auto-resize-image img {
        max-width: 100%;
        height: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 插入图片
st.image('images/main2.png')
