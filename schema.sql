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
    `create_time` real not null,
    unique key `idx_email` (`email`),
    key `idx_create_time` (`create_time`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table item (
    `id` varchar(50) not null,
    `mall_type` varchar(50) not null,
    `item_id` varchar(50) not null,
    `name` varchar(50) not null,
    `url` varchar(200) not null,
    `image_url` varchar(200) not null,
    `shop_name` varchar(200) not null,
    `state` varchar(50) not null,
    `create_time` real not null,
    key `idx_create_time` (`create_time`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table item_price (
    `id` varchar(50) not null,
    `item_id` varchar(50) not null,
    `name` varchar(50) not null,
    `pvs` varchar(100) not null,
    `stock` int not null,
    `updated_time` real not null,
    key `idx_updated_time` (`updated_time`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table item_pv (
    `id` varchar(50) not null,
    `item_id` varchar(50) not null,
    `name` varchar(50) not null,
    `pv` varchar(50) not null,
    primary key (`id`)
) engine=innodb default charset=utf8;
