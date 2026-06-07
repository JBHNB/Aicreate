-- RAG 系统知识库：文档元数据表（向量存 ChromaDB）
USE ai_passage_creator;

CREATE TABLE IF NOT EXISTS knowledge_document
(
    id           bigint auto_increment comment 'id' primary key,
    title        varchar(200)                       not null comment '文档标题',
    fileName     varchar(255)                       not null comment '原始文件名',
    fileType     varchar(20)                        not null comment '文件类型：txt/md',
    fileSize     bigint       default 0             not null comment '文件大小（字节）',
    status       varchar(20)  default 'processing' not null comment '状态：processing/ready/failed',
    chunkCount   int          default 0             not null comment '分块数量',
    errorMessage text                               null comment '失败原因',
    createdBy    bigint                             not null comment '上传管理员用户ID',
    createTime   datetime     default CURRENT_TIMESTAMP not null comment '创建时间',
    updateTime   datetime     default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP comment '更新时间',
    isDelete     tinyint      default 0             not null comment '是否删除',
    INDEX idx_status (status),
    INDEX idx_createTime (createTime),
    INDEX idx_isDelete (isDelete)
) comment '系统知识库文档' collate = utf8mb4_unicode_ci;
