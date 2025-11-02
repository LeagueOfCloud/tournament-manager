START TRANSACTION;

ALTER TABLE tournament_db.players
  DROP FOREIGN KEY `players_ibfk_1`,
  DROP FOREIGN KEY `players_ibfk_2`;

ALTER TABLE tournament_db.players
  ADD CONSTRAINT `players_ibfk_1`
    FOREIGN KEY (`team_id`)
    REFERENCES tournament_db.teams(`id`)
    ON DELETE CASCADE,
  ADD CONSTRAINT `players_ibfk_2`
    FOREIGN KEY (`discord_id`)
    REFERENCES tournament_db.profiles(`discord_id`)
    ON DELETE CASCADE;

ALTER TABLE tournament_db.riot_accounts
  DROP FOREIGN KEY `riot_accounts_ibfk_1`;

ALTER TABLE tournament_db.riot_accounts
  ADD CONSTRAINT `riot_accounts_ibfk_1`
    FOREIGN KEY (`player_id`)
    REFERENCES tournament_db.players(`id`)
    ON DELETE CASCADE;

COMMIT;