"""文章多智能体编排器"""

import logging
from typing import TYPE_CHECKING

from app.agent.agents.content_generator import ContentGeneratorAgent
from app.agent.agents.content_merger import ContentMergerAgent
from app.agent.agents.image_analyzer import ImageAnalyzerAgent
from app.agent.agents.outline_generator import OutlineGeneratorAgent
from app.agent.agents.reviewer import ReviewerAgent
from app.agent.agents.title_generator import TitleGeneratorAgent
from app.config import settings
from app.agent.context.stream_handler import StreamHandlerContext
from app.models.enums import SseMessageTypeEnum
from app.schemas.article import ArticleState

if TYPE_CHECKING:
    from app.services.article_agent_service import ArticleAgentService

logger = logging.getLogger(__name__)


class ArticleAgentOrchestrator:
    """多智能体编排器"""

    def __init__(self):
        self.title_agent = TitleGeneratorAgent()
        self.outline_agent = OutlineGeneratorAgent()
        self.content_agent = ContentGeneratorAgent()
        self.reviewer_agent = ReviewerAgent()
        self.image_analyzer_agent = ImageAnalyzerAgent()
        self.content_merger_agent = ContentMergerAgent()

    async def execute_phase1(
        self,
        service: "ArticleAgentService",
        state: ArticleState,
        stream_handler,
    ):
        stream_context = StreamHandlerContext(stream_handler)
        logger.info("阶段1：开始生成标题方案, taskId=%s", state.task_id)
        await self.title_agent.run(service, state)
        stream_context.emit(SseMessageTypeEnum.AGENT1_COMPLETE.value)
        logger.info(
            "阶段1：标题方案生成成功, taskId=%s, optionsCount=%s",
            state.task_id,
            len(state.title_options or []),
        )

    async def execute_phase2(
        self,
        service: "ArticleAgentService",
        state: ArticleState,
        stream_handler,
    ):
        stream_context = StreamHandlerContext(stream_handler)
        logger.info("阶段2：开始生成大纲, taskId=%s", state.task_id)
        await self.outline_agent.run(service, state, stream_context.emit)
        stream_context.emit(SseMessageTypeEnum.AGENT2_COMPLETE.value)
        logger.info("阶段2：大纲生成成功, taskId=%s", state.task_id)

    async def execute_phase3(
        self,
        service: "ArticleAgentService",
        state: ArticleState,
        stream_handler,
    ):
        stream_context = StreamHandlerContext(stream_handler)
        max_retries = max(0, settings.agent_content_review_max_retries)

        for attempt in range(max_retries + 1):
            state.content_rewrite_attempt = attempt
            logger.info(
                "阶段3：开始生成正文, taskId=%s, rewriteAttempt=%s",
                state.task_id,
                attempt,
            )
            await self.content_agent.run(service, state, stream_context.emit)
            stream_context.emit(SseMessageTypeEnum.AGENT3_COMPLETE.value)

            if not settings.agent_reviewer_enabled:
                break

            # 最后一轮才允许 Reviewer 直接用 revisedContent 替换；前面几轮留给 Agent3 重写
            state.apply_reviewer_revision = attempt >= max_retries
            logger.info(
                "阶段3：开始审核正文, taskId=%s, rewriteAttempt=%s",
                state.task_id,
                attempt,
            )
            await self.reviewer_agent.run(service, state)
            stream_context.emit(SseMessageTypeEnum.AGENT_REVIEWER_COMPLETE.value)

            if service.is_content_review_acceptable(state):
                logger.info(
                    "Reviewer 通过, taskId=%s, score=%s, rewriteAttempt=%s",
                    state.task_id,
                    state.review_score,
                    attempt,
                )
                break

            if attempt >= max_retries:
                logger.warning(
                    "Reviewer 未达标且已达最大重写次数, taskId=%s, score=%s",
                    state.task_id,
                    state.review_score,
                )
                break

            logger.info(
                "Reviewer 未达标，准备重跑 Agent3, taskId=%s, score=%s, issues=%s",
                state.task_id,
                state.review_score,
                (state.review_issues or [])[:3],
            )

        logger.info("阶段3：开始分析配图需求, taskId=%s", state.task_id)
        await self.image_analyzer_agent.run(service, state)
        stream_context.emit(SseMessageTypeEnum.AGENT4_COMPLETE.value)

        logger.info("阶段3：开始生成配图, taskId=%s", state.task_id)
        await service.agent5_generate_images(state, stream_context.emit)
        stream_context.emit(SseMessageTypeEnum.AGENT5_COMPLETE.value)

        logger.info("阶段3：开始图文合成, taskId=%s", state.task_id)
        self.content_merger_agent.run(service, state)
        stream_context.emit(SseMessageTypeEnum.MERGE_COMPLETE.value)

