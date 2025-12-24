import sqlite3
import json

# Create database connection
conn = sqlite3.connect("instance/broadcasts.db")
cursor = conn.cursor()

# Create all tables
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS region (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL, 
        rating REAL default 1.0
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS district (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        population INTEGER,
        region_id INTEGER NOT NULL,
        FOREIGN KEY (region_id) REFERENCES region (id)
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS smi (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        rating REAL default 1.0,
        male REAL default 0.5
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS organisation (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        inn TEXT,
        kpp TEXT,
        ogrn TEXT,
        address TEXT,
        phone TEXT,
        email TEXT,
        arv_member BOOLEAN
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS broadcast (
        id INTEGER PRIMARY KEY,
        org_id INTEGER NOT NULL,
        smi_id INTEGER,
        district_id INTEGER NOT NULL,
        region_id INTEGER,
        frequency VARCHAR(50),
        power REAL,
        FOREIGN KEY (org_id) REFERENCES organisation (id),
        FOREIGN KEY (smi_id) REFERENCES smi (id),
        FOREIGN KEY (district_id) REFERENCES district (id),
        FOREIGN KEY (region_id) REFERENCES region (id)
    )
"""
)

# Regions provided ratings
regions_data = [
    {"id": 0, "name": "Россия", "rating": 1.0},
    {"id": 1, "name": "Республика Адыгея", "rating": 0.4},
    {"id": 2, "name": "Республика Башкортостан", "rating": 0.5},
    {"id": 3, "name": "Республика Бурятия", "rating": 0.4},
    {"id": 4, "name": "Республика Алтай", "rating": 0.4},
    {"id": 5, "name": "Республика Дагестан", "rating": 0.3},
    {"id": 6, "name": "Республика Ингушетия", "rating": 0.3},
    {"id": 7, "name": "Кабардино‑Балкарская Республика", "rating": 0.3},
    {"id": 8, "name": "Республика Калмыкия", "rating": 0.3},
    {"id": 9, "name": "Карачаево‑Черкесская Республика", "rating": 0.3},
    {"id": 10, "name": "Республика Карелия", "rating": 0.4},
    {"id": 11, "name": "Республика Коми", "rating": 0.4},
    {"id": 12, "name": "Республика Марий Эл", "rating": 0.35},
    {"id": 13, "name": "Республика Мордовия", "rating": 0.5},
    {"id": 14, "name": "Республика Саха (Якутия)", "rating": 0.3},
    {"id": 15, "name": "Республика Северная Осетия — Алания", "rating": 0.3},
    {"id": 16, "name": "Республика Татарстан", "rating": 1.5},
    {"id": 17, "name": "Республика Тыва", "rating": 0.25},
    {"id": 18, "name": "Удмуртская Республика", "rating": 0.4},
    {"id": 19, "name": "Республика Хакасия", "rating": 0.5},
    {"id": 20, "name": "Чувашская Республика", "rating": 0.5},
    {"id": 21, "name": "Чеченская Республика", "rating": 0.35},
    {"id": 22, "name": "Алтайский край", "rating": 0.5},
    {"id": 23, "name": "Краснодарский край", "rating": 0.7},
    {"id": 24, "name": "Красноярский край", "rating": 0.6},
    {"id": 25, "name": "Приморский край", "rating": 0.7},
    {"id": 26, "name": "Ставропольский край", "rating": 0.5},
    {"id": 27, "name": "Хабаровский край", "rating": 0.4},
    {"id": 28, "name": "Амурская область", "rating": 0.3},
    {"id": 29, "name": "Архангельская область", "rating": 0.6},
    {"id": 30, "name": "Астраханская область", "rating": 0.4},
    {"id": 31, "name": "Белгородская область", "rating": 0.5},
    {"id": 32, "name": "Брянская область", "rating": 0.6},
    {"id": 33, "name": "Владимирская область", "rating": 0.5},
    {"id": 34, "name": "Волгоградская область", "rating": 0.5},
    {"id": 35, "name": "Вологодская область", "rating": 0.5},
    {"id": 36, "name": "Воронежская область", "rating": 0.5},
    {"id": 37, "name": "Ивановская область", "rating": 0.5},
    {"id": 38, "name": "Иркутская область", "rating": 0.4},
    {"id": 39, "name": "Калининградская область", "rating": 0.7},
    {"id": 40, "name": "Калужская область", "rating": 0.5},
    {"id": 41, "name": "Камчатский край", "rating": 0.25},
    {"id": 42, "name": "Кемеровская область — Кузбасс", "rating": 0.5},
    {"id": 43, "name": "Кировская область", "rating": 0.6},
    {"id": 44, "name": "Костромская область", "rating": 0.5},
    {"id": 45, "name": "Курганская область", "rating": 0.35},
    {"id": 46, "name": "Курская область", "rating": 0.5},
    {"id": 47, "name": "Ленинградская область", "rating": 0.7},
    {"id": 48, "name": "Липецкая область", "rating": 0.5},
    {"id": 49, "name": "Магаданская область", "rating": 1.5},
    {"id": 50, "name": "Московская область", "rating": 1.5},
    {"id": 51, "name": "Мурманская область", "rating": 0.35},
    {"id": 52, "name": "Нижегородская область", "rating": 0.7},
    {"id": 53, "name": "Новгородская область", "rating": 0.5},
    {"id": 54, "name": "Новосибирская область", "rating": 0.5},
    {"id": 55, "name": "Омская область", "rating": 0.5},
    {"id": 56, "name": "Оренбургская область", "rating": 0.4},
    {"id": 57, "name": "Орловская область", "rating": 0.5},
    {"id": 58, "name": "Пензенская область", "rating": 0.4},
    {"id": 59, "name": "Пермский край", "rating": 0.7},
    {"id": 60, "name": "Псковская область", "rating": 0.5},
    {"id": 61, "name": "Ростовская область", "rating": 0.5},
    {"id": 62, "name": "Рязанская область", "rating": 0.5},
    {"id": 63, "name": "Самарская область", "rating": 0.5},
    {"id": 64, "name": "Саратовская область", "rating": 0.4},
    {"id": 65, "name": "Сахалинская область", "rating": 1.5},
    {"id": 66, "name": "Свердловская область", "rating": 0.7},
    {"id": 67, "name": "Смоленская область", "rating": 0.5},
    {"id": 68, "name": "Тамбовская область", "rating": 0.4},
    {"id": 69, "name": "Тверская область", "rating": 0.5},
    {"id": 70, "name": "Томская область", "rating": 0.5},
    {"id": 71, "name": "Тульская область", "rating": 0.5},
    {"id": 72, "name": "Тюменская область", "rating": 0.7},
    {"id": 73, "name": "Ульяновская область", "rating": 0.5},
    {"id": 74, "name": "Челябинская область", "rating": 0.7},
    {"id": 75, "name": "Забайкальский край", "rating": 0.6},
    {"id": 76, "name": "Ярославская область", "rating": 0.5},
    {"id": 77, "name": "Город Москва", "rating": 2.0},
    {"id": 78, "name": "Город Санкт‑Петербург", "rating": 2.0},
    {"id": 79, "name": "Еврейская автономная область", "rating": 0.35},
    {"id": 80, "name": "Ненецкий автономный округ", "rating": 0.4},
    {"id": 81, "name": "Ханты‑Мансийский автономный округ — Югра", "rating": 0.7},
    {"id": 82, "name": "Чукотский автономный округ", "rating": 0.25},
    {"id": 83, "name": "Ямало‑Ненецкий автономный округ", "rating": 1.5},
    {"id": 84, "name": "Республика Крым", "rating": 0.6},
    {"id": 85, "name": "Город Севастополь", "rating": 0.6},
    {"id": 86, "name": "Автономная Республика Крым", "rating": 0.6},
]

# Update regions ratings into the database
for region in regions_data:
    region_id = region['id']
    region_name = region['name']
    region_rating = region['rating']
    cursor.execute("UPDATE region SET rating = ? WHERE id = ?", (region_rating, region_id))

# Commit the changes and close the connection
print("Tables created and regions inserted successfully!")
conn.commit()
conn.close()
