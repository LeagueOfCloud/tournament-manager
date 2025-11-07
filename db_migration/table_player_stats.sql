CREATE TABLE IF NOT EXISTS tournament_db.player_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    puuid CHAR(255) NOT NULL,
    league_entries JSON,
    UNIQUE KEY uq_puuid (puuid),
    CONSTRAINT fk_player_stats_riot_accounts
        FOREIGN KEY (puuid)
        REFERENCES tournament_db.riot_accounts (account_puuid)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
