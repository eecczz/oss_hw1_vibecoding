SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS municipalities (
    local_government_code TEXT PRIMARY KEY
        CHECK (trim(local_government_code) <> '')
);

CREATE TABLE IF NOT EXISTS toilet_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
        CHECK (trim(name) <> '')
);

CREATE TABLE IF NOT EXISTS ownership_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
        CHECK (trim(name) <> '')
);

CREATE TABLE IF NOT EXISTS sewage_process_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
        CHECK (trim(name) <> '')
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE
        CHECK (instr(email, '@') > 1),
    password_hash TEXT NOT NULL
        CHECK (trim(password_hash) <> ''),
    name TEXT NOT NULL
        CHECK (length(trim(name)) BETWEEN 2 AND 50),
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS toilets (
    management_number TEXT PRIMARY KEY
        CHECK (trim(management_number) <> ''),
    local_government_code TEXT NOT NULL,
    toilet_type_id INTEGER NOT NULL,
    ownership_type_id INTEGER,
    sewage_process_type_id INTEGER,
    legal_basis_name TEXT,
    name TEXT NOT NULL
        CHECK (trim(name) <> ''),
    road_address TEXT,
    lot_address TEXT,
    management_agency TEXT,
    phone_number TEXT,
    opening_hours_type TEXT,
    opening_hours_detail TEXT,
    installation_year_month TEXT
        CHECK (
            installation_year_month IS NULL
            OR installation_year_month GLOB '[1-2][0-9][0-9][0-9][0-1][0-9]'
        ),
    latitude REAL NOT NULL
        CHECK (latitude BETWEEN 33.0 AND 39.5),
    longitude REAL NOT NULL
        CHECK (longitude BETWEEN 124.0 AND 132.5),
    safety_target_flag INTEGER NOT NULL DEFAULT 0
        CHECK (safety_target_flag IN (0, 1)),
    emergency_bell_flag INTEGER NOT NULL DEFAULT 0
        CHECK (emergency_bell_flag IN (0, 1)),
    emergency_bell_location TEXT,
    entrance_cctv_flag INTEGER NOT NULL DEFAULT 0
        CHECK (entrance_cctv_flag IN (0, 1)),
    diaper_changing_table_flag INTEGER NOT NULL DEFAULT 0
        CHECK (diaper_changing_table_flag IN (0, 1)),
    diaper_changing_table_location TEXT,
    remodeling_year_month TEXT
        CHECK (
            remodeling_year_month IS NULL
            OR remodeling_year_month GLOB '[1-2][0-9][0-9][0-9][0-1][0-9]'
        ),
    reference_date TEXT
        CHECK (
            reference_date IS NULL
            OR reference_date GLOB '[1-2][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'
        ),
    last_modified_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (road_address IS NOT NULL OR lot_address IS NOT NULL),
    FOREIGN KEY (local_government_code)
        REFERENCES municipalities(local_government_code)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (toilet_type_id)
        REFERENCES toilet_types(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (ownership_type_id)
        REFERENCES ownership_types(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    FOREIGN KEY (sewage_process_type_id)
        REFERENCES sewage_process_types(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS toilet_stall_counts (
    management_number TEXT PRIMARY KEY,
    male_toilet_count INTEGER NOT NULL DEFAULT 0 CHECK (male_toilet_count >= 0),
    male_urinal_count INTEGER NOT NULL DEFAULT 0 CHECK (male_urinal_count >= 0),
    male_disabled_toilet_count INTEGER NOT NULL DEFAULT 0 CHECK (male_disabled_toilet_count >= 0),
    male_disabled_urinal_count INTEGER NOT NULL DEFAULT 0 CHECK (male_disabled_urinal_count >= 0),
    male_child_toilet_count INTEGER NOT NULL DEFAULT 0 CHECK (male_child_toilet_count >= 0),
    male_child_urinal_count INTEGER NOT NULL DEFAULT 0 CHECK (male_child_urinal_count >= 0),
    female_toilet_count INTEGER NOT NULL DEFAULT 0 CHECK (female_toilet_count >= 0),
    female_disabled_toilet_count INTEGER NOT NULL DEFAULT 0 CHECK (female_disabled_toilet_count >= 0),
    female_child_toilet_count INTEGER NOT NULL DEFAULT 0 CHECK (female_child_toilet_count >= 0),
    FOREIGN KEY (management_number)
        REFERENCES toilets(management_number)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_toilets_geo ON toilets(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_toilets_name ON toilets(name);
CREATE INDEX IF NOT EXISTS idx_toilets_local_government_code ON toilets(local_government_code);
CREATE INDEX IF NOT EXISTS idx_toilets_type_id ON toilets(toilet_type_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
"""
