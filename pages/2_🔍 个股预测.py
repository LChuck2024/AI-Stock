import datetime
import streamlit as st
import pandas as pd
from ai_train import utils
from ai_train import ai_train
import plotly.express as px
from datetime import timedelta

st.set_page_config(page_title='🔍 个股预测', page_icon='📈', layout='wide')
st.header('🔍 个股预测')
st.sidebar.subheader("🔍 个股预测")

# 当前日期
current_date = st.session_state.current_date
stock_info_sh_df = st.session_state.stock_info_sh_df
stock_info_sz_df = st.session_state.stock_info_sz_df
future_flag = False
stock_info = None
col1, col2, col3, col4 = st.columns(4)

# 获取当前日期的下一个工作日，跳过星期六星期天
current_date_dt = pd.to_datetime(current_date)
next_work_day = utils.get_next_workday(current_date_dt)

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

# 获得个股数据
ticker_history = utils.get_data(ticker)
# st.dataframe(ticker_history_src)
# 个股行情最大日期
ticker_max_date = (ticker_history.index[-1]).strftime("%Y-%m-%d")
# 个股行情最小日期
ticker_min_date = (ticker_history.index[0]).strftime("%Y-%m-%d")

st.write(f'当前获取到的行情日期:{ticker_min_date}至{ticker_max_date}')
# 判断输入的日期是否是周末或预测未来日期
if pred_date.weekday() in [5, 6]:
    st.write(f'你选择的日期是周末，请重新选择！')
    st.stop()
elif pd.to_datetime(pred_date) > pd.to_datetime(ticker_max_date):
    future_flag = True

# pred_date对应的上一个工作日
last_work_day = utils.get_last_workday(pred_date).strftime("%Y-%m-%d")

pred_date = pred_date.strftime("%Y-%m-%d")
# st.write(f'你选择了预测日期：{pred_date}')

if re_train == '是':
    re_train_path = pred_date
else:
    re_train_path = 'saved'

# 展示股票基础信息
st.dataframe(stock_info)

button = st.button('开始预测')

