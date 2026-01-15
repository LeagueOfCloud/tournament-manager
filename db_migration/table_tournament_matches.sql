CREATE TABLE IF NOT EXISTS tournament_db.tournament_matches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    team_1_id INT NOT NULL,
    team_2_id INT NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME DEFAULT NULL,
    winner_team_id INT DEFAULT NULL,
    tournament_match_id VARCHAR(100) DEFAULT NULL UNIQUE,
    CONSTRAINT fk_tournament_matches_team_1_id FOREIGN KEY (team_1_id) REFERENCES tournament_db.teams (id) ON DELETE CASCADE,
    CONSTRAINT fk_tournament_matches_team_2_id FOREIGN KEY (team_2_id) REFERENCES tournament_db.teams (id) ON DELETE CASCADE
);

ALTER TABLE tournament_db.tournament_matches
ADD COLUMN lobby_code VARCHAR(50) DEFAULT NULL;

ALTER TABLE tournament_db.tournament_matches
DROP FOREIGN KEY fk_tournament_matches_winner_team_id;

ALTER TABLE tournament_db.tournament_matches
ADD CONSTRAINT fk_tournament_matches_winner_team_id FOREIGN KEY (winner_team_id) REFERENCES tournament_db.teams (id) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE tournament_matches
ADD COLUMN map VARCHAR(255) NOT NULL DEFAULT("SUMMONERS_RIFT"),
ADD COLUMN pick_type VARCHAR(255) NOT NULL DEFAULT("TOURNAMENT_DRAFT"),
ADD COLUMN team_size INT NOT NULL DEFAULT(5)

ALTER TABLE tournament_matches
ADD COLUMN vod_url VARCHAR(255) DEFAULT NULL;