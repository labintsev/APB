# Калькулятор покрытия радиорекламой 

## Описание проекта 

 The project appears to be a Flask web application with database functionality for managing broadcast targets organized by regions, districts, and organizations, with a web interface that includes HTML templates and static assets (CSS, JS, images).
 The app uses SQLite for data storage and has a database schema defined in target_schema.sql.

  Projtct structure:

  - adcalc/  - Main application directory
  -  | __init__.py - Application initialization and routes
  -   | region.py - Blueprint for region-related routes
  -   | org.py - Blueprint for organization-related routes
  -   | district.py - Blueprint for district-related routes
  -   | smi.py - Blueprint for SMI (likely a typo, should be 'broadcast') related routes
  -   | utils.py - Utility functions for cost calculation and other operations
  -   | db_schema.sql - Database schema definition
  -   | models.py - Database models
  -   | static/ - Static files (CSS, JS, images)
  -   | templates/ - HTML templates



## Запуск проекта

```sh
gunicorn --bind=0.0.0.0:8000 "adcalc:create_app()" --daemon
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
*   **FR1.6:** Для форм использовать нативные HTML5 элементы с валидацией (опционально).

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

Инструкция по применению
1. На вкладке Организации добавить организацию
2. Добавить СМИ на вкладке СМИ
3. Добавить район вещания на вкладке Район вещания
4. На вкладке Организации нажать на название организации
5. Создать новую трансляцию для организации, выбрав СМИ и район из списков, указать мощность и частоту при необходимости. 
6. Убедиться что список трансляций для организации соответствует ожиданиям.
7. Перейти на главную страницу (ссылка Ассоциация Радиовещателей в верхнем левом углу).
8. Ввести бюджет и нажать кнопку Рассчитать. 