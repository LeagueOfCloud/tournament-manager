CREATE TABLE IF NOT EXISTS tournament_db.match_history (
    match_id VARCHAR(255) PRIMARY KEY,
    match_data BLOB
);