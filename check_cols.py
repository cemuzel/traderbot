from tefas import Crawler
from datetime import datetime

def check_columns():
    try:
        crawler = Crawler()
        date = datetime.now().strftime("%Y-%m-%d")
        # columns argumanini vermeden cekelim
        result = crawler.fetch(start=date, end=date)
        print("ALL COLUMNS:", list(result.columns))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()
