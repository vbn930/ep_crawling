import EP_crawler
from manager import log_manager
from manager import file_manager as FM
import datetime

# pyinstaller -n "Evotech-Preformance Crawler ver1.0" --clean --onefile main.py

global log_level
log_level = log_manager.LogType.DEBUG
logger = log_manager.Logger(log_level)
crawler = EP_crawler.Evotech_Crawler(logger)

crawler.start_category_crawling()

end_msg = input("프로그램을 종료하시려면 엔터키를 눌러주세요.")