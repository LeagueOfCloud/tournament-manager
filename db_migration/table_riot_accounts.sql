CREATE TABLE IF NOT EXISTS tournament_db.riot_accounts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    account_name VARCHAR(50) NOT NULL UNIQUE,
    account_puuid VARCHAR(255) NOT NULL UNIQUE,
    player_id INT NOT NULL,
    is_primary VARCHAR(10) NOT NULL 
        CHECK (is_primary IN ('true', 'false')),
    FOREIGN KEY (player_id) REFERENCES tournament_db.players(id)
);