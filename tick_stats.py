import os
import pandas as pd
import numpy as np


def read_data(file_name):
    """Read csv data from binance website
    website -> https://data.binance.vision/?prefix=data/futures/um/daily/trades/
    format ->
    [
    {
        "id": 28457,                // 成交ID
        "price": "4.00000100",      // 成交价格
        "qty": "12.00000000",       // 成交量
        "quoteQty": "48.00",        // 成交额
        "time": 1499865549590,      // 时间
        "isBuyerMaker": true        // 买方是否为挂单方
    }
    ]

    Args:
        file_name (_type_): _description_
    """

    data_path = os.path.join(os.getcwd(), "data")
    df_data = pd.read_csv(
        os.path.join(data_path, file_name),
        names=["id", "close", "qty", "quoteQty", "time", "isBuyerMaker"],
    )
    df_data.set_index("time", inplace=True)
    df_data.index = pd.to_datetime(df_data.index, unit="ms")

    return df_data


def get_info(file_name):
    if "BTC" in file_name:
        price_precision = 1
        tick_size = 0.1
    elif "ETH" in file_name:
        price_precision = 2
        tick_size = 0.01
    elif "XRP" in file_name:
        price_precision = 4
        tick_size = 0.0001

    info = {}
    info["file_name"] = file_name
    info["price_precision"] = price_precision
    info["tick_size"] = tick_size
    return info


def processing_data(df_data, info):

    # dif_tick
    df_data.loc[:, "dif_tick"] = np.round(df_data.close.diff() / info["tick_size"])
    lst_quantile = np.arange(0.1, 1, 0.1)
    lst_quantile = np.append(lst_quantile, [0.95, 0.99, 0.999, 0.9999, 1])
    tick_change_quantile = df_data.dif_tick.abs().quantile(lst_quantile)

    # time to millseconds
    df_data.loc[:, "millseconds"] = df_data.index.view(np.int64) / int(1e6)
    # difference in millseconds
    df_data.loc[:, "d_millseconds"] = df_data.loc[:, "millseconds"].diff().round()
    time_change_quantile = df_data.d_millseconds.abs().quantile(lst_quantile)

    # save
    df_frequency = pd.concat([tick_change_quantile, time_change_quantile], axis=1)
    df_frequency.index = df_frequency.index * 100
    df_frequency.rename(
        columns={"dif_tick": "每个tick的价格变化", "d_millseconds": "每个tick的时间变化"},
        inplace=True,
    )

    result_path = os.path.join(os.getcwd(), "results")
    df_frequency.to_excel(
        os.path.join(result_path, info["file_name"].split(".csv")[0] + "_fq.xlsx")
    )

    return df_frequency


def main():
    lst_filename = [
        "BTCBUSD-trades-2022-04-21.csv",
        "ETHBUSD-trades-2022-04-21.csv",
        "XRPBUSD-trades-2022-04-21.csv",
    ]

    # file_name = "BTCBUSD-trades-2022-04-21.csv"
    # file_name = "ETHBUSD-trades-2022-04-21.csv"
    # file_name = "XRPBUSD-trades-2022-04-21.csv"

    for file_name in lst_filename:
        info = get_info(file_name)
        df_data = read_data(file_name)
        processing_data(df_data, info)

        print("-" * 80)
        print(file_name)
        print(f"total_count: {df_data.shape[0]}")


if __name__ == "__main__":
    main()
