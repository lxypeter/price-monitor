drop database if exists price_monitor;

create database price_monitor;

use price_monitor;

create table user (
    `id` varchar(50) not null,
    `username` varchar(50) not null,
    `email` varchar(50) not null,
    `password` varchar(50) not null,
    `nickname` varchar(50) not null,
    `gender` char(1) not null,
    `image` varchar(500),
    `create_time` datetime not null,
    unique key `idx_email` (`email`),
    unique key `idx_username` (`username`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table item (
    `id` varchar(50) not null,
    `mall_type` varchar(50) not null,
    `item_id` varchar(50) not null,
    `name` varchar(200) not null,
    `url` varchar(200) not null,
    `image_url` varchar(200) not null,
    `shop_name` varchar(200) not null,
    `state` varchar(50) not null,
    `monitor_num` int not null,
    `send_city` varchar(50) not null,
    `create_time` datetime not null,
    primary key (`id`)
) engine=innodb default charset=utf8;

create table item_price (
    `id` varchar(50) not null,
    `item_p_id` varchar(50) not null,
    `name` varchar(50) not null,
    `pvs` varchar(100) not null,
    `price` varchar(50) not null,
    `stock` int not null,
    `updated_time` datetime not null,
    primary key (`id`)
) engine=innodb default charset=utf8;

create table item_pvs (
    `id` varchar(50) not null,
    `item_p_id` varchar(50) not null,
    `group_id` varchar(50) not null,
    `name` varchar(50) not null,
    `pvs` varchar(50) not null,
    primary key (`id`)
) engine=innodb default charset=utf8;

create table user_item (
    `user_id` varchar(50) not null,
    `item_p_id` varchar(50) not null
) engine=innodb default charset=utf8;
