import os, sys
import pandas as pd

# handle print
class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w", encoding="utf-8")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


def get_matrix(df, x_name, y_name, value_name):
    """get matrix from a pandas dataframe

    Args:
        df (pandas dataframe): _description_
        x_name (str): colume name of x_axis
        y_name (str): colume name of y_axis
        value_name (str): colume name of value

    Returns:
        _type_: _description_
    """

    df_matrix = df.pivot_table(columns=x_name, index=y_name, values=value_name)
    try:
        df_matrix.index = df_matrix.index.astype(str)
        df_matrix.columns = df_matrix.columns.astype(str)
    except:
        pass

    return df_matrix


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

    # open = group_c.nth(0)["open"]
    # high = group_c["high"].max()
    # low = group_c["low"].min()
    close = group_c.tail(1)["close"]
    # volume = group_c["volume"].sum()
    # avg_price = group_c["open"].mean()

    df_new = pd.DataFrame()
    # df_new["open"] = open
    # df_new["high"] = high
    # df_new["low"] = low
    df_new["close"] = close.values
    # df_new["volume"] = volume
    # df_new["avg_price"] = avg_price
    df_new.index = index

    # groupby 可能 创造新的 index, 本身数据不存在，导致右面索引出现问题
    # 只取交集的部分
    # df_new = df_new.loc[df.index.intersection(df_new.index), :]

    return df_new
