import logging
import os
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union
import pandas as pd  # type: ignore


def default_report(content: str) -> pd.DataFrame:

    def extract_asset_info(asset: Any) -> Dict[str, Union[str, int, float]]:
        """
        Extracts relevant information for each asset

        :param asset: asset object to extract information
        :return: dictionary with the relevant asset information
        """

        return {
            "id": int(asset['id']),
            "name": asset['display_name'],
            "price": float(asset['price']),
            # "probability_price_up_percentage": int(
            #    asset['current_price_change_info']['probability_price_up_percentage']),
            # "probability_price_down_percentage": int(
            #    asset['current_price_change_info']['probability_price_down_percentage']),
            # "selection_percentage": int(asset['current_price_change_info']["current_selection_percentage"]),
        }

    data = json.loads(content)
    assets = [extract_asset_info(asset) for asset in data['players']]
    report = pd.DataFrame(assets).set_index("id")
    now = datetime.now()
    report["datetime"] = now.strftime("%Y-%m-%d %H:%M:%S")
    report["timestamp"] = int(now.timestamp())

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

    logging.info(f"Saved prices to csv file: {report_file}")