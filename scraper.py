# Default imports
import logging
from datetime import datetime
from time import sleep
from typing import Optional
from zlib import decompress
from base64 import urlsafe_b64decode as b64d


# Specific imports
import requests
import schedule  # type: ignore
from argh import arg, dispatch_command, ArghParser  # type: ignore

# Custom imports
import reporters

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
        logging.error(f"Unexpected status code code: {response.status_code}")
        return None

    logging.info("Received pricing data from server.")

    content = response.content.decode('UTF-8')

    return content


def fetch_save(report_file: str) -> None:

    data = fetch_prices_data()

    if data is None:
        raise Exception("Empty response from server.")

    report = reporters.default_report(data)

    reporters.report_to_csv(report, report_file)


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

    logging.basicConfig(filename=logging_file,
                        level=logging.getLevelName(logging_level),
                        format='%(asctime)s | %(levelname)s | %(message)s')

    if delta_time is None:
        logging.info("Starting to fetch...")
        fetch_save(report_file)
        logging.info("Done.")
        return
    else:
        try:
            delta_time = int(delta_time)
        except ValueError:
            logging.error(f"Unable to parse delta_time {delta_time}")
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
