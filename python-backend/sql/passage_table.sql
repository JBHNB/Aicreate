-- 文章创作结果表（执行前请先 USE 你的库，与 create_table.sql 一致）
CREATE TABLE IF NOT EXISTS passage
(
    id         bigint auto_increment comment 'id' primary key,
    userId     bigint                             not null comment '作者用户 id',
    title      varchar(512)                       not null comment '标题',
    prompt     varchar(2048)                      null comment '创作提示/主题',
    content    mediumtext                         not null comment '正文（AI 生成或占位）',
    createTime datetime default CURRENT_TIMESTAMP not null comment '创建时间',
    updateTime datetime default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP comment '更新时间',
    isDelete   tinyint    default 0             not null comment '是否删除',
    INDEX idx_userId_createTime (userId, createTime)
) comment '文章/创作记录' collate utf8mb4_unicode_ci;
