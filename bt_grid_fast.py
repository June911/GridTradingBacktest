import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def get_price_range(p0, r, tp="arth"):
    if tp == "arth":
        pa = p0 * (1 - r)
        pb = p0 * (1 + r)
    elif tp == "geom":
        pa = p0 / (1 + r)
        pb = p0 * (1 + r)
    else:
        print("not right range type")

    return pa, pb


def get_grids(pa, pb, n_grid, tp="arth"):
    if tp == "arth":
        grids = np.linspace(pa, pb, n_grid + 1)
    elif tp == "geom":
        grids = np.geomspace(pa, pb, n_grid + 1)
    else:
        print("not right range type")
    return grids


# assuming the grids contains p0
def get_quantity_on_one_grid(wealth, grids, p0):
    quantity_on_one_grid = wealth / (np.sum(grids) - p0)
    return quantity_on_one_grid


class StaticGridBT:
    def __init__(
        self,
        w0,
        r,
        n_grid,
        tp,
        stock_prices,
        is_trading_even=False,
        is_reverse_trading=False,
        is_infinite_grid=False,
        tx_m=0,
        tx_t=0.0002,
    ):
        ## parameters
        # inital wealth
        self.w0 = w0
        self.r = r
        self.n_grid = n_grid
        self.tp = tp

        # when price move from cross one grid line, should we close our position or not
        # eg. grid = [8, 9, 10, 11, 12] p0 = 10, p1 = 11.5, p2 = 10
        #     from p0 to p1, we short one at 11,
        #     if is_trading_even is True, from p1 to p2, we close our position at 11, no profit unless the transaction costs is negative
        #     if is_trading_even is False, from p1 to p2, we do nothing
        self.is_trading_even = is_trading_even

        # when the price hits upper grids, we open long
        # when the price hits lower grids, we open short
        # when the price exits the price range, we close our positions
        # this is the reverse of original grid trading strategy
        self.is_reverse_trading = is_reverse_trading

        # if is is_infinite_grid,
        #   1. when the price hits the price range, we do not close our positions
        #   2. every time the price updates, we update our grid
        self.is_infinite_grid = is_infinite_grid

        # transaction cost
        # [maker, taker, and difference]
        self.tx_m = tx_m
        self.tx_t = tx_t
        self.dif_tx = tx_t - tx_m

        ## price data
        self.stock_prices = stock_prices
        p0 = self.stock_prices.iloc[0]

        ## on bar value
        self.positions = pd.Series(0, index=stock_prices.index)
        self.wealth = pd.Series(w0, index=stock_prices.index)
        self.pa, self.pb = get_price_range(p0, r, tp=tp)
        self.current_grid = get_grids(self.pa, self.pb, self.n_grid)
        self.last_transactions = np.array([p0])
        self.quantity_on_one_grid = get_quantity_on_one_grid(w0, self.current_grid, p0)

        self.grids_all = pd.DataFrame(
            0,
            index=stock_prices.index,
            columns=["grid" + str(i) for i in range(n_grid + 1)],
        )
        self.grids_all.iloc[0, :] = self.current_grid

    def get_transactions_from_grid_change(self, direction, last_price, current_price):
        """get_transactions_from_grid_change

        Args:
            direction (bool): price move direction
            last_price (float64): last_price
            current_price (float64): current_price

        Returns:
            int: number of transactions happened
        """
        # transactions
        if direction == 1:
            transactions = self.current_grid[
                (self.current_grid > last_price) & (self.current_grid < current_price)
            ]
            if len(self.last_transactions) > 0:
                if (np.min(self.last_transactions) in transactions) & (
                    not self.is_trading_even
                ):
                    # we ignore the minimum of last transactions
                    transactions = transactions[1:]
        else:
            transactions = self.current_grid[
                (self.current_grid > current_price) & (self.current_grid < last_price)
            ]
            if len(self.last_transactions) > 0:
                if (np.max(self.last_transactions) in transactions) & (
                    not self.is_trading_even
                ):
                    # we ignore the maximum of last transactions
                    transactions = transactions[:-1]

        return transactions

    def update_grids(self, current_price, current_wealth):
        """update price grids

        Args:
            current_price (float): current_price
            current_wealth (float): current_wealth
        """
        self.pa, self.pb = get_price_range(current_price, self.r, tp=self.tp)
        self.current_grid = get_grids(self.pa, self.pb, self.n_grid, tp=self.tp)
        self.quantity_on_one_grid = get_quantity_on_one_grid(
            current_wealth, self.current_grid, current_price
        )

    def on_bar(self, i):
        """handle position at every bar

        Args:
            i (int): bar position
        """
        current_price = self.stock_prices.iloc[i]
        last_price = self.stock_prices.iloc[i - 1]
        last_position = self.positions.iloc[i - 1]

        # price direction
        direction = 1 if current_price > last_price else -1

        # transactions
        transactions = self.get_transactions_from_grid_change(
            direction, last_price, current_price
        )

        # calculate transactions volume and average transactions price
        # volume direction is the negative of price direction
        # volume < 0, short
        # volume > 0, long
        # if is_reverse_trading, we reverse the direction
        if len(transactions) > 0:
            reverse_direction = 1 if self.is_reverse_trading else -1
            # transactions_volume = len(transactions) * direction * (-1)
            transactions_volume = len(transactions) * direction * reverse_direction
            avg_transactions_price = np.mean(transactions)
        else:
            transactions_volume, avg_transactions_price = 0, 0

        # calculate current position
        current_position = last_position + transactions_volume

        # calculate p&l from last step to this step
        # p&l = (current_price - last_price) * last_position
        #       + (current_price - avg_transactions_price) * transactions_volume
        #       - transactions fees
        # current_wealth = w_t + p&l
        transactions_quantity = transactions_volume * self.quantity_on_one_grid
        current_wealth = (
            self.wealth.iloc[i - 1]
            + (current_price - last_price) * last_position * self.quantity_on_one_grid
            + (current_price - avg_transactions_price) * transactions_quantity
            - avg_transactions_price * abs(transactions_quantity) * self.tx_m
        )

        if self.is_infinite_grid:
            # only update grid
            self.update_grids(current_price, current_wealth)
        else:
            ## if not infinite grid, we update grid only change when price outside [pa, pb]
            if (current_price < self.pa) | (current_price > self.pb):
                # close all positions
                current_position = 0

                # maker to taker
                # add additional transactions cost
                current_wealth = (
                    current_wealth
                    - avg_transactions_price * abs(transactions_quantity) * self.dif_tx
                )

                # update grid
                self.update_grids(current_price, current_wealth)

        # update relevant info
        if len(transactions) > 0:
            self.last_transactions = transactions
        self.last_position = current_position
        self.positions.iloc[i] = current_position
        self.wealth.iloc[i] = current_wealth
        self.grids_all.iloc[i, :] = self.current_grid

    def run_on_bar(self):
        """run for all bars"""
        for i in range(1, len(self.wealth)):
            self.on_bar(i)

    def plot_results(self):
        """plot results"""
        fig, axs = plt.subplots(3, 1, figsize=(20, 15), sharex=True)
        # price
        axs[0].plot(self.stock_prices)
        axs[0].plot(self.grids_all)
        axs[0].legend(["stock_prices"] + self.grids_all.columns.to_list())
        axs[0].set_title("stock_prices")
        axs[0].grid(True)

        # position
        axs[1].plot(self.positions, "-o", alpha=0.7, mfc="orange")
        axs[1].legend(["positions"])
        axs[1].set_title("positions")
        axs[1].grid(True)

        # wealth
        axs[2].plot(self.wealth)
        axs[2].legend(["wealth"])
        axs[2].set_title(f"wealth, r={self.r}, n_grid={self.n_grid}")
        axs[2].grid(True)

        plt.savefig("results.png")
