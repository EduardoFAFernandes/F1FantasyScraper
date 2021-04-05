# Default imports
import os
import zipfile
import hashlib
import logging
import json
from datetime import datetime
from time import sleep


# Specific imports
import requests
import schedule
import pandas as pd
from argh import arg, dispatch_command


# Constants
DEV = True
SLEEP_TIME = 60

DEFAULT_DELTA_TIME = 10
DEFAULT_UNIT_TIME = "minutes"
DEFAULT_DATA_FOLDER = "raw_data"
DEFAULT_ZIP = DEFAULT_DATA_FOLDER + ".zip"
DEFAULT_LOGGING_LEVEL = "INFO"



# TODO remove global variables
_static_previous_content_hash = None
_hash_file_path = "hash.txt"


def get_previous_content_hash():
    """

    :return:
    """
    global _static_previous_content_hash
    global _hash_file_path

    if _static_previous_content_hash is None \
            and os.path.isfile(_hash_file_path):
        with open(_hash_file_path) as file:
            _static_previous_content_hash = str(file.read())

    return _static_previous_content_hash


def set_previous_content_hash(previous_content_hash):
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


def request_prices_data():
    """
    Requests the latest prices from f1 fantasy api

    If result is None then either the content is duplicated or there was a network error

    :return: latest prices from f1 fantasy
    """

    prices_url = "https://fantasy-api.formula1.com/partner_games/f1/players"

    try:
        response = requests.get(prices_url)
    except requests.exceptions.ConnectionError as exception:
        logging.warning(exception)
        return None

    if response.status_code != 200:
        logging.error(f"Unexpected status code code: {response.status_code}")
        return None

    current_content_hash = hashlib.sha256(response.content).hexdigest()
    previous_content_hash = get_previous_content_hash()
    if previous_content_hash is not None \
            and previous_content_hash == current_content_hash:
        logging.info("Duplicated content.")
        return None

    logging.info("New data found.")

    set_previous_content_hash(current_content_hash)

    content = response.content.decode('UTF-8')
    # content = "{" + f'"datetime":"{str(datetime.now())}","hash":"{current_content_hash}",{content[1:]}'
    return content


def extract_asset_info(asset):
    """
    Extracts relevant information for each asset

    :param asset: asset object to extract information
    :return: dictionary with the relevant asset information
    """
    starting_price = next(filter(lambda price: price["game_period_id"] == 70, asset["season_prices"]))["price"]

    return {
        "id": int(asset['id']),
        "name": asset['display_name'],
        "price": float(asset['price']),
        "price_delta": float(asset['price']) - float(starting_price),
        "probability_price_up_percentage": int(asset['current_price_change_info']['probability_price_up_percentage']),
        "probability_price_down_percentage": int(
            asset['current_price_change_info']['probability_price_down_percentage']),
        "current_selection_percentage": int(asset['current_price_change_info']["current_selection_percentage"])
    }


def append_price_report(content, datetime_price_report, report_file):
    """
    Extract relevant information from the new file

    :param content: raw prices data content
    :param datetime_price_report: date of the price report
    :param report_file: report file used to collect all reports
    :return: None
    """
    data = json.loads(content)
    assets = [extract_asset_info(asset) for asset in data['players']]

    report = pd.DataFrame(assets) \
        .set_index("id")

    report["datetime"] = str(datetime_price_report)

    report.to_csv(report_file, mode='a', header=not os.path.isfile(report_file))


def fetch_save_prices_data(data_folder, zip_path, report_path):
    """
    Fetches an updated prices from F1 fantasy saves the response in data_folder adds it to the zip in zip_path
    and finaly saves a resume in the report report_path

    :param data_folder:
    :param zip_path:
    :param report_path:
    :return:
    """
    now = datetime.now()

    content = request_prices_data()

    if content is None:
        return

    append_price_report(content, now, report_path)

    #generating file name based on time of the request
    file_sufix = "f1Players"
    filename = f"{file_sufix}_{now.year:04d}_{now.month:02d}_{now.day:02d}" \
               f"_{now.hour:02d}_{now.minute:02d}_{now.second:02d}.json"
    file_path = os.path.join(data_folder, filename)

    #saving json file
    with open(file_path, "w") as out:
        out.write(content)

    # Saving to a zip file
    with zipfile.ZipFile(zip_path, "a") as myZipFile:
        myZipFile.write(file_path, os.path.basename(file_path), zipfile.ZIP_DEFLATED)

    # os.remove(filepath)


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
def scraper(  # todo add missing args : zip_path report_path
        delta_time=DEFAULT_DELTA_TIME,
        unit_time=DEFAULT_UNIT_TIME,
        data_folder=DEFAULT_DATA_FOLDER,
        logging_level=DEFAULT_LOGGING_LEVEL,
        logging_file=None,
        zip_path="raw_data.zip",
        report_path="prices.csv"):
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

    job.do(fetch_save_prices_data, data_folder=data_folder, zip_path=zip_path, report_path=report_path).run()

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
