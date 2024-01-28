这里列举一些很通用的东西，以后再遇到直接当 handbook 来速查，也可以直接参考 [手册](https://refer.majo.im/docs/mysql.html)

## mysql

个人优先推荐 mysql，社区活跃、文档丰富，如无特别说明，下面以 mysql 8.0 的操作为准

### sql common

1. 数据库

    1. 显示数据库：`show databases;`
    2. 创建数据库：`create database db_name;`
    3. 删除数据库：`drop database db_name;`
    4. 选择数据库：`use db_name;`
2. 表

    1. 创建表：`create table table_name (row_1 data_type, row_2 data_type, ...);`
    2. 删除表：`drop table table_name;`
    3. 显示所有表：`show tables;`
    4. 展示表的结构：`describe table_name;`
3. 数据（crud）

    1. 插入数据：`insert into table_name (row_1, row_2, ...) values (value_1, value_2, ...);`
    2. 查询：`select row_name from table_name where condition;`
    3. 更新数据：`update table_name set row_name = new_value where condition;`
    4. 删除：`delete from table_name where condition;`

### installation

1. debian 系直接用包管理器安装：`sudo apt install mysql-server`；
2. 在使用 ubuntu >= 20 以上的时候 默认的 apt 源使用的是 mysql8.0 版本，8.0与5.7版本之间有部分内容不同 保险起见推荐先备份原有数据库，如果想在 ubuntu 18.04 使用 mysql8.0，按照以下方法来：

    1. 下载官方 mysql 源切换工具：`wget -c https://dev.mysql.com/get/mysql-apt-config_0.8.15-1_all.deb`
    2. 切换 mysql 源：`sudo dpkg -i mysql-apt-config_0.8.15-1_all.deb`，更新源和升级源：`sudo apt update && sudo apt upgrade`
    3. （可选）注意这里可能会报错 *NO_PUBKEY: 467B942D3A79BD29*（可能是其他），只需要访问 key 服务器接收即可：`sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 467B942D3A79BD29`，然后更新源和升级源：`sudo apt update && sudo apt upgrade`
    4. 弹窗选择，用 Tab 切换选定列表，上下键修改选项，选择 mysql-server 8.0

### init

1. 初始化设置：`sudo mysql_secure_installation`

    1. `VALIDATE PASSWORD PLUGIN`，密码强度验证器，选 y 或 n 都行
    2. 输入有效密码，y 确认
    3. `Remove anonymous users?`，移除匿名访问权限，这个先不要禁止，选 n
    4. `Disallow root login remotely?`，禁止高权限用户远程登录，选 y
    5. `Remove test database and access to it?`，移除 test 默认数据库，选n
    6. `Reload privilege tables now?`，重新加载授权信息，选 y
2. 修改默认开放端口：

    1. 早期版本：在 `/etc/my.cnf` 文件中添加 `port = xxx` 一行，如果没有就重新创建一个：`sudo touch /etc/my.cnf`
    2. 较新版本：`/etc/mysql/mysql.conf.d/mysqld.cnf` 的 `[mysqld]` 下添加 `port = xxx`

### usage

1. 连接数据库

    1. 直接以某一账户身份，注意数据库中应有该用户，这里用 root：`sudo mysql`
    2. 指定用户登录，`-u` 指定用户 `-p` 指定使用密码登录：`mysql -u phpmyadmin -p`，然后输入密码
    3. 远程登录，`-h` 指定主机地址 `-P` 指定端口（注意这里需要给用户远程登录的操作，见后文的授权章节）：`mysql -h 192.168.0.1 -P 3306 -u phpmyadmin -p`
2. 创建普通用户和数据库，以创建一个 phpmyadmin 用户为例，登录到数据库中后，依次输入以下指令：

    1. 列出所有数据库：`show databases;`；删除某个数据库：`drop database db_name`
    2. 创建数据库：`create database phpmyadmin;`
    3. 打开一个 db 以进行后续操作：`use phpmyadmin;`
    4. 创建用户，通式：`CREATE USER 'username'@'host' IDENTIFIED BY 'password';`，

        1. 只允许本地登录：`CREATE USER 'phpmyadmin'@'localhost' IDENTIFIED BY '123456';`
        2. 允许任意 ip 登录以及本地登录，`%` 是通配符：`CREATE USER 'phpmyadmin'@'%' IDENTIFIED BY '123456';`
    5. 授权，通式：`GRANT privileges ON databasename.tablename TO 'username'@'host' IDENTIFIED BY 'password' WITH GRANT OPTION;`

        1. 为 phpmyadmin@localhost 授予数据库 phpmyadmin 中使用 select、insert、update 的权力，且其可以再授权给其他用户：`GRANT SELECT, INSERT, UPDATE ON phpmyadmin.* TO 'phpmyadmin'@'localhost' IDENTIFIED BY '123456' WITH GRANT OPTION;`
        2. 为 phpmyadmin@% 授予数据库 phpmyadmin 中所有权力，且其可以再授权给其他用户：`GRANT ALL ON phpmyadmin.* TO 'phpmyadmin'@'%' IDENTIFIED BY '密码' WITH GRANT OPTION;`
    6. 修改

        1. 改某个用户密码：`ALTER USER 'phpmyadmin'@'localhost' IDENTIFIED BY 'new_password';`
        2. 改用户名：`RENAME USER 'phpmyadmin'@'localhost' TO 'new_admin'@'localhost';`，当然还可以通过创建一个新用户，然后将旧用户的权限复制给新用户，再删除旧用户：

            1. `CREATE USER 'new_user'@'localhost' IDENTIFIED BY 'password';`
            2. `GRANT ALL PRIVILEGES ON database_name.* TO 'new_user'@'localhost';`，`FLUSH PRIVILEGES;`
            3. 删除：`DROP USER 'phpmyadmin'@'localhost';`
        3. 权限，要修改用户权限，一般是先全部撤销之再重新授予

            1. 撤销权限：`REVOKE ALL PRIVILEGES ON phpmyadmin.* FROM 'phpmyadmin'@'localhost';`
            2. 再赋予权限：`GRANT SELECT, INSERT ON phpmyadmin.* TO 'phpmyadmin'@'localhost';`
    7. 查看

        1. 查看和修改密码策略：`SHOW VARIABLES LIKE 'validate_password%';`，`set global validate_password_policy=MEDIUM;`
        2. 查看用户的权限：`show grants for phpmyadmin;`，具体查看用户在某数据库的权限：`show grants for 'phpmyadmin'@'host' on db_name;`，如果是想要查看自己有的权限：`SHOW GRANTS;`
        3. 详细查看用户的权限：`select * from mysql.user where user='xxx'\G`，这里的 `\G` 会将查询结果按照更易读的格式进行显示
3. 数据库的备份和迁移

    1. 优先推荐使用 [phpmyadmin](https://www.phpmyadmin.net/)

        1. 在两台 host 中都装入 phpmyadmin，然后善用其导入和导出功能
        2. 推荐按照前文所示创建用户和数据库的方法，创建一个 phpmyadmin@localhost 的账号，为止配置密码，然后登录之
        3. 需要安装 php 及其配套插件：`sudo apt install php php-fpm php-cgi php-mysql`；输入：`php -m` 来获取的当前已安装的插件信息；不同的 debian 源可能默认使用不同的 php 版本，下文根据具体版本号具体修改
        4. nginx 的配置参考如下：

            ```nginx
            server {
            	listen 80;
            	listen [::]:80;

            	root /home/app/phpmyadmin;
            	server_name localhost;

            	index index.php;

            	location / {
            		# uncomment to resolve CORS
            		add_header 'Access-Control-Allow-Origin' '*';
            		add_header 'Access-Control-Allow-Credentials' 'true';
            		add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
            		add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type';
            	}

            	client_max_body_size  64m;
            	error_page 404 /404.php;
            	error_page 500 502 503 504 /50x.html;
            	location /50x.html {
            		root /usr/share/nginx/html;
            	}

            	location ~ \.php$ {
            		fastcgi_pass unix:/run/php/php8.1-fpm.sock;
            		fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
            		include fastcgi_params;
            	}
            }
            ```
        5. 如果数据库导出时文件很大，默认情况下 php 允许导入的文件有大小限制，需要修改 `/etc/php/8.1/fpm/php.ini` 文件中的以下内容：

            ```ini
            upload_max_filesize = 10M
            post_max_size = 10M
            ```

            修改成实际允许的大小，反正超过要导入的文件的大小就行了（nginx 中有一项 `client_max_body_size` 也要修改），然后重启 php-fpm：`systemctl restart php8.1-fpm.service`
    2. mysql 命令行导出文件方法

        1. 建议使用相同的 mysql 版本，**数据无价、谨慎操作**
        2. 登录数据库：`mysql -u phpmyadmin -p`；查看现存的数据库：`show DATABASES;`，确定要导出的数据库名称
        3. 在命令行输入：`mysqldump -u phpmyadmin -p db_name > db_name_backup.sql`，输入密码即可导出
        4. 将导出的文件转移到新服务器，在新服务器上先创建对应 db：`create DATABSAE db_name`，导入：`mysql -u phpmyadmin -p db_name < db_name_backup.sql`

### others

1. 彻底删除 mysql 数据库程序

    1. 查看系统中所有 mysql 依赖项：`sudo dpkg --list | grep mysql`
    2. 卸载：`sudo apt remove mysql-common`，`sudo apt autoremove --purge mysql-server`
    3. 清理残留数据，涉及到数据库内容，注意备份：`sudo dpkg -l | grep ^rc | awk '{print$2}' | sudo xargs dpkg -P`
    4. 卸载残余依赖项：`sudo apt-get autoremove --purge mysql-apt-config`
2. 为 mysql 配置 ssl 加密登录

    1. 检查 mysql 是否使用 ssl：`show variables like '%ssl%';`
3. 忘记了root密码

    1. 修改配置文件 `sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf`，找到 `[mysqld]` 这一代码块，在其中加上 `skip-grant-tables` 这行内容，这一配置的作用是开启免密码登录 root 账号
    2. 重新设置root密码

        1. 以 root 进入数据库，遇到要输入密码不用管直接回车：`mysql -u root -p`
        2. 输入 sql 指令：

            1. 使用内置权限数据库：`use mysql;`
            2. 输入新密码：`update user set authentication_string=password("new_password") where user="root";`
            3. 刷新：`flush privileges;`，然后退出即可
            4. 重新将前面的 `skip-grant-tables` 注释掉，关闭免密登录
4. root 账户默认是禁止其他用户登录的，如果想要任意账户可以登录 root，按照以下操作

    1. 以 root 身份进入数据库：`sudo mysql`
    2. 输入以下 sql 语句：

        1. 使用内置权限数据库：`use mysql;`
        2. 查看账户登录时的验证策略：`select user, plugin from user;`
        3. 这里 root 是 `auth_socket`，将其修改成 `mysql_native_password` 即可：`update user set authentication_string=password("new_password"),plugin='mysql_native_password' where user='root';`，此时再看验证策略可以发现已经修改
        4. 刷新：`flush privileges;`

## postgresql

PostgreSQL 是比较新的数据库（相较于 MySQL），稳定性、功能强大、扩展灵活、还有好用的快捷键。

### sql common

1. 数据库

    1. 显示数据库：`\l` 或 `\list`
    2. 创建数据库：`CREATE DATABASE db_name;`
    3. 删除数据库：`DROP DATABASE db_name;`
    4. 选择数据库：`\c db_name`
2. 表

    1. 创建表：`CREATE TABLE table_name (column_1 data_type, column_2 data_type, ...);`
    2. 删除表：`DROP TABLE table_name;`
    3. 显示所有表：`\dt`
    4. 展示表的结构：`\d table_name;`
3. 数据（CRUD）

    1. 插入数据：`INSERT INTO table_name (column_1, column_2, ...) VALUES (value_1, value_2, ...);`
    2. 查询：`SELECT column_name FROM table_name WHERE condition;`
    3. 更新数据：`UPDATE table_name SET column_name = new_value WHERE condition;`
    4. 删除：`DELETE FROM table_name WHERE condition;`

### installation

1. debian 系可以直接使用包管理器安装：`sudo apt install postgresql postgresql-contrib`
2. 初始化数据库并创建一个用户：PostgreSQL 安装完成后会默认创建一个名为 `postgres` 的用户和数据库，先切换到这个用户：`sudo -i -u postgres`
3. 之后可以直接管理数据库：`psql`

### init

创建一个新的数据库用户和数据库。以 `db_user` 为例：

1. 创建新用户：`createuser --interactive --pwprompt`，按照提示输入密码
2. 创建新数据库：`createdb db_name`
3. 授权：`GRANT ALL PRIVILEGES ON DATABASE db_name TO db_user;`

### usage

1. 连接数据库

    1. 使用 `psql` 命令行工具：`psql -d db_name -U user_name`
    2. 如果需要远程连接，修改配置文件，主配置文件在 `/etc/postgresql/x/main/` 下，x 是版本号

        1. 修改 `/etc/postgresql/x/main/postgfresql.conf`，修改或添加 `listen_addresses = '*'`，可以接受任意 ip 的连接
        2. 修改 `/etc/postgresql/x/main/pg_hba.conf`，只允许本机通过密码认证登录，修改为上面内容后即可以对任意 ip 访问进行密码验证

            ```ini
            # TYPE  DATABASE  USER  CIDR-ADDRESS  METHOD
            host  all  all 0.0.0.0/0 md5
            ```
        3. 重启 postgresql：`sudo systemctl restart postgresql`
2. 创建普通用户和数据库

    1. 登录到 PostgreSQL 控制台：`sudo -u postgres psql`
    2. 创建用户和数据库的命令与初始化时相同

        1. 列出所有数据库：`\l`
        2. 创建数据库：`CREATE DATABASE db_name;`
        3. 切换数据库：`\c db_name`
        4. 创建用户，通式：`CREATE USER username WITH PASSWORD 'password';`

            1. 只允许本地登录：`CREATE USER username WITH PASSWORD 'new_password';`
            2. 默认允许任意登录，要限制登录 IP，需在 pg_hba.conf 文件中进行配置
        5. 授权，通式：`GRANT privileges ON DATABASE dbname TO username;`

            1. 为 username 授予数据库 db_name 中使用 SELECT、INSERT、UPDATE 的权力：`GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO username;`
            2. 为 username 授予数据库 db_name 中所有权力：`GRANT ALL PRIVILEGES ON DATABASE db_name TO username;`
3. 数据库的备份和迁移

    1. pgAdmin 没有 phpmyadmin 好用，自行决断，也是参考着创建相应用户、授权、导入和导出
    2. 使用命令行

        1. 使用 `pg_dump` 进行数据库备份：`pg_dump -U user_name -W db_name > db_name_backup.sql`
        2. 恢复，在新服务器上先创建对应数据库：`CREATE DATABASE db_name;`，然后使用 `psql` 导入备份文件：`psql -U user_name db_name < db_name_backup.sql`
    3. 倒反天罡！使用工具将 postgresql 转到 mysql，有两种方式

        1. 使用 pg2mysql
        2. 将 postgresql 的内容导出成 csv，然后将 csv 导入到 mysql

### others

1. 修改密码：在 `psql` 控制台，执行 `ALTER USER user_name WITH PASSWORD 'new_password';` 来修改用户密码
2. 查看活跃查询：`SELECT * FROM pg_stat_activity;`
3. 更改端口或允许远程连接：编辑 `postgresql.conf` 和 `pg_hba.conf` 文件，然后重启 PostgreSQL 服务

## splite3

SQLite 是一个嵌入式 SQL 数据库引擎，不需要一个单独的服务器进程，在移动设备和桌面应用中非常流行，即开即用

### sql common

1. SQLite 的数据库是一个文件 `xxx.db`，不需要创建数据库的命令，使用 SQLite 时，可以直接操作数据库文件
2. 表

    1. 创建表：`CREATE TABLE table_name (column_1 data_type, column_2 data_type, ...);`
    2. 删除表：`DROP TABLE table_name;`
    3. 显示所有表：`.tables`
    4. 展示表的结构：`.schema table_name`
3. 数据（crud）

    1. 插入数据：`INSERT INTO table_name (column_1, column_2, ...) VALUES (value_1, value_2, ...);`
    2. 查询：`SELECT column_name FROM table_name WHERE condition;`
    3. 更新数据：`UPDATE table_name SET column_name = new_value WHERE condition;`
    4. 删除：`DELETE FROM table_name WHERE condition;`

### installation

在大多数操作系统上，SQLite 无需安装。它通常已经包含在标准的开发包中，或者可以轻松地作为一个简单的可执行文件下载。

### usage

1. 使用 SQLite，通常直接通过命令行工具 `sqlite3` 连接和操作数据库文件：

    1. 打开或创建数据库文件：`sqlite3 db_name.db`
    2. 然后你可以直接在命令行中执行 SQL 命令。
2. 数据库的备份和迁移

    1. 使用 `.backup` 命令进行数据库备份：`.backup db_name_backup.db`
    2. 恢复，直接使用备份的数据库文件即可

### others

1. 查看所有的 SQLite 命令：`.help`
2. 导出数据库为 SQL 文件：`.dump > db_name.sql`
3. 改变输出格式以便阅读：`.mode column` 和 `.headers on`

## references

1. [mysql出现ERROR1698(28000):Access denied for user root@localhost错误解决方法](https://www.cnblogs.com/cpl9412290130/p/9583868.html)
2. [MySQL创建用户与授权](https://www.jianshu.com/p/d7b9c468f20d)
3. [解決 MySQL 錯誤 – ERROR 1819 (HY000)](https://www.ltsplus.com/mysql/fix-mysql-error-1819)
4. [mysql初始化后未找到配置文件](https://blog.csdn.net/Drink_hot_water/article/details/121094566)
5. [nginx配置SSL证书实现https服务](https://www.cnblogs.com/tugenhua0707/p/10940977.html)
6. [Ubuntu18 安装 MySql8.0](https://blog.csdn.net/baidu_41560343/article/details/102936428)
7. [Ubuntu18.04彻底删除MySQL数据库](https://blog.csdn.net/iehadoop/article/details/82961264)
8. [谈谈 MySQL 的 JSON 数据类型](https://segmentfault.com/a/1190000024445924)
9. [mysql5.7+ 关闭ONLY_FULL_GROUP_BY](https://blog.csdn.net/ieayoio/article/details/79543899)
10. [如何设置PostgreSQL允许被远程访问](http://lazybios.com/2016/11/how-to-make-postgreSQL-can-be-accessed-from-remote-client/)
11. [How to Convert PostgreSQL to MySQL in 3 Ways?](https://www.vinchin.com/database-tips/postgresql-to-mysql.html)
12. [Nginx 代理 Mysql 端口并开启 SSL](https://blog.csdn.net/lhp3000/article/details/107519724)