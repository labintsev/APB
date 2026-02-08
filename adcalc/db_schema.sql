-- Organisations table
CREATE TABLE if not EXISTS organisation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    inn TEXT UNIQUE,
    ogrn TEXT UNIQUE,
    address TEXT,
    phone TEXT,
    email TEXT,
    arv_member INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE if not EXISTS region (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rating REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Broadcast table with embedded SMI and District fields
CREATE TABLE if not EXISTS broadcast (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id INTEGER NOT NULL,
    
    -- Embedded SMI fields (smi table removed)
    smi_name TEXT,
    smi_rating REAL,
    smi_male_proportion REAL,
    
    -- Embedded District fields (district table removed)
    district_name TEXT,
    district_population INTEGER,
    
    -- Region relationship
    region_id INTEGER NOT NULL,
    
    frequency TEXT,
    power REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organisation(id) ON DELETE RESTRICT,
    FOREIGN KEY (region_id) REFERENCES region(id)
);

create index idx_broadcast_org on broadcast(org_id);
create index idx_broadcast_region on broadcast(region_id);
