CREATE TABLE IF NOT EXISTS tournament_db.riot_accounts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    account_name VARCHAR(50) NOT NULL UNIQUE,
    account_puuid VARCHAR(255) NOT NULL UNIQUE,
    player_id INT NOT NULL,
    is_primary VARCHAR(10) NOT NULL 
        CHECK (is_primary IN ('true', 'false')),
    FOREIGN KEY (player_id) REFERENCES tournament_db.players(id)
);

DELIMITER $$

CREATE TRIGGER check_single_primary_insert
BEFORE INSERT ON tournament_db.riot_accounts
FOR EACH ROW
BEGIN
    IF NEW.is_primary = 'true' THEN
        IF (SELECT COUNT(*) 
              FROM tournament_db.riot_accounts 
             WHERE player_id = NEW.player_id 
               AND is_primary = 'true') > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'A player can only have one primary account';
        END IF;
    END IF;
END$$

CREATE TRIGGER check_single_primary_update
BEFORE UPDATE ON tournament_db.riot_accounts
FOR EACH ROW
BEGIN
    IF NEW.is_primary = 'true' AND (OLD.is_primary <> 'true' OR OLD.player_id <> NEW.player_id) THEN
        IF (SELECT COUNT(*) 
              FROM tournament_db.riot_accounts 
             WHERE player_id = NEW.player_id 
               AND is_primary = 'true' 
               AND id <> OLD.id) > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'A player can only have one primary account';
        END IF;
    END IF;
END$$

DELIMITER ;

ALTER TABLE tournament_db.riot_accounts
ADD COLUMN last_match_history_fetch DATETIME DEFAULT NULL;