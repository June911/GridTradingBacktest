import os, sys
from bt_grid import *
from multiprocessing import Pool
from functions_processing_data import get_data
from functions_performance import f_SharpeRatio

# params
w0 = 60
tp = "arth"
lst_r = [0.1, 0.01, 0.001]
lst_n_grid = [5, 10, 20]
file_name = "binance_futures_DOTUSDT_20200101_20220322.csv"
df_data = get_data(file_name)
df_data = df_data.loc[df_data.index > pd.to_datetime("2022/1/1"), :].iloc[:1500, :]

# handle print
class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w", encoding="utf-8")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


def f_objective(r, n_grid):
    # init backtest
    bt = StaticGridBT(
        w0,
        r,
        n_grid,
        tp,
        df_data.close,
        is_trading_even=False,
        is_reverse_trading=False,
        tx_m=0,
        tx_t=0.0002,
    )

    with HiddenPrints():
        bt.run_on_bar()

    return f_SharpeRatio(bt.wealth, k=60 * 24 * 365)


def params_optmization(lst_r, lst_n_grid, parallel=True):
    # init pool
    p = Pool(2)

    # init params
    lst_params = [(x, y) for x in lst_r for y in lst_n_grid]
    print(lst_params)

    # start multiprocess -- optimization
    res = p.starmap(f_objective, lst_params)
    df_performance = pd.DataFrame(res, columns=["sharpe"], index=lst_params)

    return df_performance


def main():
    res = params_optmization(lst_r, lst_n_grid)
    print(res)


if __name__ == "__main__":
    main()
