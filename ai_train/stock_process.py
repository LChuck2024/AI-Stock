

def one_day_pred():

    source_col = build_data.columns.tolist()
    col_models = {}
    col_pred = {}
    kpis = {}
    # 循环预测
    print(target_data.columns.tolist())

    # def predict_all(target_data, target_col, pred_date_row, col_models):
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

    # 将 pred_date 转换为带有时区信息的 Timestamp 对象
    pred_date_tz = pd.Timestamp(pred_date).tz_localize('Asia/Shanghai')