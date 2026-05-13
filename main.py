import pandas as pd
from sqlalchemy import create_engine

# postgresql+psycopg2://пользователь:пароль@хост:порт/имя_базы
db_url = 'postgresql+psycopg2://postgres:@localhost:5432/shopkz_db'

# Создаем "движок" подключения. Он сам будет управлять сессиями.
engine = create_engine(db_url)

# 2. ВЫГРУЗКА ДАННЫХ ИЗ БАЗЫ
# Нам нужны только дата и сумма для базовой динамики
query = """
    SELECT sale_date, total_amount
    FROM sales
    ORDER BY sale_date ASC;
"""

# pd.read_sql сама выполняет запрос и возвращает готовый DataFrame
df = pd.read_sql(query, engine)

# 3. ПОДГОТОВКА ДАННЫХ К TIME-SERIES АНАЛИЗУ
# Убеждаемся, что колонка с датой имеет правильный тип datetime
df['sale_date'] = pd.to_datetime(df['sale_date'])

# Для динамики в pandas обязательно нужно сделать дату ИНДЕКСОМ (Index)
df.set_index(keys='sale_date', inplace=True)

# --- ДИНАМИКА 1: Ежедневная выручка ---
# Метод .resample('D') группирует данные по дням ('W' - неделя, 'M' - месяц).
# Метод .sum() суммирует чеки за этот день.
# Метод .fillna(0) ставит 0 в те дни, когда продаж вообще не было (чтобы график не рвался).
daily_sales = df['total_amount'].resample('D').sum().fillna(0)

print("--- 1. Дневная выручка (последние 5 дней) ---")
print(daily_sales.tail(5))
print("\n")

# --- ДИНАМИКА 2: Накопительная выручка (Cumulative Sum) ---
# Метод .cumsum() прибавляет выручку текущего дня ко всем предыдущим.
# Идеально для отслеживания выполнения планов продаж.
cumulative_sales = daily_sales.cumsum()

print("--- 2. Накопительная выручка (последние 5 дней) ---")
print(cumulative_sales.tail(5))
print("\n")

# --- ДИНАМИКА 3: Скользящее среднее за 7 дней (Rolling Average) ---
# Метод .rolling(window=7) берет "окно" из 7 последних дней.
# Метод .mean() считает их среднее арифметическое.
# Это убирает шум выходных дней и показывает реальный тренд продаж.
rolling_avg_7d = daily_sales.rolling(window=7).mean().fillna(0)

print("--- 3. Скользящее среднее за 7 дней (последние 5 дней) ---")
print(rolling_avg_7d.tail(5))
print("\n")

# ===============================================
# 5. СБОРКА В ЕДИНЫЙ DATAFRAME (для экспорта)
# ===============================================

# Собираем все три динамики в одну красивую таблицу
analytics_df = pd.DataFrame({
    'Дневная выручка': daily_sales,
    'Накопительный итог': cumulative_sales,
    'Тренд (7 дней)': rolling_avg_7d
})

# Округляем до двух знаков после запятой для красоты
analytics_df = analytics_df.round(2)

print("--- ИТОГОВАЯ ТАБЛИЦА ДИНАМИКИ (фрагмент) ---")
print(analytics_df.tail(10))

# analytics_df.to_excel('sales_dynamics.xlsx')