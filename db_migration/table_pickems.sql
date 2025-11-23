CREATE TABLE IF NOT EXISTS tournament_db.pickems (
    id VARCHAR(255) PRIMARY KEY,
    pickem_id VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    value VARCHAR(255) NOT NULL,
    CONSTRAINT fk_pickems_user_id
        FOREIGN KEY (user_id)
        REFERENCES tournament_db.profiles (id)
        ON DELETE CASCADE
);