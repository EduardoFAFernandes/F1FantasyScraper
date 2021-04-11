# F1FantasyScraper
The main focus of this project is to track f1 fantasy game.
The scripts saves the responses of the f1 fantasy api.
If you are interested in only the data visit ()[]

To run the project on your machine you will need to:
 - Install python 3
 - Clone the repository
 - Run `pip install -r requirements.txt`
 - Run `python scrapper.py`
 
 With this default configuration will run.
 
 You can also request help with the command by running 
 `python scrapper.py -h`
 
This is subject to change but for now this is the ouput:
 ```
usage: scraper.py [-h] [--delta-time DELTA_TIME]
                  [--unit-time {m,minutes,h,hours,s,seconds}]
                  [--data-folder DATA_FOLDER]
                  [--logging-level {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG}]
                  [--logging-file LOGGING_FILE] [--zip-file ZIP_FILE]
                  [--report-file REPORT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --delta-time DELTA_TIME, -dt DELTA_TIME
                        interval of time in unitTime between updates (default:
                        10)
  --unit-time {m,minutes,h,hours,s,seconds}, -ut {m,minutes,h,hours,s,seconds}
                        unit of time to use with deltaTime (default:
                        'minutes')
  --data-folder DATA_FOLDER, -df DATA_FOLDER
                        path to a folder where data will be stored (default:
                        'raw_data')
  --logging-level {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG}, -ll {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG}
                        logging level to use (default: 'INFO')
  --logging-file LOGGING_FILE, -lf LOGGING_FILE
                        file to save the logs (default: -)
  --zip-file ZIP_FILE, -zf ZIP_FILE
                        zipfile file where a backup of the data will be stored
                        (default: 'raw_data.zip')
  --report-file REPORT_FILE, -rf REPORT_FILE
                        file to save the data in a smaller format (default:
                        'prices.csv')
``` 
