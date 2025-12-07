CREATE TABLE IF NOT EXISTS tournament_db.processed_match_data (
    match_id VARCHAR(255) NOT NULL,
    account_puuid VARCHAR(255) NOT NULL,
    account_name VARCHAR(50) NOT NULL,
    champion_name VARCHAR(50),
    teamPosition VARCHAR(50),
    goldEarned INT,
    totalDamageDealtToChampions INT,
    totalMinionsKilled INT,
    kills INT,
    deaths INT,
    assists INT,
    vision_score INT,
    win VARCHAR(10)
        CHECK (win IN ('true', 'false')),
    CONSTRAINT fk_processed_match_data_match_history_match_id
        FOREIGN KEY (match_id)
        REFERENCES tournament_db.match_history (match_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,    
    CONSTRAINT fk_processed_match_data_riot_accounts_puuid
        FOREIGN KEY (account_puuid)
        REFERENCES tournament_db.riot_accounts (account_puuid)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_processed_match_data_riot_accounts_name
        FOREIGN KEY (account_name)
        REFERENCES tournament_db.riot_accounts (account_name)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    PRIMARY KEY (match_id, account_puuid)
);

ALTER TABLE tournament_db.processed_match_data
ADD COLUMN queueId INT;

ALTER TABLE tournament_db.processed_match_data
ADD COLUMN gameDuration INT;

ALTER TABLE tournament_db.processed_match_data
ADD COLUMN damageDealtToTurrets INT,
ADD COLUMN totalDamageTaken INT,
ADD COLUMN damageSelfMitigated INT,
ADD COLUMN totalHealsOnTeammates INT,
ADD COLUMN totalTimeCCDealt INT,
ADD COLUMN objectivesStolen INT;
