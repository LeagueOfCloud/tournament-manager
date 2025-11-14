CREATE TABLE IF NOT EXISTS tournament_db.tournament_matches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    team_1_id INT NOT NULL,
    team_2_id INT NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME DEFAULT NULL,
    winner_team_id INT DEFAULT NULL,
    tournament_match_id VARCHAR(100) NOT NULL UNIQUE
);

ALTER TABLE tournament_db.tournament_matches
MODIFY tournament_match_id VARCHAR(100) DEFAULT NULL UNIQUE;