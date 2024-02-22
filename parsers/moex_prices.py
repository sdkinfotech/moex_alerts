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

        """
        вызываем этот метод когда требуется записать лог
        в аргументы передается строка, которую нужно записать. 
        """

        # Получение текущего времени и форматирование его для вывода в лог
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Создание записи лога с временем и сообщением, переданным в метод
        log_entry = f"[{current_time}] moex_price_tqbr {message}"

        # Вывод записи лога в стандартный вывод (консоль)
        print(log_entry)

        # Открытие файла лога в режиме добавления ('a') и запись туда созданной записи лога
        with open(self.logfile, "a", encoding='utf-8') as f:
            # Добавление записи лога в файл и перевод строки для разделения записей
            f.write(log_entry + "\n")

    
    def get_prices(self):
       
        """
        Этот метод обращается к API Московской Биржи (MOEX) для получения маркетдаты
        Идем за маркетдатой в MOEX API 
        Выполненный запрос сохраняем в json
        """
        
        # Запись сообщения о начале запроса в лог
        self.log_message("Requesting prices for the TQBR class...")

        try:
            # Выполнение HTTP GET запроса к MOEX API для получения маркетдаты акций TQBR
            response = requests.get(
                'http://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json', 
                params={
                    'iss.meta': 'off',        # Отключение метаданных в ответе
                    'iss.only': 'marketdata', # Получение только данных рынка
                    'marketdata.columns': 'SECID,LAST' # Указание запрашиваемых колонок: идентификатор ценной бумаги и последняя цена
                }
            )
            
            # Проверка на ошибки HTTP в ответе
            response.raise_for_status()

            # Извлечение нужных данных из JSON-ответа
            self.latest_data = response.json()['marketdata']['data']

            # Запись сообщения об успешном получении данных в лог
            self.log_message("TQBR data successfully received.")
            
            # Сохранение полученных данных в локальный JSON-файл
            with open('latest_prices.json', 'w', encoding='utf-8') as json_file:
                json.dump(self.latest_data, json_file)

            # Запись сообщения о сохранении данных в файл в лог
            self.log_message("TQBR data saved to latest_prices.json.")
            
        except Exception as e:
            # Запись сообщения об ошибке при запросе данных в лог и завершение программы с ошибкой
            self.log_message(f"Error retrieving TQBR data: {e}")
            sys.exit(1)  # Завершение программы с кодом ошибки 1

    
    def update_db(self):
        
        """
        Метод для обновления базы ценовыми значениями TQBR тикеров, полученными через API
        вызывается когда требуется записать в базу то, что есть в json,
        который был получен при вызове метода get_prices()
        """

        # Запись в лог о начале процесса обновления БД
        self.log_message("Updating the database...")

        # Проверка, есть ли актуальные данные для записи в БД
        if self.latest_data:
            # Открытие блока try для перехвата исключений в процессе обновления БД
            try:
                # Установление соединения с БД
                conn = psycopg2.connect(
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port
                )
                # Создание объекта cursor для выполнения операций в БД
                cursor = conn.cursor()

                # SQL запрос для вставки данных
                insert_query = """
                INSERT INTO TQBR_prices (quote_date, quote_time, ticker, price)
                VALUES (%s, %s, %s, %s);
                """
                # Получение текущей даты и времени
                now = datetime.now()
                current_date = now.date()
                current_time = now.time()

                # Перебор последовательности данных и вставка каждой записи в БД
                for security in self.latest_data:
                    ticker, price = security[0], security[1]  # Извлечение данных о ценной бумаге
                    cursor.execute(insert_query, (current_date, current_time, ticker, price))  # Выполнение SQL запроса

                # Подтверждение транзакций в БД
                conn.commit()

                # Запись в лог о успешном добавлении данных в БД
                self.log_message("Data for the TQBR class successfully added to the database.")
            except Exception as e:
                # В случае неудачи запись в лог информации об ошибке
                self.log_message(f"Error updating the database: {e}")
            finally:
                # Закрытие курсора и соединения с БД в любом случае
                cursor.close()
                conn.close()
        else:
            # Если данных для обновления нет, запись соответствующего сообщения в лог
            self.log_message("No data to update the database, the get_prices method was not run before the update.")
    

    def show_prices(self):
        
        """
        метод для вывода информаци в консоль о тикерах 
        TQBR из json файла, вызывается после запроса get_prices()
        """

        # Блок try-catch, чтобы обработать возможные исключения при выполнении кода
        try:
            # Открытие файла 'latest_prices.json' в режиме чтения
            with open('latest_prices.json', 'r', encoding='utf-8') as json_file:
                # Загрузка данных из json-файла в переменную self.latest_data
                self.latest_data = json.load(json_file)
            
            # Проверка наличия данных в self.latest_data
            if self.latest_data:

                # Получение времени последнего изменения файла 'latest_prices.json'
                # и преобразование его в читаемый формат для вывода
                last_updated = datetime.fromtimestamp(os.path.getmtime('latest_prices.json'))
                self.log_message(
                    f"SHOW LATEST: Current information as of {last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Перебор всех записей в последних данных и логирование тикера и цены
                for security in self.latest_data:
                    ticker, price = security[0], security[1]  # Извлечение тикера и цены
                    self.log_message(f"Ticker: {ticker}, Price: {price}")  # Вывод тикера и цены в лог
            else:
                # Если данных нет, выводится сообщение о том, что get_prices не был выполнен
                self.log_message("No data to display. The get_prices method was not run.")
        except Exception as e:
            # Логирование исключения в случае ошибки при чтении файла
            self.log_message(f"Error reading data from the JSON file: {e}")
    
    
    def save_null_prices_percentage_to_db(self, null_price_percentage):
        
        """
        Метод для сохранения в базу данных процента записей с нулевой ценой
        сохраняет информацию, полученную при выполнении calculate_null_prices_percentage()
        """

        # Инициализация переменной соединения с базой данных
        conn = None
        try:
            # Установление соединения с базой данных
            conn = psycopg2.connect(
                dbname=self.dbname,  # Имя базы данных
                user=self.user,      # Имя пользователя
                password=self.password,  # Пароль
                host=self.host,      # Хост
                port=self.port       # Порт
            )
            # Создание курсора для выполнения операций с базой данных
            cursor = conn.cursor()

            # SQL запрос на вставку данных о проценте записей с нулевой ценой
            insert_query = """
            INSERT INTO null_price_percent_metrics (calculation_date, calculation_time, percent_null_prices) 
            VALUES (%s, %s, %s);
            """
            # Получение текущей даты и времени
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")  # Форматирование даты
            current_time = now.strftime("%H:%M:%S")  # Форматирование времени

            # Выполнение SQL команды с параметрами
            cursor.execute(insert_query, (current_date, current_time, null_price_percentage))

            # Подтверждение изменений в базе данных
            conn.commit()
            # Запись сообщения о успешном сохранении данных в лог
            self.log_message(f"Null price percentage data successfully added to the database - info")

        except Exception as e:
            # В случае возникновения ошибки записываем сообщение в лог
            self.log_message(f"Error saving null price percentage to database: {e} - error")

        finally:
            # В блоке finally гарантируем закрытие курсора и соединения с базой данных
            if conn:  # Проверяем, что соединение было установлено
                cursor.close()
                conn.close()
    
    def calculate_null_prices_percentage(self):
        
        """
        Метод для вычисления процента записей с нулевой ценой
        рассчитывает Null от всех значений price в TQBR
        и вызывает save_null_prices_percentage_to_db() для сохранения
        """
        
        # Проверка наличия данных для анализа
        if not self.latest_data:
            # Если данных нет, выводится сообщение об ошибке и метод завершается
            self.log_message("No data to analyze. The get_prices method was not run. - error")
            return  # Ранний выход из метода

        # Подсчет общего количества записей
        total_count = len(self.latest_data)

        # Подсчет количества записей со значением Null в цене
        null_price_count = sum(1 for item in self.latest_data if item[1] is None)

        # Расчет процента записей с Null ценой от общего количества
        # Если total_count не равен нулю, иначе процент равен 0
        null_price_percentage = (null_price_count / total_count) * 100 if total_count else 0

        # Запись рассчитанного процента в лог
        self.log_message(f"Percent of tickers with null price: {null_price_percentage:.2f}% - info")

        # Вызов метода для сохранения рассчитанного процента в базу данных
        self.save_null_prices_percentage_to_db(null_price_percentage)