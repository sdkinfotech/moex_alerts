import requests
import psycopg2
import sys
import json
from datetime import datetime
import os

class MoexPriceTQBR:
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
            # Loading data from the JSON file
            with open('latest_prices.json', 'r', encoding='utf-8') as json_file:
                self.latest_data = json.load(json_file)
            
            # Checking for the presence of data
            if self.latest_data:
                # Getting the time of the last record from the JSON file
                last_updated = datetime.fromtimestamp(os.path.getmtime('latest_prices.json'))
                self.log_message(
                    f"SHOW LATEST: Current information as of {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
                
                for security in self.latest_data:
                    ticker, price = security[0], security[1]
                    # print(f"Ticker: {ticker}, Price: {price}")
                    self.log_message(f"Ticker: {ticker}, Price: {price}")
            else:
                self.log_message("No data to display. The get_prices method was not run.")
        except Exception as e:
            self.log_message(f"Error reading data from the JSON file: {e}")

    def save_null_prices_percentage_to_db(self, null_price_percentage):
        # Подключаемся к базе данных
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

            # SQL запрос для вставки данных в таблицу
            insert_query = """
            INSERT INTO null_price_percent_metrics (calculation_date, calculation_time, percent_null_prices) 
            VALUES (%s, %s, %s);
            """
            # Текущая дата и время для регистрации в базе данных
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")

            # Выполнить запрос на вставку данных
            cursor.execute(insert_query, (current_date, current_time, null_price_percentage))

            # Подтвердить изменения
            conn.commit()
            self.log_message(f"Null price percentage data successfully added to the database - info")

        except Exception as e:
            self.log_message(f"Error saving null price percentage to database: {e} - error")

        finally:
            # Закрываем соединение с базой данных
            if conn:  # проверяем, что `conn` не равно `None`
                cursor.close()
                conn.close()

    # Теперь нужно вызвать этот метод в конце метода `calculate_null_prices_percentage`:
    def calculate_null_prices_percentage(self):
        if not self.latest_data:
            self.log_message("No data to analyze. The get_prices method was not run. - error")
            return

        total_count = len(self.latest_data)
        null_price_count = sum(1 for item in self.latest_data if item[1] is None)

        # Вычисление процента значений null
        null_price_percentage = (null_price_count / total_count) * 100 if total_count else 0

        # Запись результата в лог
        self.log_message(f"Percent of tickers with null price: {null_price_percentage:.2f}% - info")

        # Сохраняем результат в базе данных
        self.save_null_prices_percentage_to_db(null_price_percentage)