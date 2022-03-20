"""
A module that provides a way to get F1 Fantasy price data

Can be used in the command line: python scraper.py
"""

# Default imports
import json
import logging
import os
from base64 import urlsafe_b64decode as b64d
from dataclasses import dataclass
from datetime import datetime
from time import sleep
from typing import Any, Optional
from zlib import decompress


# Specific imports
import pandas as pd #type: ignore
import requests
import schedule #type: ignore
from argh import arg, dispatch_command #type: ignore

# Constants
SLEEP_TIME = 60

DEFAULT_DELTA_TIME = None
DEFAULT_UNIT_TIME = "minutes"
DEFAULT_LOGGING_LEVEL = "INFO"
DEFAULT_REPORT_FILE = "prices.csv"
DEFAULT_LOGGING_FILE = None

# nothing to see here :)
OBFUSCATED = b'eJzLKCkpKLbS109LzCtJLK7UTSzI1EvLL8otzUk01EvOz9VPM9Q3MjAy0i_ISaxMLSoGAKgiENU='
PRICES_URL = decompress(b64d(OBFUSCATED)).decode("utf-8")


def fetch_prices_data() -> Optional[str]:
    """
    Requests the latest prices from F1 fantasy

    If result is None then either the content is duplicated or there was a
    network error

    :return: latest prices from f1 fantasy
    """

    try:
        logging.info("Sending price request to server.")
        response = requests.get(PRICES_URL)

    except requests.exceptions.ConnectionError as exception:
        logging.warning(exception)
        return None

    if response.status_code != 200:
        logging.error("Unexpected status code code: %s",
            response.status_code)
        return None

    logging.info("Received pricing data from server.")

    content = response.content.decode('UTF-8')

    return content


@dataclass()
class Asset:
    """
    A class used to store relevant information about one asset
    """

    asset_id: int
    name: str
    price: float
    sentiment: int
    selection_percentage: int
    date_time: str
    timestamp: int

    def __init__(self, asset: Any, now:datetime):
        """
        Extracts relevant information a given asset

        :param asset: asset object to extract information
        :return: dictionary with the relevant asset information
        """

        if asset['current_price_change_info'] is None:
            raise Exception("Price change info unavailable.")

        self.asset_id = int(asset['id'])
        self.name = str(asset['display_name'])
        self.price = float(asset['price'])
        self.sentiment = int(asset['current_price_change_info']\
                        ['probability_price_up_percentage'])\
                        - int(asset['current_price_change_info']\
                        ['probability_price_down_percentage'])
        self.selection_percentage = int(asset['current_price_change_info']\
                                ["current_selection_percentage"])
        self.date_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self.timestamp = int(now.timestamp())


def default_report(content: str) -> pd.DataFrame:
    """
    Creates a Pandas DataFrame from asset information

    :param content the raw date from the request
    :return Pandas DataFrame with assets and their relevant information
    """

    data = json.loads(content)
    now = datetime.now()
    assets = [Asset(asset, now) for asset in data['players']]
    report = pd.DataFrame(assets).set_index("asset_id")

    return report


def report_to_csv(report: pd.DataFrame, report_file: str) -> None:
    """
    Extract relevant information from content and append it to a csv file

    :param report_file: report file used to collect all reports
    :return: None
    """

    report.to_csv(report_file,
                  mode='a',
                  header=not os.path.isfile(report_file))

    logging.info("Saved prices to csv file: %s", report_file)


def fetch_save(report_file: str) -> None:
    """
    Fetches the most recent prices, generates a report and saves it to a
    CSV file.

    :param report_file the path to the csv file
    """

    data = fetch_prices_data()

    if data is None:
        raise Exception("Empty response from server.")

    report = default_report(data)

    report_to_csv(report, report_file)


@arg("--delta-time", "-dt",
     help="interval of time in unitTime between updates")
@arg("--unit-time", "-ut",
     help="unit of time to use with deltaTime",
     choices=["m", "minutes", "h", "hours"])
@arg("--logging-level", "-ll",
     help="logging level to use",
     choices=['CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG'])
@arg("--logging-file", "-lf",
     help="file to save the logs")
@arg("--report-file", "-rf",
     help="file to save the data in a smaller format")
def scrape(
        delta_time: Optional[int] = DEFAULT_DELTA_TIME,
        unit_time: str = DEFAULT_UNIT_TIME,
        logging_level: str = DEFAULT_LOGGING_LEVEL,
        logging_file: Optional[str] = DEFAULT_LOGGING_FILE,
        report_file: str = DEFAULT_REPORT_FILE) -> None:
    """
    Main Function that manages scraping scheduling.

    :param delta_time time interval between price fetching if None only fetches
                      data once
    :param unit_time time unit the interval uses (m)inutes or (h)ours
    :param logging_level the logging level to be used
    :param logging_file the file where logs be stored if None stdout is used
    :param report_file the name of the file where results should be stored"""

    logging.basicConfig(filename=logging_file,
                        level=logging.getLevelName(logging_level),
                        format='%(asctime)s | %(levelname)s | %(message)s')

    if delta_time is None:
        logging.info("Starting to fetch...")
        fetch_save(report_file)
        logging.info("Done.")
        return

    try:
        delta_time = int(delta_time)
    except ValueError:
        logging.error("Unable to parse delta_time %s", delta_time)
        return

    if delta_time <= 0:
        logging.error("delta_time must be > 0")
        return

    logging.info("Starting to scrape...")

    job = schedule.every(delta_time)

    if unit_time in ["m", "minutes"]:
        job = job.minutes
    elif unit_time in ["h", "hours"]:
        job = job.hours
    else:
        logging.error("Invalid delta time: %s", unit_time)

    job.do(fetch_save, report_file=report_file).run()

    while True:
        try:
            schedule.run_pending()
            sleep(SLEEP_TIME)
        except KeyboardInterrupt:
            logging.info("Stopping scrapper.")
            return


if __name__ == "__main__":

    try:
        dispatch_command(scrape)
    except Exception as e:
        logging.critical(e)
        raise e
