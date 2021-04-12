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
        os.mkdir(data_folder)

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

        price_delta_race = round(float(asset["weekly_price_change"]), 1)
        # some requests have sent this field as the team price instead of 0
        if price_delta_race == starting_price:
            price_delta_race = 0

        # These initial percentages are not 100% certain, found it in f1 fantasy tracker discord
        INITIAL_PCT = {
            29 : 5,      # N. Mazepin
            26 : 15,     # K. Raikkonen
            4  : 12,     # Mercedes
            3  : 30,     # McLaren
            6  : 3,      # Alpine
            5  : 30,     # Red Bull
            25 : 26,     # Y. Tsunoda
            19 : 19,     # S. Vettel
            23 : 27,     # C. Sainz
            24 : 42,     # P. Gasly
            8  : 1,      # Alfa Romeo
            14 : 50,     # M. Verstappen
            22 : 27,     # C. Leclerc
            18 : 11,     # L. Stroll
            2  : 1,      # Williams
            20 : 17,     # E. Ocon
            17 : 39,     # D. Ricciardo
            16 : 51,     # L. Norris
            15 : 32,     # S. Perez
            27 : 8,      # A. Giovinazzi
            30 : 42,     # G. Russell
            21 : 14,     # F. Alonso
            1  : 8,      # Ferrari
            12 : 29,     # L. Hamilton
            10 : 1,      # Haas
            31 : 4,      # N. Latifi
            28 : 27,     # M. Schumacher
            9  : 8,      # Aston Martin
            7  : 6,      # AlphaTauri
            13 : 13,     # V. Bottas
         }
        starting_selection_percentage = INITIAL_PCT[asset['id']]

        return {
            "id": int(asset['id']),
            "name": asset['display_name'],
            "price": float(asset['price']),
            "price_delta_start": round(float(asset['price']) - float(starting_price), 1),
            "price_delta_race": price_delta_race,
            "probability_price_up_percentage": int(
                asset['current_price_change_info']['probability_price_up_percentage']),
            "probability_price_down_percentage": int(
                asset['current_price_change_info']['probability_price_down_percentage']),
            "current_selection_percentage": int(asset['current_price_change_info']["current_selection_percentage"]),
            "current_selection_percentage_delta":
                int(asset['current_price_change_info']["current_selection_percentage"]) - starting_selection_percentage

        }

    data = json.loads(content)
    assets = [extract_asset_info(asset) for asset in data['players']]

    report = pd.DataFrame(assets) \
        .set_index("id")

    report["datetime"] = data["datetime"]

    report.to_csv(report_file, mode='a', header=not os.path.isfile(report_file))

