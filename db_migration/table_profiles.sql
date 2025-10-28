CREATE TABLE IF NOT EXISTS tournament_db.profiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    discord_id VARCHAR(50) NOT NULL UNIQUE,
    avatar_url VARCHAR(255),
    type VARCHAR(20) NOT NULL
        CHECK (type IN ('player', 'admin', 'user')) DEFAULT("user"),
    token VARCHAR(255) NOT NULL DEFAULT(UUID())
);
