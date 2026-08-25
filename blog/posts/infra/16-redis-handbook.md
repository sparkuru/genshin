---
title: "app | Redis，一种高速缓存数据库"
description: "一种高性能的 NoSql 数据库。"
date: "2022-03-21T10:52:00.000Z"
updated: "2024-02-21T12:10:35.000Z"
tags: []
draft: false
layout: "post"
slug: "redis-handbook"
---

## **Redis**

**Redis 是一个高性能的key-value数据库。redis会周期性的把更新的数据写入磁盘或者把修改操作写入追加的记录文件，并且在此基础上实现了master-slave(主从)同步。完全实现了**[**发布/订阅**](https://baike.baidu.com/item/发布%2F订阅)**机制，使得从数据库在任何地方同步树时，可订阅一个频道并接收主服务器完整的消息发布记录。同步对读取操作的可扩展性和数据冗余很有帮助。**

## **安装 Redis**

**ubuntu 的 apt源 默认自带 redis-server**

**直接安装即可**

> **sudo apt install redis-server**

## **语法**

**放一点简单的 redis 语法 那确实简洁**

```
 # 登录 redis
 redis-cli
 
 # 查看所有 key
 keys *
 
 # 增加一条 key1
 set key1 "Hello"
 
 # 打印 key1
 get key1
 
 # 增加一个列表 list
 LPUSH list a
 ## 从左插入列表
 LPUSH list b
 ## 从右插入列表
 RPUSH list c
 ## 按左到右打印列表
 LRANGE list 0 3
 
  # 删除key4
  del key4
```

## **配置 Redis**

**出于远程访问，安全性等需求，需要配置 redis**

**修改 redis 的配置文件**

> **sudo vim /etc/redis/redis.conf**
>
> **修改完记得重启服务**
>
> **sudo service redis-server restart**

**打开密码登录 想要设置一个密码为 password**

> 1. **在 redis.conf 中找到 # requirepass xxx 这行**
> 2. **去掉注释 然后 把xxx改成 password**
> 3. **保存且重启redis即可**
> 4. **在添加了密码之后 尝试登录还是会进入redis 但是无法操作****输入 redis-cli -a password 验证登录**

**打开远程登录**

> 1. **redis默认不允许远程登录**
> 2. **在 redis.conf 中找到 bind 127.0.0.1 这行 在前面加#注释这行**
> 3. **保存重启redis**
> 4. **查看redis在本地监听的端口****sudo netstat -anp | grep redis****默认监听 6379 端口****而且在上一步之后 就不会再出现 127.0.0.1 字样**
> 5. **远程登录****redis-cli -a password -h 这台机子的ip地址**

## **参考链接**

**1，**[**Redis - 百度百科**](https://baike.baidu.com/item/Redis/6549233)

**2，**[**在Ubuntu中安装Redis**](http://blog.fens.me/linux-redis-install/)

**3，**
