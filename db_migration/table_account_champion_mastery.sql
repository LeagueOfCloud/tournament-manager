CREATE TABLE IF NOT EXISTS tournament_db.account_champion_mastery (
    account_puuid CHAR(255) NOT NULL,
    #champion_id INT NOT NULL,
    #champion_level INT DEFAULT 0,
    #champion_points INT DEFAULT 0,
    #last_play_time DATETIME DEFAULT NULL,
    #chest_granted BOOLEAN DEFAULT FALSE,
    #tokens_earned INT DEFAULT 0,
    mastery_json JSON NOT NULL,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (account_puuid),
    
    CONSTRAINT fk_account_champion_mastery_riot_accounts
        FOREIGN KEY (account_puuid)
        REFERENCES tournament_db.riot_accounts (account_puuid)
        ON DELETE CASCADE
);