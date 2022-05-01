# ### get market depth data from crypto-chassis
# url: https://github.com/crypto-chassis/cryptochassis-data-api-docs

import os, json
import pandas as pd
import datetime
from datetime import date

import requests
from bs4 import BeautifulSoup
import json

base_url = "https://api.cryptochassis.com/v1"
NUM_RETRIES = 3


def quickSoup(url):
    """_summary_

    Args:
        url (str): crypto-chassis url

    Returns:
        bs4.BeautifulSoup: parsed response for url
    """

    header = {}
    header[
        "User-Agent"
    ] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"

    response = ""
    # send request to scraperapi, and automatically retry failed requests
    for _ in range(NUM_RETRIES):
        try:
            response = requests.get(url, headers=header, timeout=10)
            if response.status_code in [200, 404]:
                ## escape for loop if the API returns a successful response
                break
        except requests.exceptions.ConnectionError:
            response = ""

    ## parse data if 200 status code (successful response)
    if response.status_code == 200:
        ## parse data with beautifulsoup
        soup = BeautifulSoup(response.content, "html.parser")

        ##
        if "Page Cannot be Found" in soup.get_text():
            return None

        return soup

    elif response.status_code == 404:
        print("not found url")
        return None


def get_url(
    dataType,
    exchange,
    instrument,
    dataType2=1,
    interval=10,
    startSecond=None,
    endSecond=None,
):
    """_summary_

    Args:
        dataType (str): _description_
            1. market-depth
            2. trade
            3. ohlc
        exchange (str): exchange name
            - bitfinex,bitmex,binance,binance-coin-futures,binance-usds-futures,binance-us,
            - bitstamp,coinbase,deribit,ftx,ftx-us,gateio,gateio-perpetual-futures,gemini,
            - huobi,huobi-coin-swap,huobi-usdt-swap,kucoin,kraken,kraken-futures,okex
        instrument (str): pair name
            for binance-usds-futures:


        dataType2 (int, optional): number of depth only for depth. Defaults to 1.
        startSecond (str, optional): _description_. Defaults to None.
    """

    url = base_url + "/" + dataType + "/" + exchange + "/" + instrument

    if dataType == "market-depth":
        # GET /market-depth/<exchange>/<instrument>?depth=<depth>&startTime=<startTime>
        url = url + "?depth=" + str(dataType2)
        if startSecond:
            url = url + "&startTime=" + str(startSecond)
    elif dataType == "trade":
        # GET /trade/<exchange>/<instrument>?startTime=<startTime>
        if startSecond:
            url = url + "?startTime=" + str(startSecond)
    elif dataType == "ohlc":
        # GET /ohlc/<exchange>/<instrument>?interval=<interval>&startTime=<startTime>&endTime=<endTime>
        # still in progress
        url = url + "?interval=" + str(interval)
        if startSecond:
            url = url + "&startTime=" + str(startSecond)
        if endSecond:
            url = url + "&startTime=" + str(endSecond)

    return url


def main():
    dataType = "market-depth"
    dataType = "trade"
    exchange = "binance-usds-futures"
    # instrument = "btcusdt"
    instrument = "xrpusdt"
    instrument = "ethusdt"
    startTime = pd.to_datetime("2022/4/22")
    startSecond = int((startTime - datetime.datetime(1970, 1, 1)).total_seconds())

    lst_url = []
    for i in range((pd.to_datetime(date.today()) - startTime).days - 1):
        # find start seconds in the consecutive days
        startSecond = startSecond + 60 * 60 * 24
        # find url
        url = get_url(dataType, exchange, instrument)
        soup = quickSoup(url)
        url_download = json.loads(soup.get_text())["urls"][0]["url"]

        print("-" * 80)
        print(i)
        print("start second: ", startSecond)
        print("start time: ", pd.to_datetime(startSecond, unit="s"))
        print(f"url: {url}")
        # print(f"url_download: {url_download}")

    # url = get_url(dataType, exchange, instrument)
    # print(f"url: {url}")

    # soup = quickSoup(url)
    # # print(f"soup: {soup}")

    # url_download = json.loads(soup.get_text())["urls"][0]["url"]
    # print(f"url_download: {url_download}")


if __name__ == "__main__":
    main()
