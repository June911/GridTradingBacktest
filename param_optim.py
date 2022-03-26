import tqdm
import multiprocessing
from bt_grid import *
from functions_processing_data import get_data
from functions_performance import f_SharpeRatio
from helpful_scripts import HiddenPrints, get_matrix

import seaborn as sns


# params
w0 = 60
tp = "arth"

lst_r = [0.001 * 2**i for i in range(10)]
lst_n_grid = [5 * 2**i for i in range(5)]
lst_tx = np.round(np.arange(1, 6, 2) * 0.0001, 4)
file_name = "binance_futures_DOTUSDT_20200101_20220322.csv"
df_data = get_data(file_name)
df_data = df_data.loc[df_data.index > pd.to_datetime("2022/1/1"), :].iloc[:10000, :]


def f_objective(r, n_grid, tx_m):
    # init backtest
    bt = StaticGridBT(
        w0,
        r,
        n_grid,
        tp,
        df_data.close,
        is_trading_even=False,
        is_reverse_trading=True,
        tx_m=tx_m,
        tx_t=tx_m + 0.0002,
    )

    with HiddenPrints():
        bt.run_on_bar()

    return f_SharpeRatio(bt.wealth, k=60 * 24 * 365)


def params_optmization(lst_r, lst_n_grid, lst_tx):
    # init params
    lst_params = [(x, y, z) for x in lst_r for y in lst_n_grid for z in lst_tx]
    print(len(lst_params))

    # init pool
    p = multiprocessing.Pool(multiprocessing.cpu_count() - 1)

    # start multiprocess -- optimization
    res = list(tqdm.tqdm(p.starmap(f_objective, lst_params), total=len(lst_params)))
    p.close()
    p.join()

    # output
    df_performance = pd.DataFrame(lst_params, columns=["r", "n_grid", "tx_m"])
    df_performance["SharpRatio"] = res

    return df_performance


def main():
    df_performance = params_optmization(lst_r, lst_n_grid, lst_tx)
    print(df_performance)


if __name__ == "__main__":
    main()
