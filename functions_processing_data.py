"""
Functions to handle data
"""

import os
import pandas as pd
import numpy as np


def get_data(file_name, from_database=False, from_params=False):

    data_path = os.path.join(os.getcwd(), "data")

    # 读取文件
    if from_database:
        df = pd.read_csv(
            os.path.join(data_path, file_name), header=[0, 1], index_col=[0]
        )
        if df.columns.nlevels == 2:
            df = df.droplevel(0, 1)
            df = df[["open", "high", "low", "close", "volume"]]
            df.index = pd.to_datetime(df.index)

    elif from_params:
        df = pd.read_excel(os.path.join(data_path, file_name), index_col=0)

    else:
        df = pd.read_csv(os.path.join(data_path, file_name), index_col=0)
        df.index = pd.to_datetime(df.index)
        df.rename(
            columns={
                "Time": "time",
                "Open": "open",
                "High": "high",
                "Close": "close",
                "Low": "low",
                "Volume": "volume",
                "price": "close",
            },
            inplace=True,
        )

    # handle missing data
    # for i in range(len(df)-1):
    #     next_m = df.index[i] +  pd.Timedelta(minutes=1)
    #     if next_m != btc_current.index[i+1]:
    #         print('-'*80)
    #         print(i)
    #         print("预测值  ", next_m)
    #         print("实际值  ", btc_current.index[i+1])
    #         next_m = btc_current.index[i+1]
    #

    return df


def f_change_barperiod(df, freq):
    """
    K线转换
    eg: from
    :param df:
    :param freq: Y, Q, M, W, D, H, T(min), S
    :return: 新周期的K线图
    """

    group_c = df.groupby(pd.Grouper(freq=freq))

    index = group_c.nth(0).index
    open = group_c.nth(0)["open"]
    high = group_c["high"].max()
    low = group_c["low"].min()
    close = group_c.tail(1)["close"]
    volume = group_c["volume"].sum()
    avg_price = group_c["open"].mean()

    df_new = pd.DataFrame()
    df_new["open"] = open
    df_new["high"] = high
    df_new["low"] = low
    df_new["close"] = close.values
    df_new["volume"] = volume
    df_new["avg_price"] = avg_price
    df_new.index = index

    # groupby 可能 创造新的 index, 本身数据不存在，导致右面索引出现问题
    # 只取交集的部分
    df_new = df_new.loc[df.index.intersection(df_new.index), :]

    return df_new


def f_change_to_time(df, freq):
    """
    标记这个时间段，属于每天中的哪些时间区间
    :param df:
    :return:
    """

    # 先换算成想要的时间评率
    df = f_change_barperiod(df, freq)

    df_new = df.copy()
    df_new["timeofday"] = df.groupby(lambda x: x.time).grouper.group_info[0]

    # if box_plot:
    #     df_new.boxplot(column=["volume"], by=["timeofday"])

    return df_new


def f_drop_timezone(df):
    """
    Set timezome to None
    :param df:
    :return:
    """
    df.index = df.index.tz_convert(None)
    df.index = df.index.astype(str)
    return df


def f_get_returns_from_specific_time_range(df, lst_time):
    """
    :param df:
    :param lst_time: eg. [22, 0, 7]
    :return:
    """
    df_timeofday = f_change_to_time(df, "1H")

    bool = df_timeofday["timeofday"].apply(lambda x: x in lst_time)
    df_close_inrange = df_timeofday.close[bool]
    df_rets_inrange = df_close_inrange.pct_change().shift(-1)
    df_rets_inrange = df_rets_inrange.to_frame()

    df_rets_inrange["timeofday"] = df_rets_inrange.groupby(
        lambda x: x.time
    ).grouper.group_info[0]

    x = df_rets_inrange[(df_rets_inrange["timeofday"] == 2)]["close"]
    y = df_rets_inrange[(df_rets_inrange["timeofday"] == 0)]["close"]
    lst = []
    for i in range(392):
        next_rets_index = x.index[i] + pd.Timedelta("2H")
        try:
            next_rets = y.loc[next_rets_index]
            lst.append(next_rets)
        except:
            print(next_rets_index)
            lst.append(np.nan)

    df_results = pd.DataFrame(
        data=np.transpose([x.to_list(), lst]), index=x.index, columns=["x", "y"]
    )
    return df_results
