-- sample auto-import script, runs once when ./data is empty
-- replace with your own dump, e.g. mysqldump ... > 01-init.sql
CREATE DATABASE IF NOT EXISTS test;
USE test;

CREATE TABLE IF NOT EXISTS demo (
  id   INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(64) NOT NULL
);

INSERT INTO demo (name) VALUES ('hello'), ('world');
