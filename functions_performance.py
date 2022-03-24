from typing import final
import numpy as np
import pandas as pd


def f_AnnualReturn(portfolio_wealth):
    """calculate AnnualReturn

    Args:
        portfolio_wealth (pandas.Series): series of wealth

    Returns:
        float: annual_return
    """

    n_days = (portfolio_wealth.index[-1] - portfolio_wealth.index[0]).days
    final_wealth = portfolio_wealth.iloc[-1]
    initial_wealth = portfolio_wealth.iloc[0]

    annual_return = (final_wealth / initial_wealth - 1) / n_days * 365
    return annual_return


def f_SharpeRatio(portfolio_wealth, rf=0.05, n_transactions=1, k=365):
    """_summary_

    Args:
        portfolio_wealth (pandas.Series): series of wealth
        rf (float): risk free rate
        n_transactions (int, optional): number of transactions. Defaults to 1.
        k (int, optional): days in a year. Defaults to 365.

    Returns:
        _type_: _description_
    """

    if n_transactions > 0:
        annual_return = f_AnnualReturn(portfolio_wealth)
        portfolio_returns = portfolio_wealth.pct_change()
        anuual_standard_deviation = portfolio_returns.std(axis=0) * np.sqrt(k)
        sharpe_ratio = (annual_return - rf) / anuual_standard_deviation
    else:
        sharpe_ratio = 0
    return sharpe_ratio
