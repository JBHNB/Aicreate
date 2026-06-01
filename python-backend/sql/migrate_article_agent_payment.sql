-- 对齐官方「AI 核心创作」相关表与字段（在已有库上执行一次）
-- 使用前请改为你的库名：下面默认 ai_passage_creator
--
-- 兼容说明：`ADD COLUMN IF NOT EXISTS` 仅 MySQL 8.0.12+ 支持；Docker 常用 5.7 会报 1064。
-- 本脚本使用普通 ADD COLUMN。若某列已存在，对应语句会报 Duplicate column，跳过即可。

USE ai_passage_creator;

-- ----- user：quota / vipTime -----
-- 已单独执行过 patch_user_quota_vip.sql、或 create_table 里已有 quota/vipTime 时：不要取消注释下面几行，否则会 Duplicate column。
-- 仅有「老库从未加过这两列」时：删掉下面 4 行行首的 -- 再执行。
-- ALTER TABLE `user` ADD COLUMN quota int default 5 not null comment '剩余配额' AFTER userRole;
-- ALTER TABLE `user` ADD COLUMN vipTime DATETIME NULL COMMENT '成为会员时间';
-- UPDATE `user` SET quota = 5 WHERE quota IS NULL;

-- ----- article / agent_log（官方基础DDL）-----
CREATE TABLE IF NOT EXISTS article
(
    id              bigint auto_increment comment 'id' primary key,
    taskId          varchar(64)                        not null comment '任务ID（UUID）',
    userId          bigint                             not null comment '用户ID',
    topic           varchar(500)                       not null comment '选题',
    mainTitle       varchar(200)                       null comment '主标题',
    subTitle        varchar(300)                       null comment '副标题',
    outline         json                               null comment '大纲（JSON格式）',
    content         text                               null comment '正文（Markdown格式）',
    fullContent     text                               null comment '完整图文（Markdown格式，含配图）',
    coverImage      varchar(512)                       null comment '封面图 URL',
    images          json                               null comment '配图列表（JSON数组，包含封面图 position=1）',
    status          varchar(20) default 'PENDING'      not null comment '状态：PENDING/PROCESSING/COMPLETED/FAILED',
    errorMessage    text                               null comment '错误信息',
    createTime      datetime    default CURRENT_TIMESTAMP not null comment '创建时间',
    completedTime   datetime                           null comment '完成时间',
    updateTime      datetime    default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP comment '更新时间',
    isDelete        tinyint     default 0              not null comment '是否删除',
    UNIQUE KEY uk_taskId (taskId),
    INDEX idx_userId (userId),
    INDEX idx_status (status),
    INDEX idx_createTime (createTime),
    INDEX idx_userId_status (userId, status)
) comment '文章表' collate = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS agent_log
(
    id              bigint auto_increment comment 'id' primary key,
    taskId          varchar(64)                        not null comment '任务ID',
    agentName       varchar(50)                        not null comment '智能体名称',
    startTime       datetime                           not null comment '开始时间',
    endTime         datetime                           null comment '结束时间',
    durationMs      int                                null comment '耗时（毫秒）',
    status          varchar(20)                        not null comment '状态：SUCCESS/FAILED',
    errorMessage    text                               null comment '错误信息',
    prompt          text                               null comment '使用的Prompt',
    inputData       json                               null comment '输入数据（JSON格式）',
    outputData      json                               null comment '输出数据（JSON格式）',
    createTime      datetime    default CURRENT_TIMESTAMP not null comment '创建时间',
    updateTime      datetime    default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP comment '更新时间',
    isDelete        tinyint     default 0              not null comment '是否删除',
    INDEX idx_taskId (taskId),
    INDEX idx_agentName (agentName),
    INDEX idx_status (status),
    INDEX idx_createTime (createTime)
) comment '智能体执行日志表' collate = utf8mb4_unicode_ci;

-- ----- article 增量字段 -----
-- 若某列已存在会报 Duplicate column：在该行行首加 -- 注释掉即可。
-- DEFAULT 必须用英文单引号，例如 DEFAULT 'PENDING'；不要用双引号 "PENDING"。
-- AFTER 后的列名要与库里一致，一般为 subTitle（勿写成 subtitle）。
ALTER TABLE article ADD COLUMN style VARCHAR(20) NULL COMMENT '文章风格：tech/emotional/educational/humorous' AFTER topic;
ALTER TABLE article ADD COLUMN phase VARCHAR(50) DEFAULT 'PENDING' COMMENT '当前阶段' AFTER status;
ALTER TABLE article ADD COLUMN titleOptions JSON NULL COMMENT '标题方案列表' AFTER subTitle;
ALTER TABLE article ADD COLUMN userDescription TEXT NULL COMMENT '用户补充描述' AFTER topic;
-- 勿写 AFTER userDescription：若上一句未成功执行，会报 1054 Unknown column。改为依附表中已有的 outline 列。
ALTER TABLE article ADD COLUMN enabledImageMethods JSON NULL COMMENT '允许的配图方式列表' AFTER outline;

CREATE TABLE IF NOT EXISTS payment_record (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    userId BIGINT NOT NULL COMMENT '用户ID',
    stripeSessionId VARCHAR(128) COMMENT 'Stripe Checkout Session ID',
    stripePaymentIntentId VARCHAR(128) COMMENT 'Stripe 支付意向ID',
    amount DECIMAL(10,2) NOT NULL COMMENT '金额（美元）',
    currency VARCHAR(8) DEFAULT 'usd' COMMENT '货币',
    status VARCHAR(32) NOT NULL COMMENT '状态：PENDING/SUCCEEDED/FAILED/REFUNDED',
    productType VARCHAR(32) NOT NULL COMMENT '产品类型：VIP_PERMANENT',
    description VARCHAR(256) COMMENT '描述',
    refundTime DATETIME NULL COMMENT '退款时间',
    refundReason VARCHAR(512) NULL COMMENT '退款原因',
    createTime DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updateTime DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_userId (userId),
    INDEX idx_stripeSessionId (stripeSessionId),
    INDEX idx_status (status),
    INDEX idx_createTime (createTime)
) COMMENT '支付记录表' COLLATE = utf8mb4_unicode_ci;
