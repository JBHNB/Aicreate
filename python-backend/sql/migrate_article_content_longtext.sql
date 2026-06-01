-- 将 article 正文改为 LONGTEXT；封面改为 TEXT（data URL 常远超 varchar(512)，否则阶段3保存失败）
-- 在 DBeaver 等对 ai_passage_creator 执行一次即可

USE ai_passage_creator;

ALTER TABLE article
    MODIFY COLUMN content LONGTEXT NULL COMMENT '正文（Markdown格式）',
    MODIFY COLUMN fullContent LONGTEXT NULL COMMENT '完整图文（Markdown格式，含配图）',
    MODIFY COLUMN coverImage TEXT NULL COMMENT '封面图 URL 或 data URL（可能很长）';
