CREATE TABLE IF NOT EXISTS metrics_baseline (
    role VARCHAR(10) NOT NULL,
    metric VARCHAR(50) NOT NULL,

    mean FLOAT NOT NULL,
    std FLOAT NOT NULL,
    sample_size INT NOT NULL,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (role, metric)
);

ALTER TABLE metrics_baseline
DROP PRIMARY KEY,
ADD PRIMARY KEY (role, metric);