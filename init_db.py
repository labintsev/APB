import sqlite3
import json

# Create database connection
conn = sqlite3.connect('instance/broadcasts.db')
cursor = conn.cursor()

# Create all tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS region (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL, 
        rating REAL default 1.0
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS district (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        population INTEGER,
        region_id INTEGER NOT NULL,
        FOREIGN KEY (region_id) REFERENCES region (id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS smi (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        rating REAL default 1.0,
        male REAL default 0.5
    )
''')

cursor.execute('''
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
''')

cursor.execute('''
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
''')

# Insert regions from the provided data
regions_data = [
    {"id": 0, "name": "Россия", "rating": 1.0},
    {"id": 1, "name": "Республика Адыгея", "rating": 1.0},
    {"id": 2, "name": "Республика Башкортостан", "rating": 1.0},
    {"id": 3, "name": "Республика Бурятия", "rating": 1.0},
    {"id": 4, "name": "Республика Алтай", "rating": 1.0},
    {"id": 5, "name": "Республика Дагестан", "rating": 1.0},
    {"id": 6, "name": "Республика Ингушетия", "rating": 1.0},
    {"id": 7, "name": "Кабардино‑Балкарская Республика", "rating": 1.0},
    {"id": 8, "name": "Республика Калмыкия", "rating": 1.0},
    {"id": 9, "name": "Карачаево‑Черкесская Республика", "rating": 1.0},
    {"id": 10, "name": "Республика Карелия", "rating": 1.0},
    {"id": 11, "name": "Республика Коми", "rating": 1.0},
    {"id": 12, "name": "Республика Марий Эл", "rating": 1.0},
    {"id": 13, "name": "Республика Мордовия", "rating": 1.0},
    {"id": 14, "name": "Республика Саха (Якутия)", "rating": 1.0},
    {"id": 15, "name": "Республика Северная Осетия — Алания", "rating": 1.0},
    {"id": 16, "name": "Республика Татарстан", "rating": 1.0},
    {"id": 17, "name": "Республика Тыва", "rating": 1.0},
    {"id": 18, "name": "Удмуртская Республика", "rating": 1.0},
    {"id": 19, "name": "Республика Хакасия", "rating": 1.0},
    {"id": 20, "name": "Чувашская Республика", "rating": 1.0},
    {"id": 21, "name": "Чеченская Республика", "rating": 1.0},
    {"id": 22, "name": "Алтайский край", "rating": 1.0},
    {"id": 23, "name": "Краснодарский край", "rating": 1.0},
    {"id": 24, "name": "Красноярский край", "rating": 1.0},
    {"id": 25, "name": "Приморский край", "rating": 1.0},
    {"id": 26, "name": "Ставропольский край", "rating": 1.0},
    {"id": 27, "name": "Хабаровский край", "rating": 1.0},
    {"id": 28, "name": "Амурская область", "rating": 1.0},
    {"id": 29, "name": "Архангельская область", "rating": 1.0},
    {"id": 30, "name": "Астраханская область", "rating": 1.0},
    {"id": 31, "name": "Белгородская область", "rating": 1.0},
    {"id": 32, "name": "Брянская область", "rating": 1.0},
    {"id": 33, "name": "Владимирская область", "rating": 1.0},
    {"id": 34, "name": "Волгоградская область", "rating": 1.0},
    {"id": 35, "name": "Вологодская область", "rating": 1.0},
    {"id": 36, "name": "Воронежская область", "rating": 1.0},
    {"id": 37, "name": "Ивановская область", "rating": 1.0},
    {"id": 38, "name": "Иркутская область", "rating": 1.0},
    {"id": 39, "name": "Калининградская область", "rating": 1.0},
    {"id": 40, "name": "Калужская область", "rating": 1.0},
    {"id": 41, "name": "Камчатский край", "rating": 1.0},
    {"id": 42, "name": "Кемеровская область — Кузбасс", "rating": 1.0},
    {"id": 43, "name": "Кировская область", "rating": 1.0},
    {"id": 44, "name": "Костромская область", "rating": 1.0},
    {"id": 45, "name": "Курганская область", "rating": 1.0},
    {"id": 46, "name": "Курская область", "rating": 1.0},
    {"id": 47, "name": "Ленинградская область", "rating": 1.0},
    {"id": 48, "name": "Липецкая область", "rating": 1.0},
    {"id": 49, "name": "Магаданская область", "rating": 1.0},
    {"id": 50, "name": "Московская область", "rating": 1.0},
    {"id": 51, "name": "Мурманская область", "rating": 1.0},
    {"id": 52, "name": "Нижегородская область", "rating": 1.0},
    {"id": 53, "name": "Новгородская область", "rating": 1.0},
    {"id": 54, "name": "Новосибирская область", "rating": 1.0},
    {"id": 55, "name": "Омская область", "rating": 1.0},
    {"id": 56, "name": "Оренбургская область", "rating": 1.0},
    {"id": 57, "name": "Орловская область", "rating": 1.0},
    {"id": 58, "name": "Пензенская область", "rating": 1.0},
    {"id": 59, "name": "Пермский край", "rating": 1.0},
    {"id": 60, "name": "Псковская область", "rating": 1.0},
    {"id": 61, "name": "Ростовская область", "rating": 1.0},
    {"id": 62, "name": "Рязанская область", "rating": 1.0},
    {"id": 63, "name": "Самарская область", "rating": 1.0},
    {"id": 64, "name": "Саратовская область", "rating": 1.0},
    {"id": 65, "name": "Сахалинская область", "rating": 1.0},
    {"id": 66, "name": "Свердловская область", "rating": 1.0},
    {"id": 67, "name": "Смоленская область", "rating": 1.0},
    {"id": 68, "name": "Тамбовская область", "rating": 1.0},
    {"id": 69, "name": "Тверская область", "rating": 1.0},
    {"id": 70, "name": "Томская область", "rating": 1.0},
    {"id": 71, "name": "Тульская область", "rating": 1.0},
    {"id": 72, "name": "Тюменская область", "rating": 1.0},
    {"id": 73, "name": "Ульяновская область", "rating": 1.0},
    {"id": 74, "name": "Челябинская область", "rating": 1.0},
    {"id": 75, "name": "Забайкальский край", "rating": 1.0},
    {"id": 76, "name": "Ярославская область", "rating": 1.0},
    {"id": 77, "name": "Город Москва", "rating": 1.0},
    {"id": 78, "name": "Город Санкт‑Петербург", "rating": 1.0},
    {"id": 79, "name": "Еврейская автономная область", "rating": 1.0},
    {"id": 80, "name": "Ненецкий автономный округ", "rating": 1.0},
    {"id": 81, "name": "Ханты‑Мансийский автономный округ — Югра", "rating": 1.0},
    {"id": 82, "name": "Чукотский автономный округ", "rating": 1.0},
    {"id": 83, "name": "Ямало‑Ненецкий автономный округ", "rating": 1.0},
    {"id": 84, "name": "Республика Крым", "rating": 1.0},
    {"id": 85, "name": "Город Севастополь", "rating": 1.0},
    {"id": 86, "name": "Автономная Республика Крым", "rating": 1.0}
]

# Insert regions into the database
for region in regions_data:
    cursor.execute("INSERT OR REPLACE INTO region (id, name) VALUES (?, ?)", 
                    (region["id"], region["name"]))

print("Tables created and regions inserted successfully!")
conn.commit()
conn.close()
