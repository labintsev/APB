# Калькулятор покрытия радиорекламой
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

  The project appears to be a Flask web application with a database backend, using SQLite (based on the .db file and target_schema.sql) for storing broadcast targets. It has a web interface for managing broadcast targets organized by regions,
  districts, and organizations.


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
    GET     /organisation/<int:id>             # Детальная информация об организации
    GET     /organisation/create               # Форма создания новой организации
    POST    /organisation/create               # Обработка создания организации
    GET     /organisation/<int:id>/update      # Форма редактирования организации
    POST    /organisation/<int:id>/update      # Обработка обновления организации
    POST    /organisation/<int:id>/delete      # Удаление организации

    GET     /smi_list                          # Список всех СМИ
    GET     /smi/<int:id>                      # Детальная информация о СМИ
    GET     /smi/new                           # Форма создания нового СМИ
    POST    /smi/create                        # Обработка создания СМИ
    GET     /smi/<int:id>/edit                 # Форма редактирования СМИ
    POST    /smi/<int:id>/update               # Обработка обновления СМИ
    POST    /smi/<int:id>/delete               # Удаление СМИ
    GET     /smi/<int:id>/broadcasts           # Список вещаний данного СМИ

    GET     /district                          # Список всех районов
    GET     /district/<int:id>                 # Детальная информация о районе
    GET     /district/new                      # Форма создания нового района
    POST    /district/create                   # Обработка создания района
    GET     /district/<int:id>/edit            # Форма редактирования района
    POST    /district/<int:id>/update          # Обработка обновления района
    POST    /district/<int:id>/delete          # Удаление района
    GET     /district/<int:id>/broadcasts      # Список вещаний в районе
    GET     /api/districts/by-region/<int:region_id>  # API: Районы по региону (JSON)

    GET     /broadcast                         # Список всех вещаний
    GET     /broadcast/<int:id>                # Детальная информация о вещании
    GET     /broadcast/new                     # Форма создания нового вещания
    POST    /broadcast/create                  # Обработка создания вещания
    GET     /broadcast/<int:id>/edit           # Форма редактирования вещания
    POST    /broadcast/<int:id>/update         # Обработка обновления вещания
    POST    /broadcast/<int:id>/delete         # Удаление вещания
    GET     /broadcast/filter                  # Фильтр вещаний по параметрам
    POST    /api/broadcast/calculate           # API: Расчет стоимости вещания

    ```

### **FR4: Главная страница - детальные требования**
*   **FR4.1:** Верстка:
    ```html
    <div class="region-list">
      <div class="region-card">
        <h3>Московская область</h3>
        <p>Рейтинг: 1.5</p>
        <p>Население: 8,500,000</p>
        <button class="show-smi-btn" data-region-id="1">Показать СМИ</button>
        <div class="smi-list" id="smi-1" style="display:none">
          <!-- Динамически загружаемые СМИ -->
        </div>
      </div>
    </div>
    ```
*   **FR4.2:** JavaScript логика:
    ```javascript
    // При клике на кнопку "Показать СМИ"
    document.querySelectorAll('.show-smi-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const regionId = btn.dataset.regionId;
        const response = await fetch(`/api/region/${regionId}/smi`);
        const smiData = await response.json();
        // Отобразить в соответствующем div
      });
    });
    ```

### **FR5: Калькулятор стоимости - интерфейс**
*   **FR5.1:** HTML форма:
    ```html
    <div class="calculator">
      <select id="org-selector">
        <option value="">Выберите организацию...</option>
        <!-- Опции загружаются через AJAX -->
      </select>
      <button id="calculate-btn">Рассчитать</button>
      <div class="result" id="calculation-result"></div>
      <button id="export-pdf" style="display:none">Экспорт в PDF</button>
      <button id="export-csv" style="display:none">Экспорт в CSV</button>
    </div>
    ```
*   **FR5.2:** Логика расчета на сервере:
    ```python
    @app.route('/api/calculate', methods=['POST'])
    def calculate_cost():
        org_id = request.json.get('org_id')
        base_tariff = 0.01  # Конфигурируемый параметр
        
        # Получаем все broadcast записи организации
        broadcasts = Broadcast.query.filter_by(org_id=org_id).all()
        
        total_cost = 0
        for br in broadcasts:
            district_pop = br.district.population or 0
            smi_rating = br.smi.rating or 1.0
            region_rating = br.district.region.rating or 1.0
            
            point_cost = district_pop * smi_rating * region_rating * base_tariff
            total_cost += point_cost
        
        avg_monthly_cost = total_cost / len(broadcasts) if broadcasts else 0
        
        return jsonify({
            'org_name': org.name,
            'avg_monthly_cost': round(avg_monthly_cost, 2),
            'broadcast_count': len(broadcasts),
            'total_population': sum(b.district.population for b in broadcasts)
        })
    ```

### **FR6: Админ-панель CRUD**
*   **FR6.1:** Общий шаблон для всех сущностей:
    ```html
    <!-- templates/organisation/list.html -->
    <table id="organisations-table" class="display">
        <thead>
            <tr>
                <th>ID</th>
                <th>Название</th>
                <th>ИНН</th>
                <th>Телефон</th>
                <th>Действия</th>
            </tr>
        </thead>
        <tbody>
            {% for org in organisations %}
            <tr>
                <td>{{ org.id }}</td>
                <td>{{ org.name }}</td>
                <td>{{ org.inn }}</td>
                <td>{{ org.phone }}</td>
                <td>
                    <a href="/organisation/{{ org.id }}" class="btn-view">Просмотр</a>
                    <a href="/organisation/{{ org.id }}/edit" class="btn-edit">Редактировать</a>
                    <button class="btn-delete" data-id="{{ org.id }}">Удалить</button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    ```
*   **FR6.2:** Форма создания/редактирования:
    ```html
    <!-- templates/organisation/form.html -->
    <form id="org-form" method="POST" action="{% if org %}/organisation/{{ org.id }}/update{% else %}/organisation/create{% endif %}">
        <div class="form-group">
            <label for="name">Название организации *</label>
            <input type="text" id="name" name="name" value="{{ org.name if org else '' }}" required>
        </div>
        <div class="form-group">
            <label for="inn">ИНН *</label>
            <input type="text" id="inn" name="inn" value="{{ org.inn if org else '' }}" 
                   pattern="\d{10}|\d{12}" title="10 или 12 цифр" required>
        </div>
        <!-- остальные поля -->
        <button type="submit">Сохранить</button>
    </form>
    ```

### **FR7: Аналитика и отчеты**
*   **FR7.1:** Страница аналитики:
    ```html
    <!-- templates/analytics/dashboard.html -->
    <div class="dashboard">
        <div class="filters">
            <select id="region-filter">
                <option value="">Все регионы</option>
                <!-- Опции регионов -->
            </select>
            <select id="smi-filter">
                <option value="">Все СМИ</option>
                <!-- Опции СМИ -->
            </select>
            <button id="apply-filters">Применить</button>
        </div>
        
        <div class="charts">
            <canvas id="cost-by-org-chart" width="400" height="200"></canvas>
        </div>
        
        <div class="report-table">
            <table id="analytics-table">
                <!-- Данные загружаются через AJAX -->
            </table>
        </div>
    </div>
    ```

### **FR8: Безопасность и валидация**
*   **FR8.1:** CSRF защита для всех POST/PUT/DELETE запросов.
*   **FR8.2:** Валидация на сервере для всех входящих данных:
    ```python
    @app.route('/organisation/create', methods=['POST'])
    def create_organisation():
        name = request.form.get('name', '').strip()
        inn = request.form.get('inn', '').strip()
        
        # Проверка обязательных полей
        if not name or not inn:
            flash('Все обязательные поля должны быть заполнены', 'error')
            return redirect(url_for('new_organisation'))
        
        # Проверка уникальности ИНН
        existing = Organisation.query.filter_by(inn=inn).first()
        if existing:
            flash('Организация с таким ИНН уже существует', 'error')
            return redirect(url_for('new_organisation'))
        
        # Создание записи
        org = Organisation(name=name, inn=inn, ...)
        db.session.add(org)
        db.session.commit()
        
        flash('Организация успешно создана', 'success')
        return redirect(url_for('list_organisations'))
    ```

### **FR9: UI/UX требования**
*   **FR9.1:** Адаптивная верстка (mobile-first):
    ```css
    /* static/css/style.css */
    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 15px;
    }
    
    @media (max-width: 768px) {
        .region-card {
            flex-direction: column;
        }
        table {
            font-size: 14px;
        }
    }
    ```
*   **FR9.2:** Интерактивные элементы:
    ```javascript
    // Плавное раскрытие/скрытие списка СМИ
    function toggleSmiList(regionId) {
        const smiList = document.getElementById(`smi-${regionId}`);
        const btn = document.querySelector(`[data-region-id="${regionId}"]`);
        
        if (smiList.style.display === 'none') {
            smiList.style.display = 'block';
            btn.textContent = 'Скрыть СМИ';
            // Загрузка данных через AJAX если еще не загружены
        } else {
            smiList.style.display = 'none';
            btn.textContent = 'Показать СМИ';
        }
    }
    ```

