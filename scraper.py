# Default imports
import os
import hashlib
import logging
from datetime import datetime
from time import sleep
from typing import Optional
from zlib import decompress
from base64 import urlsafe_b64decode as b64d

# Specific imports
import requests
import schedule  # type: ignore
from argh import arg, dispatch_command  # type: ignore

#
import reporters

# Constants
DEV = True
SLEEP_TIME = 60

DEFAULT_DELTA_TIME = 10
DEFAULT_UNIT_TIME = "minutes"
DEFAULT_DATA_FOLDER = "raw_data"
DEFAULT_ZIP = DEFAULT_DATA_FOLDER + ".zip"
DEFAULT_LOGGING_LEVEL = "INFO"

# TODO remove global variables
_static_previous_content_hash: Optional[str] = None
_hash_file_path = "hash.txt"


def get_previous_content_hash() -> Optional[str]:
    """
    Returns the hash of a previously saved file or None if no hash was saved
    :return: the hash of a previously saved file
    """
    global _static_previous_content_hash
    global _hash_file_path

    if _static_previous_content_hash is None \
            and os.path.isfile(_hash_file_path):
        with open(_hash_file_path) as file:
            _static_previous_content_hash = str(file.read())

    return _static_previous_content_hash


def set_previous_content_hash(previous_content_hash: str) -> str:
    """

    :param previous_content_hash:
    :return:
    """
    global _static_previous_content_hash
    global _hash_file_path

    _static_previous_content_hash = previous_content_hash
    with open(_hash_file_path, "w") as file:
        file.write(_static_previous_content_hash)
    return _static_previous_content_hash


# nothing to see here :)
obscured = b'eNoFwUEOwCAIBMAXVeLVzzQbA7WJKAF68PedGZkWjUiwEnEu2Ftku34TtfStZPBc7PcD5SCpZBOHPX5rNxV3'
PRICES_URL = decompress(b64d(obscured)).decode("utf-8")

def request_prices_data(duplicates: bool = False) -> Optional[str]:
    """
    Requests the latest prices from f1 fantasy

    If result is None then either the content is duplicated or there was a network error

    :return: latest prices from f1 fantasy
    """

    try:
        response = requests.get(PRICES_URL)
    except requests.exceptions.ConnectionError as exception:
        logging.warning(exception)
        return None

    if response.status_code != 200:
        logging.error(f"Unexpected status code code: {response.status_code}")
        return None

    current_content_hash = hashlib.sha256(response.content).hexdigest()
    previous_content_hash = get_previous_content_hash()
    if not duplicates \
            and previous_content_hash is not None \
            and previous_content_hash == current_content_hash:
        logging.info("Duplicated content.")
        return None

    logging.info("New data found.")

    set_previous_content_hash(current_content_hash)

    content = response.content.decode('UTF-8')

    content = "{" + f'"datetime":"{str(datetime.now())}",' \
                    f'"hash":"{current_content_hash}",' \
                    f'{content[1:]}'

    return content


def fetch_save_prices_data(data_folder: str, zip_path: str, report_path: str) -> None:
    """
    Fetches an updated prices from F1 fantasy saves the response in data_folder adds it to the zip in zip_path
    and finaly saves a resume in the report report_path

    :param data_folder:
    :param zip_path:
    :param report_path:
    :return:
    """

    content = request_prices_data()

    if content is None:
        return

    reporters.append_price_report(content, report_file=report_path)

    reporters.save_to_local_dir(content, data_folder=data_folder)

    reporters.save_to_local_zip(content, zip_path=zip_path)


@arg("--delta-time", "-dt",
     help="interval of time in unitTime between updates")
@arg("--unit-time", "-ut",
     help="unit of time to use with deltaTime",
     choices=["m", "minutes", "h", "hours", "s", "seconds"])
@arg("--data-folder", "-df",
     help="path to a folder where data will be stored")
@arg("--logging-level", "-ll",
     help="logging level to use",
     choices=['CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG'])
@arg("--logging-file", "-lf",
     help="file to save the logs")
@arg("--zip-file", "-zf",
     help="zipfile file where a backup of the data will be stored")
@arg("--report-file", "-rf",
     help="file to save the data in a smaller format")
def scraper(
        delta_time: int = DEFAULT_DELTA_TIME,
        unit_time: str = DEFAULT_UNIT_TIME,
        data_folder: str = DEFAULT_DATA_FOLDER,
        logging_level: str = DEFAULT_LOGGING_LEVEL,
        logging_file: Optional[str] = None,
        zip_file: str = "raw_data.zip",
        report_file: str = "raw_data.csv") -> None:
    logging.basicConfig(filename=logging_file,
                        level=logging.getLevelName(logging_level),
                        format='%(asctime)s | %(levelname)s | %(message)s')

    logging.info("Starting scraper...")

    if not os.path.isdir(data_folder):
        os.mkdir(data_folder)

    job = schedule.every(delta_time)

    if unit_time in ["m", "minutes"]:
        job = job.minutes
    elif unit_time in ["s", "seconds"]:
        job = job.seconds
    elif unit_time in ["h", "hours"]:
        job = job.hours

    job.do(fetch_save_prices_data,
           data_folder=data_folder,
           zip_path=zip_file,
           report_path=report_file).run()

    while True:
        try:
            schedule.run_pending()
            sleep(SLEEP_TIME)
        except KeyboardInterrupt:
            logging.info("Exiting program.")
            return


if __name__ == "__main__":
    try:
        dispatch_command(scraper)
    except Exception as e:
        logging.critical(e)
