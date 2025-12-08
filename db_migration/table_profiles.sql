CREATE TABLE IF NOT EXISTS tournament_db.profiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    discord_id VARCHAR(50) NOT NULL UNIQUE,
    avatar_url VARCHAR(255),
    type VARCHAR(20) NOT NULL DEFAULT('user') CHECK (
        type IN ('player', 'admin', 'user')
    ),
    token VARCHAR(255) NOT NULL DEFAULT(UUID())
);

ALTER TABLE tournament_db.profiles
ADD pickems_score INT NOT NULL DEFAULT(0);

ALTER TABLE tournament_db.profiles
ADD dd_score INT NOT NULL DEFAULT(0);