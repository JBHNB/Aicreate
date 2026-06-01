-- Patch user table: quota + vipTime
-- Use ASCII semicolon ";" only (not Chinese "；")
-- In DBeaver: run line 9 alone (Ctrl+Enter), then line 10, then line 11, then line 12

SET NAMES utf8mb4;

USE ai_passage_creator;

ALTER TABLE `ai_passage_creator`.`user` ADD COLUMN quota int NOT NULL DEFAULT 5 COMMENT 'quota' AFTER userRole;

ALTER TABLE `ai_passage_creator`.`user` ADD COLUMN vipTime datetime NULL COMMENT 'vipTime';

UPDATE `ai_passage_creator`.`user` SET quota = 5 WHERE quota IS NULL;
