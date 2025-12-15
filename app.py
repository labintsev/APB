from flask import Flask, render_template, render_template_string, g, abort, request, url_for, redirect
import sqlite3
from pathlib import Path

app = Flask(__name__)

# Path to the database created by the importer
DB_PATH = Path("broadcast_target.db")


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        if not DB_PATH.exists():
            raise RuntimeError(f"Database not found at {DB_PATH}. Run the importer first.")
        db = sqlite3.connect(str(DB_PATH))
        db.row_factory = sqlite3.Row
        g._database = db
        # Ensure `is_active` column exists on `broadcast` table; add if missing
        try:
            cols = [r[1] for r in db.execute("PRAGMA table_info(broadcast)").fetchall()]
            if 'is_active' not in cols:
                db.execute("ALTER TABLE broadcast ADD COLUMN is_active INTEGER DEFAULT 1")
                db.commit()
        except Exception:
            # If broadcast table doesn't exist or other error, ignore here
            pass
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    """List organisations with links."""
    db = get_db()

    # Fetch all regions for display
    regions = db.execute('SELECT id, name, rating FROM region ORDER BY name').fetchall()
    return render_template('index.html', regions=regions)


@app.route('/org_list')
def org_list():
    """List organisations with links."""
    db = get_db()

    # Search and pagination
    q = (request.args.get('q') or '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    PAGE_SIZE = 20
    offset = (page - 1) * PAGE_SIZE

    params = []
    where = ''
    if q:
        likeq = f"%{q}%"
        where = "WHERE name LIKE ? OR name_short LIKE ? OR inn LIKE ?"
        params = [likeq, likeq, likeq]

    # total count for pagination
    count_sql = f"SELECT COUNT(*) as cnt FROM organisation {where}"
    cur = db.execute(count_sql, params)
    total_count = cur.fetchone()['cnt']
    total_pages = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)

    # Subquery: sum distinct district populations per organisation (broadcasts reference organisation.id)
    pop_subq = (
        "(SELECT b.org_id AS org_db_id, SUM(DISTINCT d.population) AS total_population "
        "FROM broadcast b JOIN district d ON b.district_id = d.id GROUP BY b.org_id) AS pop_sums"
    )

    # Select organisations with joined population sums, ordered by population descending
    sql = (
        f"SELECT o.id, o.org_id, o.name, o.name_short, COALESCE(pop_sums.total_population, 0) AS total_population "
        f"FROM organisation o LEFT JOIN {pop_subq} ON pop_sums.org_db_id = o.id {where} "
        f"ORDER BY COALESCE(pop_sums.total_population, 0) DESC, o.name LIMIT ? OFFSET ?"
    )

    rows = db.execute(sql, params + [PAGE_SIZE, offset]).fetchall()

    return render_template('org-list.html', organisations=rows, q=q, page=page, total_pages=total_pages, total_count=total_count)


@app.route('/org/<int:org_db_id>')
def organisation_detail(org_db_id: int):
    """Show districts, SMI and population for a given organisation.

    Also show the summed population (sum of DISTINCT district populations referenced by this org).
    """
    db = get_db()

    # Get organisation
    cur = db.execute('SELECT id, org_id, name, name_short, inn FROM organisation WHERE id = ?', (org_db_id,))
    org = cur.fetchone()
    if org is None:
        abort(404)

    # Query broadcast rows with district and smi
    rows = []
    try:
        q = '''
            SELECT b.id AS broadcast_id,
                   d.id AS district_id,
                   d.name AS district_name,
                   d.population AS population,
                   s.name AS smi_name,
                   COALESCE(s.rating, 0.0) AS smi_rating,
                   COALESCE(r.rating, 0.0) AS region_rating,
                   b.mount_point, b.channel_num, b.freq, b.power, b.brcst_time,
                   COALESCE(b.is_active, 1) AS is_active
            FROM broadcast b
            JOIN district d ON b.district_id = d.id
            JOIN smi s ON b.smi_id = s.id
            JOIN region r ON d.region_id = r.id
            WHERE b.org_id = ?
            ORDER BY d.name
            '''
        rows = db.execute(q, (org_db_id,)).fetchall()
    except Exception:
        # If query fails (missing tables, etc.), keep rows empty
        rows = []

    # Sum distinct district populations to avoid double counting one district
    sum_q = '''
    SELECT SUM(DISTINCT d.population) AS total_population
    FROM broadcast b
    JOIN district d ON b.district_id = d.id
    WHERE b.org_id = ?
    '''
    total_row = db.execute(sum_q, (org_db_id,)).fetchone()
    total_population = total_row['total_population'] or 0

    # The importer stored population as integer (population * 1000).
    # Convert to human-friendly millions for display (i.e. raw value / 1_000_000).
    def fmt_pop(p):
        try:
            return float(p) / 1000000.0
        except Exception:
            return None

    # Prepare list of districts for display
    districts = []
    for r in rows:
        districts.append({
            'district_id': r['district_id'],
            'district_name': r['district_name'],
            'population': fmt_pop(r['population']),
            'smi_name': r['smi_name'],
            'smi_rating': float(r['smi_rating']) if r['smi_rating'] is not None else None,
            'region_rating': float(r['region_rating']) if r['region_rating'] is not None else None,
            'mount_point': r['mount_point'],
            'channel_num': r['channel_num'],
            'freq': r['freq'],
            'power': r['power'],
            'brcst_time': r['brcst_time'],
            'broadcast_id': r['broadcast_id'],
            'is_active': bool(r['is_active'])
        })

    return render_template('org-broadcasts.html', org=org, districts=districts, total_population=fmt_pop(total_population))