if button:

    i = 0
    progress_bar = st.progress(i)
    status_text = st.empty()
    start_time = datetime.datetime.now()
    status_text.text(f'开始预测{ticker} {pred_date} 数据，请耐心等待...')

    # 构建新的数据
    status_text.text('开始列扩充构建新数据集...')
    build_history = utils.build_data(ticker, ticker_history, ticker_max_date)
    # st.dataframe(build_history)
    status_text.text(f'构建新数据集完毕，新数据集大小为：{build_history.shape}')

    # 重命名字段名称，空格替换为下划线，全部设置小写字母
    ticker_history.columns = ['target_' + col.replace(' ', '_').lower() for col in ticker_history.columns]
    build_history.columns = ['source_' + col.replace(' ', '_').lower() for col in build_history.columns]
    ticker_history_cols = ticker_history.columns.tolist()
    # 构建数据集
    X_data = build_history.shift(1)
    y_data = ticker_history[ticker_history.index.strftime("%Y-%m-%d") != ticker_min_date]
    train_data = pd.concat([y_data,X_data], axis=1)
    # st.dataframe(train_data)
    # 数据集清洗
    train_data = train_data.dropna().drop_duplicates()
    X = train_data[X_data.columns.tolist()]
    # 实例化模型
    client = ai_train.mlClient()
    models = client.models.keys()
    col_models = {}
    kpis = {}

    # 训练阶段
    # 按列循环训练模型，获得每列的最优模型及评估指标
    for target_col in ticker_history_cols:
        y = pd.DataFrame(train_data[target_col])
        # st.write(pd.DataFrame(ticker_history[target_col]).columns[0])
        status_text.text(f'开始训练{target_col}最优模型...')
        df_model_compare = client.train(ticker, X, y, pred_date, re_train_path, models)
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
        # 各列的的最优模型
        col_models[target_col] = best_model
        # 最优模型对应的评估指标
        kpis[target_col] = kpi_value
        i += 10
        progress_bar.progress(i)
        # st.write(i)
    # st.dataframe(col_models)

    # 预测阶段
    col_pred = {}
    final_pred = None
    if future_flag:
        # 构建未来日期的数据
        # 重新获取当前日期数据
        ticker_history_new = ticker_history
        # st.dataframe(ticker_history_new)
        # 循环取 ticker_max_date 和 pred_date 之间的日期
        # pred_date = pd.to_datetime(pred_date)

        # 循环预测开始日期
        current_pred_date = pd.to_datetime(ticker_max_date) + timedelta(days=1)
        # 获取需要循环的次数
        loop_times = ((pd.to_datetime(pred_date) - current_pred_date).days + 1) * len(ticker_history_cols)
        rate = (100-i)/loop_times
        # st.write(f'loop_times:{loop_times} {rate}')
        while current_pred_date <= pd.to_datetime(pred_date):
            status_text.text(f'开始预测{ticker} {current_pred_date.strftime("%Y-%m-%d")} 数据，请耐心等待...')
            build_data_date = utils.get_last_workday(current_pred_date).strftime("%Y-%m-%d")
            ticker_history_new.columns = [col.replace('target_', '').lower() for col in ticker_history_new.columns]
            build_history_new = utils.build_data(ticker, ticker_history_new, build_data_date, category='future')
            status_text.text('开始列扩充构建新数据集...')
            pred_date_row = (build_history_new[build_history_new.index.strftime("%Y-%m-%d") == build_data_date])
            pred_date_row.columns = ['source_' + col for col in pred_date_row.columns]
            print(pred_date_row.columns)
            # st.write('预测源数据行...')
            # st.dataframe(pred_date_row)
            # 按列循环用每列的最优模型进行预测,获得各列预测值
            for target_col in ticker_history_cols:
                model = col_models.get(target_col)
                status_text.text(f'开始使用模型{model}预测{target_col}的数据值...')
                y_pred = client.predict(ticker, pred_date_row, target_col, col_models.get(target_col))
                col_pred[target_col] = y_pred
                # st.write(round(i))
                progress_bar.progress(round(i))
                i += rate

            # 将 pred_date 转换为带有时区信息的 Timestamp 对象
            pred_date_tz = pd.Timestamp(current_pred_date).tz_localize('Asia/Shanghai')
            # 创建 total_pred DataFrame 并设置索引
            total_pred = pd.DataFrame(col_pred, index=[pred_date_tz]).T
            total_pred.index.name = 'Date'

            final_pred = total_pred.T
            st.write(f'{current_pred_date.strftime("%Y-%m-%d")} 预测结果...')
            st.dataframe(final_pred)
            # 拼接未来日期的数据
            ticker_history_new.columns = ['target_' + col.replace(' ', '_').lower() for col in ticker_history_new.columns]
            ticker_history_new = pd.concat([ticker_history_new, final_pred],axis=0)
            # st.write('拼接未来日期的数据...')
            # st.dataframe(ticker_history_new)
            current_pred_date += timedelta(days=1)
    else:
        # st.write('预测源数据行...')
        pred_date_row = (build_history[build_history.index.strftime("%Y-%m-%d") == pred_date])
        # st.dataframe(pred_date_row)
        # 按列循环用每列的最优模型进行预测,获得各列预测值
        for target_col in ticker_history_cols:
            model = col_models.get(target_col)
            status_text.text(f'开始使用模型{model}预测{target_col}的数据值...')
            y_pred = client.predict(ticker, pred_date_row, target_col, col_models.get(target_col))
            col_pred[target_col] = y_pred
            # st.write(round(i))
            progress_bar.progress(round(i))
            i += 10
        # 将 pred_date 转换为带有时区信息的 Timestamp 对象
        pred_date_tz = pd.Timestamp(pred_date).tz_localize('Asia/Shanghai')
        # 创建 total_pred DataFrame 并设置索引
        total_pred = pd.DataFrame(col_pred, index=[pred_date_tz]).T
        total_pred.index.name = 'Date'

        final_pred = total_pred.T
        st.write(f'{pred_date} 预测结果...')
        st.dataframe(final_pred)
        # 拼接未来日期的数据
        # ticker_history_new.columns = ['target_' + col.replace(' ', '_').lower() for col in ticker_history_new.columns]
        ticker_history_new = pd.concat([ticker_history, final_pred], axis=0)

    # st.write(i)
    progress_bar.progress(100)
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    status_text.text(f'预测完毕，总耗时{duration}秒')

    # 黑体标题
    st.markdown(f'<h3 style="color:black;">{ticker} {pred_date} 预测结果：</h3>', unsafe_allow_html=True)
    col_model = pd.DataFrame(col_models, index=['最优模型']).T
    col_pred = pd.DataFrame(col_pred, index=['预测值']).T
    kpis = pd.DataFrame(kpis, index=[kpi]).T

    if future_flag:
        df = pd.concat([col_model, col_pred, kpis], axis=1)
        # 预测结果比对
        st.dataframe(df)
    else:
        target_data_row = ticker_history[ticker_history.index.strftime("%Y-%m-%d") == pred_date]
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
    st.markdown('<h3 style="color:black;">合并后记录参考：</h3>', unsafe_allow_html=True)
    # 合并final_pred到ticker_history_src
    ticker_history_src = pd.concat([ticker_history, final_pred], axis=0)
    st.dataframe(ticker_history_src)
