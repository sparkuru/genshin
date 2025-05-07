CREATE DATABASE typecho;
CREATE USER 'typecho'@'localhost' IDENTIFIED BY 'typecho';
GRANT ALL PRIVILEGES ON typecho.* TO 'typecho'@'localhost';

CREATE DATABASE hedgedoc;
CREATE USER 'hedgedoc'@'%' IDENTIFIED BY 'hedgedoc';
GRANT ALL PRIVILEGES ON hedgedoc.* TO 'hedgedoc'@'%';

FLUSH PRIVILEGES; 