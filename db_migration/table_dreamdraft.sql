CREATE TABLE dreamdraft (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    selection_1 INT NOT NULL,
    selection_2 INT NOT NULL,
    selection_3 INT NOT NULL,
    selection_4 INT NOT NULL,
    selection_5 INT NOT NULL,
    UNIQUE KEY uq_dreamdraft_user (user_id),
    CONSTRAINT fk_dreamdraft_user
        FOREIGN KEY (user_id) REFERENCES profiles(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_dreamdraft_sel_1
        FOREIGN KEY (selection_1) REFERENCES players(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_dreamdraft_sel_2
        FOREIGN KEY (selection_2) REFERENCES players(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_dreamdraft_sel_3
        FOREIGN KEY (selection_3) REFERENCES players(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_dreamdraft_sel_4
        FOREIGN KEY (selection_4) REFERENCES players(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_dreamdraft_sel_5
        FOREIGN KEY (selection_5) REFERENCES players(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);