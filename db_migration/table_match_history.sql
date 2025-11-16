CREATE TABLE IF NOT EXISTS tournament_db.match_history (
    match_id VARCHAR(255) PRIMARY KEY,
    match_data JSON
);

ALTER TABLE tournament_db.match_history
MODIFY match_data JSON;

ALTER TABLE tournament_db.match_history
ADD COLUMN was_processed VARCHAR(10) NOT NULL DEFAULT 'false'
        CHECK (was_processed IN ('true', 'false'));