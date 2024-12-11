import pandas as pd
from ai_train import utils
from ai_train import ai_train
from datetime import timedelta


class single_stock_prediction:
    def __init__(self, ticker, pred_date, re_train_path, kpi):
        # 股票代码
        self.ticker = ticker
        # 预测日期
        self.pred_date = pred_date
        # 重算模型标签
        self.re_train_path = re_train_path
        # 评估指标
        self.kpi = kpi
        # 获得个股数据
        self.ticker_history = utils.get_data(ticker)
        # print(self.ticker_history)
        # 个股行情最大日期
        self.ticker_max_date = (self.ticker_history.index[-1]).strftime("%Y-%m-%d")
        # 个股行情最小日期
        self.ticker_min_date = (self.ticker_history.index[0]).strftime("%Y-%m-%d")
        # 预测日期标签
        self.future_flag = True if pd.to_datetime(pred_date) > pd.to_datetime(self.ticker_max_date) else False
        print(f'预测未来日期：{self.future_flag}')
        # 列扩充构建新数据集
        self.build_history = utils.build_data(self.ticker, self.ticker_history, self.ticker_max_date)
        # 数据集改列名
        self.ticker_history.columns = ['target_' + col.replace(' ', '_').lower() for col in self.ticker_history.columns]
        self.build_history.columns = ['source_' + col.replace(' ', '_').lower() for col in self.build_history.columns]
        self.ticker_history_cols = self.ticker_history.columns.tolist()
        # 实例化模型训练模型
        self.client = ai_train.mlClient()
        # 各列对应模型
        self.col_models = {}
        # 评估指标
        self.kpis = {}

    def single_train(self):
        # 构建数据集
        X_data = self.build_history.shift(1)
        y_data = self.ticker_history[self.ticker_history.index.strftime("%Y-%m-%d") != self.ticker_min_date]
        train_data = pd.concat([y_data, X_data], axis=1)

        # 数据集清洗
        train_data = train_data.dropna().drop_duplicates()
        X = train_data[X_data.columns.tolist()]
        models = self.client.models.keys()
        col_models = {}
        kpis = {}

        # 训练阶段
        # 按列循环训练模型，获得每列的最优模型及评估指标
        for target_col in self.ticker_history_cols:
            y = pd.DataFrame(train_data[target_col])
            # st.write(pd.DataFrame(ticker_history[target_col]).columns[0])
            print(f'开始训练{target_col}最优模型...')
            df_model_compare = self.client.train(self.ticker, X, y, self.pred_date, self.re_train_path, models)
            # st.dataframe(df_model_compare)
            if self.kpi == 'All':
                # 获取4列评估的值进行平均
                kpi_value = df_model_compare.iloc[:, 3:7].mean(axis=1)
                # 找到最大值所在的行索引
                min_index = kpi_value.idxmin()
                kpi_value = kpi_value.loc[min_index]
                # print(min_index)
            else:
                min_index = df_model_compare[self.kpi].idxmin()
                kpi_value = df_model_compare.loc[min_index][self.kpi]
            best_model = df_model_compare.loc[min_index]['model']
            # 各列的的最优模型
            col_models[target_col] = best_model
            # 最优模型对应的评估指标
            kpis[target_col] = kpi_value
        self.col_models = col_models
        self.kpis = kpis
        return [col_models, kpis]

    def single_pred(self):
        # 预测阶段
        col_pred = {}
        final_pred = None
        # 构建未来日期的数据
        if self.future_flag:
            # 重新获取当前日期数据
            ticker_history_new = self.ticker_history
            # 循环预测开始日期
            current_pred_date = pd.to_datetime(self.ticker_max_date) + timedelta(days=1)
            final_pred = None
            print(f'循环预测{self.ticker} {current_pred_date.strftime("%Y-%m-%d")}至{self.pred_date} 数据，请耐心等待...')
            while current_pred_date <= pd.to_datetime(self.pred_date):

                print(f'开始预测{self.ticker} {current_pred_date.strftime("%Y-%m-%d")} 数据')
                build_data_date = utils.get_last_workday(current_pred_date).strftime("%Y-%m-%d")
                ticker_history_new.columns = [col.replace('target_', '').lower() for col in ticker_history_new.columns]
                print('开始列扩充构建新数据集...')
                build_history_new = utils.build_data(self.ticker, ticker_history_new, build_data_date, category='future')
                print(f'扩充后数据行：{build_history_new}')
                pred_date_row = (build_history_new[build_history_new.index.strftime("%Y-%m-%d") == build_data_date])
                pred_date_row.columns = ['source_' + col for col in pred_date_row.columns]

                print('预测源数据行...')
                print(pred_date_row)

                # 按列循环用每列的最优模型进行预测,获得各列预测值
                for target_col in self.ticker_history_cols:
                    model = self.col_models.get(target_col)
                    # print(f'开始使用模型{model}预测{target_col}的数据值...')
                    y_pred = self.client.predict(self.ticker, pred_date_row, target_col, model)
                    col_pred[target_col] = y_pred

                # 将 pred_date 转换为带有时区信息的 Timestamp 对象
                pred_date_tz = pd.Timestamp(current_pred_date).tz_localize('Asia/Shanghai')

                # 创建 total_pred DataFrame 并设置索引
                target_pred = pd.DataFrame(col_pred, index=[pred_date_tz]).T
                target_pred.index.name = 'Date'
                target_pred = target_pred.T

                print(f'{current_pred_date.strftime("%Y-%m-%d")} 预测结果...')
                # print(total_pred)

                final_pred = pd.concat([final_pred, target_pred])

                # 拼接未来日期的数据
                ticker_history_new.columns = ['target_' + col.replace(' ', '_').lower() for col in ticker_history_new.columns]

                ticker_history_new = pd.concat([ticker_history_new, target_pred], axis=0)

                current_pred_date += timedelta(days=1)
        else:
            print('预测源数据行...')
            pred_date_row = (self.build_history[self.build_history.index.strftime("%Y-%m-%d") == self.pred_date])
            print(pred_date_row)

            # 按列循环用每列的最优模型进行预测,获得各列预测值
            for target_col in self.ticker_history_cols:
                model = self.col_models.get(target_col)
                # print(f'开始使用模型{model}预测{target_col}的数据值...')
                y_pred = self.client.predict(self.ticker, pred_date_row, target_col, self.col_models.get(target_col))
                col_pred[target_col] = y_pred

            # 将 pred_date 转换为带有时区信息的 Timestamp 对象
            pred_date_tz = pd.Timestamp(self.pred_date).tz_localize('Asia/Shanghai')
            # 创建 total_pred DataFrame 并设置索引
            total_pred = pd.DataFrame(col_pred, index=[pred_date_tz]).T
            total_pred.index.name = 'Date'

            final_pred = total_pred.T
            print(f'{self.pred_date} 预测结果...')
            print(final_pred)

            # 拼接未来日期的数据
            ticker_history_new = pd.concat([self.ticker_history, final_pred], axis=0)
        # print(ticker_history_new)
        return [final_pred, col_pred, ticker_history_new]
