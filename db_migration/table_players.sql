CREATE TABLE IF NOT EXISTS tournament_db.players (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    discord_id VARCHAR(50) UNIQUE,
    avatar_url VARCHAR(255),
    team_id INT NOT NULL,
    team_role VARCHAR(10) NOT NULL
        CHECK (team_role IN ('top', 'jungle', 'mid', 'bot', 'support', 'sub')),
    FOREIGN KEY (team_id) REFERENCES tournament_db.teams(id),
    FOREIGN KEY (discord_id) REFERENCES tournament_db.profiles(discord_id)
);