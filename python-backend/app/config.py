"""配置管理（对齐官方 ai-passage-creator + 本地兼容）"""

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """应用配置：数据库 / Redis / Session / AI / 配图 / 支付等"""

    server_port: int = 8567
    server_host: str = "0.0.0.0"

    db_host: str
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str

    redis_host: str
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    session_secret_key: str
    session_max_age: int = 2592000

    password_salt: str

    # AI（DashScope OpenAI 兼容）
    dashscope_api_key: str = ""
    dashscope_model: str = "qwen-plus"
    # 兼容旧 .env：LLM_MODEL；若为空则用 dashscope_model
    llm_model: str = ""

    pexels_api_key: str = ""

    tencent_cos_secret_id: str = ""
    tencent_cos_secret_key: str = ""
    tencent_cos_region: str = ""
    tencent_cos_bucket: str = ""
    tencent_cos_domain: str = ""

    nano_banana_api_key: str = ""
    # gemini：NANO_BANANA_API_KEY；dashscope：DASHSCOPE_API_KEY。可用 AI_IMAGE_PROVIDER 作为备用变量名。
    nano_banana_provider: str = Field(
        default="gemini",
        validation_alias=AliasChoices(
            "NANO_BANANA_PROVIDER",
            "AI_IMAGE_PROVIDER",
        ),
    )
    nano_banana_model: str = "gemini-2.5-flash-image"
    nano_banana_aspect_ratio: str = "16:9"
    nano_banana_image_size: str = "1K"
    nano_banana_output_mime_type: str = "image/png"
    # 仅当 nano_banana_provider=dashscope 时生效（参见阿里云万相文生图文档）
    dashscope_wanx_model: str = "wanx-v1"
    dashscope_wanx_base_url: str = "https://dashscope.aliyuncs.com"
    # 万相创建任务易触发 Throttling.RateQuota：见 nano_banana_service 串行 + 退避重试
    dashscope_wanx_create_max_retries: int = 8
    dashscope_wanx_retry_base_seconds: float = 2.0
    dashscope_wanx_min_interval_seconds: float = 0.55

    mermaid_cli_command: str = "mmdc"
    mermaid_background_color: str = "transparent"
    mermaid_output_format: str = "svg"
    mermaid_width: int = 1200
    mermaid_timeout: int = 30000
    # 未安装 @mermaid-js/mermaid-cli 时，是否用 Kroki 公网接口渲染（需能访问外网）
    mermaid_enable_remote_fallback: bool = True
    mermaid_remote_kroki_url: str = "https://kroki.io"

    iconify_api_url: str = "https://api.iconify.design"
    iconify_search_limit: int = 10
    iconify_default_height: int = 64
    iconify_default_color: str = ""

    emoji_pack_search_url: str = "https://cn.bing.com/images/async"
    emoji_pack_suffix: str = "表情包"
    emoji_pack_timeout: int = 10000

    svg_diagram_default_width: int = 800
    svg_diagram_default_height: int = 600
    svg_diagram_folder: str = "svg-diagrams"

    agent_image_max_concurrency: int = 3
    agent_image_fail_fast: bool = True

    # 智能体 LLM / JSON 重试
    agent_llm_max_retries: int = 3
    agent_llm_retry_base_seconds: float = 1.5

    # Reviewer：正文后审核，低于 pass_score 且未 passed 时用 revisedContent 替换
    agent_reviewer_enabled: bool = True
    agent_reviewer_pass_score: int = 75

    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_success_url: str = "http://localhost:5173/vip?success=true"
    stripe_cancel_url: str = "http://localhost:5173/vip?cancelled=true"

    # RAG 系统知识库
    rag_enabled: bool = True
    dashscope_embedding_model: str = "text-embedding-v3"
    rag_top_k: int = 5
    rag_chunk_size: int = 600
    rag_chunk_overlap: int = 80
    rag_min_score: float = 0.35
    rag_embed_batch_size: int = 10
    chroma_persist_dir: str = "./data/chroma"
    knowledge_files_dir: str = "./data/knowledge_files"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        # Windows 记事本等保存的 UTF-8 BOM 会导致首项解析异常；utf-8-sig 可去掉 BOM
        env_file_encoding="utf-8-sig",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace("mysql+pymysql", "mysql")

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}@{self.redis_host}:"
                f"{self.redis_port}/{self.redis_db}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def resolved_llm_model(self) -> str:
        """passage 模块与官方 article 共用：优先 LLM_MODEL，否则 DASHSCOPE_MODEL"""
        v = (self.llm_model or "").strip()
        return v or self.dashscope_model

    @property
    def chroma_persist_path(self) -> Path:
        p = Path(self.chroma_persist_dir)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def knowledge_files_path(self) -> Path:
        p = Path(self.knowledge_files_dir)
        return p if p.is_absolute() else BASE_DIR / p


settings = Settings()
