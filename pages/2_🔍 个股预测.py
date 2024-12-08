import datetime
import streamlit as st
import pandas as pd
from ai_train import get_stock_data
from ai_train import ai_train
import plotly.express as px

st.set_page_config(page_title='🔍 个股预测', page_icon='📈', layout='wide')
st.header('🔍 个股预测')
st.sidebar.subheader("🔍 个股预测")

# 当前日期
current_date = st.session_state.current_date
stock_info_sh_df = st.session_state.stock_info_sh_df
stock_info_sz_df = st.session_state.stock_info_sz_df
flag = False
stock_info = None
col1, col2, col3, col4 = st.columns(4)

with col1:
    ticker = st.text_input('请输入你要预测的股票代码','600999')

# 如果还没输入代码，就直接显示所有股票代码
if ticker == '':
    st.write('你没有输入股票代码，请输入股票代码！')
else:
    ticker, stock_info = get_stock_data.get_ticker(ticker)
    if ticker is None:
        st.write('你输入的股票代码有误，请重新输入！')
        exit()

with col2:
    pred_date = st.date_input('选择预测日期')

with col3:
    kpi = st.selectbox('选择评价指标', ("mae", "mse", "mape", "rmse", 'All'))
with col4:
    re_train = st.selectbox('是否重新训练模型', ("否", "是"))

# 获取当前日期的下一个工作日，跳过星期六星期天
current_date_dt = pd.to_datetime(current_date)
next_work_day = current_date_dt + pd.offsets.BDay(1)
# 判断输入的日期是否是周末或大于下一个工作日
if pred_date.weekday() in [5, 6] or pd.to_datetime(pred_date) > next_work_day:
    st.write(f'你选择的日期是周末或大于下一个工作日({next_work_day.date()}), 暂不支持预测！')
    st.stop()
elif pd.to_datetime(pred_date) == next_work_day:
    flag = True

# pred_date对应的上一个工作日
last_work_day = pred_date - pd.offsets.BDay(1)

pred_date = pred_date.strftime("%Y-%m-%d")
last_work_day = last_work_day.strftime("%Y-%m-%d")
# st.write(f'你选择了预测日期：{pred_date}')


if re_train == '是':
    re_train_path = pred_date
else:
    re_train_path = 'saved'

st.dataframe(stock_info)

button = st.button('开始预测')

if button:

    i = 0
    progress_bar = st.progress(i)
    status_text = st.empty()

    # 获得个股数据
    status_text.text(f'正在获取{ticker}的全部历史行情信息...')
    ticker_history_src = get_stock_data.get_data(ticker)
    status_text.text(f'历史行情信息获取完毕，数据集大小为：{ticker_history_src.shape}')

    # 构建新的数据
    status_text.text('开始列扩充构建新数据集...')
    build_col = [3, 5, 10, 15, 30, 60, 90, 120, 180, 240, 360, 480, 720]
    build_data_src = get_stock_data.build_data(ticker, ticker_history_src, build_col)
    # st.dataframe(data)
    status_text.text(f'构建新数据集完毕，新数据集大小为：{build_data_src.shape}')
    # st.dataframe(build_data_src)

    build_data = build_data_src
    # ticker_history_src['trans_date'] = ticker_history_src.index.strftime("%Y-%m-%d")
    build_data['trans_date'] = build_data.index.weekday

    # 将data中的列名全部改为以source开头，空格替换为下划线，全部设置小写字母
    ticker_history_src.columns = ['target_' + col.replace(' ', '_').lower() for col in ticker_history_src.columns]
    build_data.columns = ['source_' + col.replace(' ', '_').lower() for col in build_data.columns]
    # stock_info与data错位一天拼接
    build_data = build_data.shift(1)
    target_data = ticker_history_src

    result = pd.concat([target_data, build_data], axis=1)
    # st.dataframe(result)
    status_text.text(f'新数据集拼接完毕，新数据集大小为：{result.shape}')
    result = result.dropna().drop_duplicates()
    # st.dataframe(result)
    status_text.text(f'新数据集清洗完毕，新数据集大小为：{result.shape}')

    source_col = build_data.columns.tolist()
    # 预测日期前一天的数据
    if pd.to_datetime(pred_date) == next_work_day:
        pred_date_row = build_data_src[build_data_src.index.strftime("%Y-%m-%d") == last_work_day]
        # st.dataframe(pred_date_row)
    else:
        pred_date_row = build_data[build_data.index.strftime("%Y-%m-%d") == pred_date]

    target_data_row = target_data[target_data.index.strftime("%Y-%m-%d") == pred_date]
    # st.dataframe(target_data_row)
    # st.dataframe(result_date_row)

    status_text.text(f'开始预测{ticker} {pred_date} 数据，请耐心等待...')
    start_time = datetime.datetime.now()
    # 实例化模型
    client = ai_train.mlClient()
    models = client.models.keys()

    col_models = {}
    col_pred = {}
    kpis = {}
    # 循环预测
    print(target_data.columns.tolist())

    for target_col in target_data.columns.tolist():
        # if target_col != 'target_volume':
        #     continue
        status_text.text(f'开始训练{target_col}最优模型...')
        df_model_compare = client.train(ticker, result, source_col, target_col, pred_date, re_train_path, models)
        # st.dataframe(df_model_compare)
        if kpi == 'All':
            # 获取4列评估的值进行平均
            kpi_value = df_model_compare.iloc[:, 3:7].mean(axis=1)
            # 找到最大值所在的行索引
            min_index = kpi_value.idxmin()
            kpi_value = kpi_value.loc[min_index]
            # print(min_index)
        else:
            min_index = df_model_compare[kpi].idxmin()
            kpi_value = df_model_compare.loc[min_index][kpi]
        best_model = df_model_compare.loc[min_index]['model']
        col_models[target_col] = best_model
        status_text.text(f'开始预测{target_col}的数据值...')
        y_pred = client.predict(ticker, pred_date_row, target_col, re_train_path, best_model)
        col_pred[target_col] = y_pred
        kpis[target_col] = kpi_value
        i += 20
        progress_bar.progress(i)

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    status_text.text(f'预测完毕，总耗时{duration}秒')

    # 黑体标题
    st.markdown('<h3 style="color:black;">预测结果：</h3>', unsafe_allow_html=True)
    col_model = pd.DataFrame(col_models, index=['最优模型']).T
    col_pred = pd.DataFrame(col_pred, index=['预测值']).T
    kpis = pd.DataFrame(kpis, index=[kpi]).T

    if flag:
        df = pd.concat([col_model, col_pred, kpis], axis=1)
        # 预测结果比对
        st.dataframe(df)
    else:
        col_true = pd.DataFrame(target_data_row.T)
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
    st.markdown('<h3 style="color:black;">历史记录参考：</h3>', unsafe_allow_html=True)
    st.dataframe(ticker_history_src)