@app.route('/org/<int:org_db_id>/update_active', methods=['POST'])
def update_active(org_db_id: int):
    """Update is_active flags for broadcasts of the given organisation.

    The form posts checkboxes named 'active' with broadcast IDs for those that should be active.
    All other broadcasts for the organisation will be set to inactive.
    """
    db = get_db()
    # Ensure organisation exists
    cur = db.execute('SELECT id FROM organisation WHERE id = ?', (org_db_id,))
    if cur.fetchone() is None:
        abort(404)

    checked = request.form.getlist('active')  # list of broadcast id strings
    try:
        checked_ids = [int(x) for x in checked]
    except Exception:
        checked_ids = []

    # Set all to inactive, then activate selected ones
    try:
        db.execute('BEGIN')
        db.execute('UPDATE broadcast SET is_active = 0 WHERE org_id = ?', (org_db_id,))
        if checked_ids:
            placeholders = ','.join(['?'] * len(checked_ids))
            params = checked_ids + [org_db_id]
            db.execute(f'UPDATE broadcast SET is_active = 1 WHERE id IN ({placeholders}) AND org_id = ?', params)
        db.commit()
    except Exception:
        db.rollback()

    return redirect(url_for('organisation_detail', org_db_id=org_db_id))


# --- SMI CRUD ---
@app.route('/smi')
def smi_list():
    db = get_db()
    rows = db.execute('SELECT id, name, rating FROM smi ORDER BY name').fetchall()
    return render_template('smi.html', smis=rows)


@app.route('/smi/create', methods=['POST'])
def create_smi():
    db = get_db()
    name = (request.form.get('name') or '').strip()
    rating = request.form.get('rating')
    try:
        rating_val = float(rating) if rating else None
    except Exception:
        rating_val = None
    if name:
        db.execute('INSERT INTO smi (name, rating) VALUES (?, ?)', (name, rating_val))
        db.commit()
    return redirect(url_for('smi_list'))


@app.route('/smi/<int:smi_id>/delete', methods=['POST'])
def delete_smi(smi_id: int):
    db = get_db()
    db.execute('DELETE FROM smi WHERE id = ?', (smi_id,))
    db.commit()
    return redirect(url_for('smi_list'))


@app.route('/smi/<int:smi_id>/edit', methods=['GET', 'POST'])
def edit_smi(smi_id: int):
    db = get_db()
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        rating = request.form.get('rating')
        try:
            rating_val = float(rating) if rating else None
        except Exception:
            rating_val = None
        if name:
            db.execute('UPDATE smi SET name = ?, rating = ? WHERE id = ?', (name, rating_val, smi_id))
            db.commit()
        return redirect(url_for('smi_list'))
    row = db.execute('SELECT id, name, rating FROM smi WHERE id = ?', (smi_id,)).fetchone()
    if row is None:
        abort(404)
    # Simple inline edit form
    return render_template_string('''
      <form method="post">
        <label>Name: <input name="name" value="{{name}}"></label>
        <label>Rating: <input name="rating" value="{{rating}}"></label>
        <button type="submit">Save</button>
      </form>
    ''', name=row['name'], rating=row['rating'])


