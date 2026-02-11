CREATE TABLE IF NOT EXISTS tournament_db.dreamdraft_match_scores (
    tournament_match_id INT NOT NULL,
    player_id INT NOT NULL,
    score FLOAT NOT NULL,

    PRIMARY KEY (tournament_match_id, player_id),

    CONSTRAINT fk_ddms_match FOREIGN KEY (tournament_match_id) REFERENCES tournament_db.tournament_matches (id) ON DELETE CASCADE,
    CONSTRAINT fk_ddms_player FOREIGN KEY (player_id) REFERENCES tournament_db.players (id) ON DELETE CASCADE
);