CREATE TABLE IF NOT EXISTS tournament_db.config (
    name VARCHAR(255) PRIMARY KEY UNIQUE,
    value TEXT
)

ALTER TABLE tournament_db.config ADD COLUMN public BOOLEAN DEFAULT(false)