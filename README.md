# F1FantasyScraper

![](https://img.shields.io/badge/Maintained%3F-yes-green.svg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![typechecking-and-linting](https://github.com/EduardoFAFernandes/F1FantasyScraper/actions/workflows/typecheking-and-linting.yaml/badge.svg)](https://github.com/EduardoFAFernandes/F1FantasyScraper/actions/workflows/typecheking-and-linting.yaml)

The main focus of this project is to track F1 fantasy game prices.
If you are interested in only the data visit 
https://github.com/EduardoFAFernandes/F1FantasyData

This program can request price data to F1Fantasy and save it as a CSV.

## Installation

To run the project on your machine you will need to:
 - Install python 3
 - Clone the repository
 - Run `pip install -r requirements.txt`
With this default configuration will run.


## Run the program

After installation simply run `python scrapper.py`
This will fetch the data and save it in a file named `prices.csv` in the 
working directory. If you want the program to fetch the data in a constant 
interval you need one additional parameter `-dt, --delta-time` for example:
`python scrapper.py -dt 30` will keep the program running and will fetch the 
data every 30 minutes. More information in the Usage section.
 
## Usage

Bellow you can see the help command being run.

```
usage: scraper.py [-h] [--delta-time DELTA_TIME]
                  [--unit-time {m,minutes,h,hours}]
                  [--logging-level {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG}]
                  [--logging-file LOGGING_FILE] [--report-file REPORT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --delta-time DELTA_TIME, -dt DELTA_TIME
                        interval of time in unitTime between updates (default:
                        -)
  --unit-time {m,minutes,h,hours}, -ut {m,minutes,h,hours}
                        unit of time to use with deltaTime (default:
                        'minutes')
  --logging-level {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG}, -ll {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG}
                        logging level to use (default: 'INFO')
  --logging-file LOGGING_FILE, -lf LOGGING_FILE
                        file to save the logs (default: -)
  --report-file REPORT_FILE, -rf REPORT_FILE
                        file to save the data in a smaller format (default:
                        'prices.csv')

```
