import requests
import psycopg2
import sys
import json
from datetime import datetime
import os

class MoexPriceTQBR:
    """
    __init__: 
    инициализирует экземпляр класса с переданными 
    параметрами для доступа к базе данных и файлу лога.

    log_message: 
    логирует сообщения, принимая строку сообщения 
    и записывая его в файл лога с временной меткой.

    get_prices: 
    запрашивает данные о котировках 
    с Московской биржи и сохраняет их как JSON.

    update_db: 
    обновляет базу данных, вставляя 
    полученные данные о ценах.

    show_prices: 
    читает данные из файла JSON и логирует 
    информацию о текущих ценах акций.

    save_null_prices_percentage_to_db: 
    сохраняет рассчитанный процент нулевых цен в базу данных.

    calculate_null_prices_percentage: 
    рассчитывает процент нулевых цен на основе 
    полученных данных и вызывает метод сохранения в базе данных.
    """

    def __init__(self, dbname, user, password, host, port, logfile='log.txt'):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.logfile = logfile
        self.latest_data = None

    def log_message(self, message):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{current_time}] moex_price_tqbr {message}"
        print(log_entry)
        with open(self.logfile, "a", encoding='utf-8') as f:
            f.write(log_entry + "\n")

    def get_prices(self):
        self.log_message("Requesting prices for the TQBR class...")
        try:
            response = requests.get('http://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json', params={
                'iss.meta': 'off',
                'iss.only': 'marketdata',
                'marketdata.columns': 'SECID,LAST'
            })
            response.raise_for_status()
            self.latest_data = response.json()['marketdata']['data']
            self.log_message("TQBR data successfully received.")
            # Writing data to JSON file
            with open('latest_prices.json', 'w', encoding='utf-8') as json_file:
                json.dump(self.latest_data, json_file)
            self.log_message("TQBR data saved to latest_prices.json.")
        except Exception as e:
            self.log_message(f"Error retrieving TQBR data: {e}")
            sys.exit(1)

    def update_db(self):
        self.log_message("Updating the database...")
        if self.latest_data:
            try:
                conn = psycopg2.connect(
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port
                )
                cursor = conn.cursor()

                insert_query = """
                INSERT INTO TQBR_prices (quote_date, quote_time, ticker, price)
                VALUES (%s, %s, %s, %s);
                """
                now = datetime.now()
                current_date = now.date()
                current_time = now.time()

                for security in self.latest_data:
                    ticker, price = security[0], security[1]
                    cursor.execute(insert_query, (current_date, current_time, ticker, price))

                conn.commit()
                self.log_message("Data for the TQBR class successfully added to the database.")
            except Exception as e:
                self.log_message(f"Error updating the database: {e}")
            finally:
                cursor.close()
                conn.close()
        else:
            self.log_message("No data to update the database, the get_prices method was not run before the update.")

    def show_prices(self):
        try:
            with open('latest_prices.json', 'r', encoding='utf-8') as json_file:
                self.latest_data = json.load(json_file)
            
            if self.latest_data:

                last_updated = datetime.fromtimestamp(os.path.getmtime('latest_prices.json'))
                self.log_message(
                    f"SHOW LATEST: Current information as of {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
                
                for security in self.latest_data:
                    ticker, price = security[0], security[1]
                    self.log_message(f"Ticker: {ticker}, Price: {price}")
            else:
                self.log_message("No data to display. The get_prices method was not run.")
        except Exception as e:
            self.log_message(f"Error reading data from the JSON file: {e}")

    def save_null_prices_percentage_to_db(self, null_price_percentage):

        conn = None
        try:
            conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            cursor = conn.cursor()

            insert_query = """
            INSERT INTO null_price_percent_metrics (calculation_date, calculation_time, percent_null_prices) 
            VALUES (%s, %s, %s);
            """
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")

            cursor.execute(insert_query, (current_date, current_time, null_price_percentage))

            conn.commit()
            self.log_message(f"Null price percentage data successfully added to the database - info")

        except Exception as e:
            self.log_message(f"Error saving null price percentage to database: {e} - error")

        finally:

            if conn:  
                cursor.close()
                conn.close()

    def calculate_null_prices_percentage(self):
        
        if not self.latest_data:
            self.log_message("No data to analyze. The get_prices method was not run. - error")
            return

        total_count = len(self.latest_data)
        null_price_count = sum(1 for item in self.latest_data if item[1] is None)
        null_price_percentage = (null_price_count / total_count) * 100 if total_count else 0
        self.log_message(f"Percent of tickers with null price: {null_price_percentage:.2f}% - info")
        self.save_null_prices_percentage_to_db(null_price_percentage)