# --- Region CRUD ---
@app.route('/region')
def region_list():
    db = get_db()
    rows = db.execute('SELECT id, name, rating FROM region ORDER BY name').fetchall()
    return render_template('region.html', regions=rows)


@app.route('/region/create', methods=['POST'])
def create_region():
    db = get_db()
    name = (request.form.get('name') or '').strip()
    rating = request.form.get('rating')
    try:
        rating_val = float(rating) if rating else None
    except Exception:
        rating_val = None
    if name:
        db.execute('INSERT INTO region (name, rating) VALUES (?, ?)', (name, rating_val))
        db.commit()
    return redirect(url_for('region_list'))


@app.route('/region/<int:region_id>/delete', methods=['POST'])
def delete_region(region_id: int):
    db = get_db()
    db.execute('DELETE FROM region WHERE id = ?', (region_id,))
    db.commit()
    return redirect(url_for('region_list'))


@app.route('/region/<int:region_id>/edit', methods=['GET', 'POST'])
def edit_region(region_id: int):
    db = get_db()
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        rating = request.form.get('rating')
        try:
            rating_val = float(rating) if rating else None
        except Exception:
            rating_val = None
        if name:
            db.execute('UPDATE region SET name = ?, rating = ? WHERE id = ?', (name, rating_val, region_id))
            db.commit()
        return redirect(url_for('region_list'))
    row = db.execute('SELECT id, name, rating FROM region WHERE id = ?', (region_id,)).fetchone()
    if row is None:
        abort(404)
    return render_template_string('''
      <form method="post">
        <label>Name: <input name="name" value="{{name}}"></label>
        <label>Rating: <input name="rating" value="{{rating}}"></label>
        <button type="submit">Save</button>
      </form>
    ''', name=row['name'], rating=row['rating'])


# --- District CRUD ---
@app.route('/district')
def district_list():
    db = get_db()
    districts = db.execute('SELECT d.id, d.name, d.population, r.name as region_name FROM district d LEFT JOIN region r ON d.region_id = r.id ORDER BY d.name').fetchall()
    regions = db.execute('SELECT id, name FROM region ORDER BY name').fetchall()
    return render_template('district.html', districts=districts, regions=regions)


@app.route('/district/create', methods=['POST'])
def create_district():
    db = get_db()
    name = (request.form.get('name') or '').strip()
    region_id = request.form.get('region_id')
    population = request.form.get('population')
    try:
        region_val = int(region_id) if region_id else None
    except Exception:
        region_val = None
    try:
        pop_val = int(population) if population else None
    except Exception:
        pop_val = None
    if name and region_val:
        db.execute('INSERT INTO district (name, region_id, population) VALUES (?, ?, ?)', (name, region_val, pop_val))
        db.commit()
    return redirect(url_for('district_list'))


@app.route('/district/<int:district_id>/delete', methods=['POST'])
def delete_district(district_id: int):
    db = get_db()
    db.execute('DELETE FROM district WHERE id = ?', (district_id,))
    db.commit()
    return redirect(url_for('district_list'))


@app.route('/district/<int:district_id>/edit', methods=['GET', 'POST'])
def edit_district(district_id: int):
    db = get_db()
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        region_id = request.form.get('region_id')
        population = request.form.get('population')
        try:
            region_val = int(region_id) if region_id else None
        except Exception:
            region_val = None
        try:
            pop_val = int(population) if population else None
        except Exception:
            pop_val = None
        if name and region_val:
            db.execute('UPDATE district SET name = ?, region_id = ?, population = ? WHERE id = ?', (name, region_val, pop_val, district_id))
            db.commit()
        return redirect(url_for('district_list'))
    row = db.execute('SELECT id, name, region_id, population FROM district WHERE id = ?', (district_id,)).fetchone()
    if row is None:
        abort(404)
    regions = db.execute('SELECT id, name FROM region ORDER BY name').fetchall()
    return render_template_string('''
      <form method="post">
        <label>Name: <input name="name" value="{{name}}"></label>
        <label>Region: <select name="region_id">{% for r in regions %}<option value="{{r.id}}" {% if r.id==region_id %}selected{% endif %}>{{r.name}}</option>{% endfor %}</select></label>
        <label>Population: <input name="population" value="{{population}}"></label>
        <button type="submit">Save</button>
      </form>
    ''', name=row['name'], region_id=row['region_id'], regions=regions, population=row['population'])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
