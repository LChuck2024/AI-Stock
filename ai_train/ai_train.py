# 导入需要的包
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
import datetime
# from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor
# from sklearn.svm import LinearSVC
from sklearn.ensemble import VotingRegressor
from sklearn.ensemble import BaggingRegressor
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import StackingRegressor
# from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error, root_mean_squared_error
import warnings
import joblib
import os
import streamlit as st
import shutil

warnings.filterwarnings('ignore', category=FutureWarning)  # 忽略 FutureWarning

# 项目目录
Home_path = st.session_state.path
dicts_path = os.path.join(Home_path, 'ai_train', 'dicts')
models_path = os.path.join(Home_path, 'ai_train', 'models')

if not os.path.exists(dicts_path):
    os.makedirs(dicts_path)

if not os.path.exists(models_path):
    os.makedirs(models_path)


class mlClient(object):
    def __init__(self):
        self.mu = None
        self.sigma = None
        self.models = {
            'KNN': KNeighborsRegressor
            # ,'GaussianNB': GaussianNB
            , 'DecisionTree': DecisionTreeRegressor
            # , 'Logistic': LogisticRegression
            , 'RandomForest': RandomForestRegressor
            # ,'LinearSVC': LinearSVC
            # , 'LGBM': LGBMRegressor
            , 'Voting': VotingRegressor
            , 'Bagging': BaggingRegressor
            , 'Boost': AdaBoostRegressor
            , 'Stacking': StackingRegressor
        }
        self.estimators = [
            [
                ('KNN', KNeighborsRegressor(n_neighbors=200))
                # ,('GaussianNB', GaussianNB())
                , ('DecisionTree', DecisionTreeRegressor())
                # ,('Logistic', LogisticRegression(max_iter=100000))
                , ('RandomForest', RandomForestRegressor())
                # , ('LinearSVC', LinearSVC(dual=True))
            ]
        ]
        self.params = {
            'KNN': {'n_neighbors': [17]}
            # ,'Logistic': {'max_iter': [100000]}
            , 'LinearSVC': {'dual': [True]}
            , 'Voting': {'estimators': self.estimators}
            , 'Stacking': {'estimators': self.estimators, 'final_estimator': [RandomForestRegressor()]}
        }
        self.column_names = ["model", "train_time", "pred_time", "mae", "mse", "mape", "rmse", "importances"]

    def train(self, ticker, X, y, pred_date, re_train_path, selections=['DecisionTree']):

        ticker_model_path = f'{models_path}/{re_train_path}/{ticker}'
        print('*'*100)
        target_column = y.columns[0]
        print(target_column)
        if not os.path.exists(f'{ticker_model_path}/{target_column}_model_compare.pkl'):
            print(f'{ticker}模型比对数据不存在，开始训练...')
            model_compare = []

            print(f'预测数据集 -> X.shape:{X.shape},y.shape:{y.shape},selections:{selections}')

            # 数据拆分
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

            # 数据标准化
            self.mu = X_train.mean()
            self.sigma = X_train.std()
            X_train = (X_train - self.mu) / self.sigma
            X_test = (X_test - self.mu) / self.sigma
            selected_models = {key: self.models[key] for key in selections if key in self.models}

            # for col in X_train.columns:
            #     if X_train[col].isna().any():
            #         print(f'col:{col},unique:{X_train[col].unique()}')
            # return

            if not os.path.exists(f'{ticker_model_path}'):
                os.makedirs(f'{ticker_model_path}')

            for name, model_class in selected_models.items():
                if os.path.exists(f'{ticker_model_path}/{target_column}_{name}.pkl'):
                    print(f'{ticker} {name}模型已存在,跳过训练...')
                    continue

                if name in self.params and name in selections:
                    param = {k: v[0] for k, v in self.params[name].items()}
                    # print(name,param)
                    clf = model_class(**param)
                else:
                    clf = model_class()

                train_start_time = datetime.datetime.now()
                print(f'{target_column}模型训练:{name}')

                # 模型训练
                clf.fit(X=X_train, y=y_train)
                train_end_time = datetime.datetime.now()
                train_time = round((train_end_time - train_start_time).total_seconds(), 2)

                # 模型预测
                y_pred = clf.predict(X=X_test)
                pred_end_time = datetime.datetime.now()
                pred_time = round((pred_end_time - train_end_time).total_seconds(), 2)

                # 模型评估
                # mean_absolute_error, mean_squared_error, mean_absolute_percentage_error, root_mean_squared_error
                mae = mean_absolute_error(y_test, y_pred)
                mse = mean_squared_error(y_test, y_pred)
                mape = mean_absolute_percentage_error(y_test, y_pred)
                rmse = root_mean_squared_error(y_test, y_pred)

                print(f'{name}模型评估 -> mae:{mae},mse:{mse},mape:{mape},rmse:{rmse}')
                # print(y_test)
                # print(y_pred)
                # return
                importances = None
                try:
                    importances = clf.feature_importances_
                except:
                    print(f'{name}模型没有feature_importances_')

                model_compare.append([name, train_time, pred_time, mae, mse, mape, rmse, importances])
                # 覆盖保存模型
                joblib.dump([clf, self.mu, self.sigma, mae, mse, mape, rmse], f'{ticker_model_path}/{target_column}_{name}.pkl')

            joblib.dump(model_compare, f'{ticker_model_path}/{target_column}_model_compare.pkl')
        else:
            print(f'{ticker}模型比对数据已存在，直接加载...')
            model_compare = joblib.load(f'{ticker_model_path}/{target_column}_model_compare.pkl')
        df_model_compare = pd.DataFrame(model_compare, columns=self.column_names)
        print(f'{target_column}训练完成!')

        # 覆盖新生成模型到保存目录
        if re_train_path == pred_date:
            print('覆盖新生成模型到保存目录')
            shutil.rmtree(f'{models_path}/saved/{ticker}/')
            shutil.copytree(f'{models_path}/{re_train_path}/{ticker}/', f'{models_path}/saved/{ticker}/')

        return df_model_compare

    def predict(self, ticker, X, target_col, best_model):
        # print(X.shape)
        [model, mu, sigma, _, _, _, _] = joblib.load(f'{models_path}/saved/{ticker}/{target_col}_{best_model}.pkl')
        data = (X - mu) / sigma
        print(f'{target_col} 预测中！')
        # print(data)
        y_pred = model.predict(data)[0]
        # print(f'{target_col} : {y_pred}')
        return y_pred
