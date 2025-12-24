-- Organisations table
CREATE TABLE if not EXISTS organisation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    name_short TEXT,
    inn TEXT NOT NULL UNIQUE,
    ogrn TEXT NOT NULL UNIQUE,
    address TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    arv_member INTEGER DEFAULT 0,
    population_sum INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE if not EXISTS smi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    smi_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    rating REAL DEFAULT 3.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE if not EXISTS region (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rating REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE if not EXISTS district (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    population INTEGER,
    rating REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES region(id)
);

CREATE TABLE if not EXISTS broadcast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id INTEGER NOT NULL,
    district_id INTEGER NOT NULL,
    smi_id INTEGER NOT NULL,
    mount_point TEXT,
    channel_num TEXT,
    freq TEXT,
    power TEXT,
    brcst_time TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organisation(id),
    FOREIGN KEY (district_id) REFERENCES district(id),
    FOREIGN KEY (smi_id) REFERENCES smi(id)
    );

create index idx_broadcast_org on broadcast(org_id);
create index idx_broadcast_distinct on broadcast(district_id);
create index idx_broadcast_smi on broadcast(smi_id);
create index idx_district_region on district(region_id);
