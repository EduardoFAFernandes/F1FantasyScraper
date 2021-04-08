import zipfile
import os
import json
import datetime

import pandas as pd


_GEN_FILENAME_SUFIX = "f1Players"


def _gen_filename(content):
    dt_srt = json.loads(content)["datetime"]
    if '.' not in dt_srt:
        dt_srt += '.0'
    now = datetime.datetime(2, 2, 2).strptime(dt_srt, "%Y-%m-%d %H:%M:%S.%f")
    return f"{_GEN_FILENAME_SUFIX}_{now.year:04d}_{now.month:02d}_{now.day:02d}" \
           f"_{now.hour:02d}_{now.minute:02d}_{now.second:02d}.json"


def save_to_local_dir(content, data_folder="."):
    """
    Saves the content to a json file in a given folder

    :param content: content to save to the json file
    :param data_folder: path of the folder where to save the file
    :return: returns the file_path of the saved json file
    """
    if not os.path.isdir(data_folder):
        raise NotADirectoryError()

    filename = _gen_filename(content)

    file_path = os.path.join(data_folder, filename)
    with open(file_path, "w") as out:
        out.write(content)

    return file_path


def save_to_local_zip(content, zip_path="zip.zip"):
    """
    Saves the content to a json file inside a zipfile generating a filename based on the date of the content

    :param content: content to save to the json file
    :param zip_path: path of the zipfile where to save the file
    :return: returns the filename inside the zipfile
    """
    filename = _gen_filename(content)

    with zipfile.ZipFile(zip_path, "a") as myZipFile:
        myZipFile.writestr(filename, content, zipfile.ZIP_DEFLATED)

    return filename


def append_price_report(content, report_file):
    """
    Extract relevant information from content and append it to a csv file

    :param content: raw prices data content
    :param datetime_price_report: date of the price report
    :param report_file: report file used to collect all reports
    :return: None
    """

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
            "probability_price_up_percentage": int(
                asset['current_price_change_info']['probability_price_up_percentage']),
            "probability_price_down_percentage": int(
                asset['current_price_change_info']['probability_price_down_percentage']),
            "current_selection_percentage": int(asset['current_price_change_info']["current_selection_percentage"])
        }

    data = json.loads(content)
    assets = [extract_asset_info(asset) for asset in data['players']]

    report = pd.DataFrame(assets) \
        .set_index("id")

    report["datetime"] = data["datetime"]

    report.to_csv(report_file, mode='a', header=not os.path.isfile(report_file))

