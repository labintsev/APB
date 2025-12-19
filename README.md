# Калькулятор покрытия радиорекламой 

## Описание проекта 

 The project appears to be a Flask web application with database functionality for managing broadcast targets organized by regions, districts, and organizations, with a web interface that includes HTML templates and static assets (CSS, JS, images).
 The app uses SQLite for data storage and has a database schema defined in target_schema.sql.

  Root Directory:

  - .gitignore - Git ignore file
  - app.py - Main application file
  - models.py - Database models
  - requirements.txt - Python dependencies
  - static/ - Static files (CSS, JS, images)
  - templates/ - HTML templates

  Key files:
  - app.py - Main application logic 
  - models.py - Database models 
  - requirements.txt - Dependencies 

  Directories:
  - static/ - Contains CSS, JS, and image files
  - templates/ - HTML template files for the web interface


## Запуск проекта

```sh
gunicorn --bind=0.0.0.0:8000 "app:app"
```

## Функциональные требования для реализации на Flask + HTML + JS + CSS

Несколько организаций осуществляют покрытие радио в определенных регионах и районах несколькими СМИ. 
Нужно вычислить среднюю месячную стоимость рекламы для каждой организации. 
На главной странице отображать список регионов с возможностью прочитать какие сми вещают в каждом регионе. 

### **FR1: Архитектура и технологии**
*   **FR1.1:** Серверная часть реализуется на **Flask 3.x**, использует **SQLAlchemy ORM** для работы с SQLite.
*   **FR1.2:** Фронтенд - чистая **HTML5, CSS3, JavaScript (ES6+)** без тяжелых фреймворков.
*   **FR1.3:** Для таблиц использовать **DataTables.js** или аналогичную библиотеку для сортировки, поиска и пагинации.
*   **FR1.4:** Для графиков использовать **Chart.js** или аналогичную легковесную библиотеку.
*   **FR1.5:** Для запросов AJAX использовать **Fetch API** или **Axios**.
*   **FR1.6:** Для форм использовать нативные HTML5 элементы с валидацией + Flask-WTF (опционально).

### **FR2: Структура базы данных и модели**
*   **FR2.1:** Реализовать все таблицы из схемы как SQLAlchemy модели в `models.py`.
*   **FR2.2:** Добавить отношения между моделями:
    ```python
    # Пример для модели Broadcast
    organisation = relationship('Organisation', back_populates='broadcasts')
    district = relationship('District', back_populates='broadcasts')
    smi = relationship('Smi', back_populates='broadcasts')
    ```
*   **FR2.3:** Создать скрипт инициализации БД (`init_db.py`) с тестовыми данными для демонстрации.

### **FR3: Маршруты Flask (routes)**
*   **FR3.1:** Главная страница:
    ```
    GET / - отображает список регионов с возможностью раскрытия СМИ
    ```
*   **FR3.2:** API для получения данных:
    ```
    GET /api/regions - JSON всех регионов с суммарным населением
    GET /api/region/<int:id>/smi - JSON СМИ для конкретного региона
    GET /api/organisations - JSON всех организаций
    GET /api/calculation/<int:org_id> - JSON расчета стоимости для организации
    ```
*   **FR3.3:** Страницы CRUD:
    ```
    GET     /org_list                          # Список всех организаций
    GET     /organisation/<int:org_id>         # Детальная информация об организации
    GET     /organisation/create               # Форма создания новой организации
    POST    /organisation/create               # Обработка создания организации
    GET     /organisation/<int:id>/update      # Форма редактирования организации
    POST    /organisation/<int:id>/update      # Обработка обновления организации
    POST    /organisation/<int:id>/delete      # Удаление организации

    GET     /smi_list                          # Список всех СМИ
    GET     /smi/<int:smi_id>                  # Детальная информация о СМИ
    GET     /smi/create                        # Форма создания нового СМИ
    POST    /smi/create                        # Обработка создания СМИ
    GET     /smi/<int:id>/edit                 # Форма редактирования СМИ
    POST    /smi/<int:id>/update               # Обработка обновления СМИ
    POST    /smi/<int:id>/delete               # Удаление СМИ
    GET     /smi/<int:id>/broadcasts           # Список районов вещания данного СМИ

    GET     /district                          # Список всех районов
    GET     /district/<int:dis_id>             # Детальная информация о районе
    GET     /district/create                   # Форма создания нового района
    POST    /district/create                   # Обработка создания района
    GET     /district/<int:id>/edit            # Форма редактирования района
    POST    /district/<int:id>/update          # Обработка обновления района
    POST    /district/<int:id>/delete          # Удаление района

    GET     /district/<int:id>/broadcasts      # Список вещаний СМИ в районе
    GET     /api/districts/by-region/<int:region_id>  # API: Районы по региону (JSON)


    POST    /broadcast/create                  # Обработка создания вещания
    GET     /broadcast/<int:id>/update         # Форма редактирования вещания
    POST    /broadcast/<int:id>/update         # Обработка обновления вещания
    POST    /broadcast/<int:id>/delete         # Удаление вещания
    GET     /broadcast/filter                  # Фильтр вещаний по параметрам
    POST    /api/broadcast/calculate           # API: Расчет стоимости вещания

    ```

