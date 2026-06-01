"""文章异步任务服务"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from app.schemas.article import ArticleState, OutlineSection, OutlineResult, TitleResult
from app.models.enums import ArticlePhaseEnum, ArticleStatusEnum, SseMessageTypeEnum
from app.services.article_agent_service import ArticleAgentService
from app.services.article_service import ArticleService
from app.managers.sse_manager import sse_emitter_manager
from app.database import database

logger = logging.getLogger(__name__)


class ArticleAsyncService:
    """文章异步任务服务"""

    def __init__(self):
        self._running_phase2: set[str] = set()
        self._running_phase3: set[str] = set()

    def is_phase2_running(self, task_id: str) -> bool:
        return task_id in self._running_phase2

    def is_phase3_running(self, task_id: str) -> bool:
        return task_id in self._running_phase3

    def start_phase2(self, task_id: str, *, force: bool = False) -> None:
        """启动阶段2后台任务（若已在跑则跳过，force 时强制重跑）。"""
        if task_id in self._running_phase2:
            if not force:
                logger.info("阶段2 已在执行中, taskId=%s", task_id)
                return
            self._running_phase2.discard(task_id)

        async def runner() -> None:
            self._running_phase2.add(task_id)
            try:
                print(f"[文章创作] 阶段2 runner 开始 taskId={task_id}", flush=True)
                await self.execute_phase2(task_id)
            except Exception as e:
                logger.error(
                    "阶段2后台任务异常, taskId=%s, error=%s",
                    task_id,
                    e,
                    exc_info=True,
                )
            finally:
                self._running_phase2.discard(task_id)

        asyncio.create_task(runner())

    def start_phase3(self, task_id: str, *, force: bool = False) -> None:
        """启动阶段3后台任务（若已在跑则跳过，force 时强制重跑）。"""
        if task_id in self._running_phase3:
            if not force:
                logger.info("阶段3 已在执行中, taskId=%s", task_id)
                return
            self._running_phase3.discard(task_id)

        async def runner() -> None:
            self._running_phase3.add(task_id)
            try:
                print(f"[文章创作] 阶段3 runner 开始 taskId={task_id}", flush=True)
                await self.execute_phase3(task_id)
            except Exception as e:
                logger.error(
                    "阶段3后台任务异常, taskId=%s, error=%s",
                    task_id,
                    e,
                    exc_info=True,
                )
            finally:
                self._running_phase3.discard(task_id)

        asyncio.create_task(runner())

    async def catch_up_sse(self, task_id: str) -> None:
        """
        SSE 连接建立后，若阶段任务已先完成，补发 TITLES_GENERATED / OUTLINE_GENERATED 等，
        避免前端一直停在「创建任务」。
        """
        article_service = ArticleService(database)
        try:
            article = await article_service.get_by_task_id(task_id)
            if not article:
                return

            status = article.get("status")
            phase = article.get("phase")

            if status == ArticleStatusEnum.FAILED.value:
                self._send_sse_message(
                    task_id,
                    SseMessageTypeEnum.ERROR,
                    {"message": article.get("errorMessage") or "任务失败"},
                )
                sse_emitter_manager.complete(task_id)
                return

            if phase == ArticlePhaseEnum.TITLE_SELECTING.value:
                raw = article.get("titleOptions")
                title_options = json.loads(raw) if raw else []
                if title_options:
                    logger.info(
                        "SSE 回补标题方案, taskId=%s, count=%s",
                        task_id,
                        len(title_options),
                    )
                    self._send_sse_message(
                        task_id,
                        SseMessageTypeEnum.TITLES_GENERATED,
                        {"titleOptions": title_options},
                    )
                return

            if phase == ArticlePhaseEnum.OUTLINE_GENERATING.value:
                logger.info("SSE 回补：阶段2进行中, taskId=%s", task_id)
                self._send_sse_message(
                    task_id,
                    SseMessageTypeEnum.PHASE2_STARTED,
                    {"taskId": task_id},
                )
                return

            if phase == ArticlePhaseEnum.OUTLINE_EDITING.value:
                raw = article.get("outline")
                outline = json.loads(raw) if raw else []
                if outline:
                    logger.info("SSE 回补大纲, taskId=%s", task_id)
                    self._send_sse_message(
                        task_id,
                        SseMessageTypeEnum.OUTLINE_GENERATED,
                        {"outline": outline},
                    )
                return

            if phase == ArticlePhaseEnum.CONTENT_GENERATING.value:
                logger.info("SSE 回补：阶段3进行中, taskId=%s", task_id)
                content = article.get("content")
                full = article.get("fullContent")
                if full:
                    self._send_sse_message(
                        task_id,
                        SseMessageTypeEnum.MERGE_COMPLETE,
                        {"fullContent": full},
                    )
                elif content:
                    self._send_sse_message(
                        task_id,
                        SseMessageTypeEnum.AGENT3_COMPLETE,
                        {},
                    )
                return

            if status == ArticleStatusEnum.COMPLETED.value:
                self._send_sse_message(
                    task_id,
                    SseMessageTypeEnum.ALL_COMPLETE,
                    {"taskId": task_id},
                )
                sse_emitter_manager.complete(task_id)
        except Exception as e:
            logger.warning("SSE 状态回补失败, taskId=%s, error=%s", task_id, e)

    async def execute_phase1(
        self,
        task_id: str,
        topic: str,
        style: Optional[str] = None,
    ):
        """阶段1：异步生成标题方案"""
        logger.info("阶段1异步任务开始, taskId=%s, topic=%s, style=%s", task_id, topic, style)
        article_agent_service = ArticleAgentService()
        article_service = ArticleService(database)

        try:
            await article_service.update_article_status(task_id, ArticleStatusEnum.PROCESSING)
            await article_service.update_phase(task_id, ArticlePhaseEnum.TITLE_GENERATING)

            state = ArticleState()
            state.task_id = task_id
            state.topic = topic
            state.style = style

            await article_agent_service.execute_phase1_generate_titles(
                state,
                lambda message: self._handle_agent_message(task_id, message, state)
            )

            await article_service.save_title_options(task_id, state.title_options or [])
            await article_service.update_phase(task_id, ArticlePhaseEnum.TITLE_SELECTING)

            self._send_sse_message(
                task_id,
                SseMessageTypeEnum.TITLES_GENERATED,
                {
                    "titleOptions": [
                        item.model_dump(by_alias=True) for item in (state.title_options or [])
                    ]
                },
            )

            logger.info("阶段1异步任务完成, taskId=%s", task_id)
        except Exception as e:
            logger.error("阶段1异步任务失败, taskId=%s, error=%s", task_id, e)
            await article_service.update_article_status(
                task_id,
                ArticleStatusEnum.FAILED,
                str(e)
            )
            self._send_sse_message(
                task_id,
                SseMessageTypeEnum.ERROR,
                {"message": str(e)}
            )
            sse_emitter_manager.complete(task_id)

    async def execute_phase2(self, task_id: str):
        """阶段2：异步生成大纲"""
        logger.info("阶段2异步任务开始, taskId=%s", task_id)
        article_agent_service = ArticleAgentService()
        article_service = ArticleService(database)

        try:
            self._send_sse_message(
                task_id,
                SseMessageTypeEnum.PHASE2_STARTED,
                {"taskId": task_id},
            )
            article = await article_service.get_by_task_id(task_id)
            if not article:
                raise RuntimeError("文章不存在")

            state = ArticleState()
            state.task_id = task_id
            state.style = article["style"]
            state.user_description = article["userDescription"]
            state.title = TitleResult(
                mainTitle=article["mainTitle"],
                subTitle=article["subTitle"],
            )

            await article_agent_service.execute_phase2_generate_outline(
                state,
                lambda message: self._handle_agent_message(task_id, message, state)
            )
            await article_service.save_outline(task_id, state.outline.sections if state.outline else [])
            await article_service.update_phase(task_id, ArticlePhaseEnum.OUTLINE_EDITING)

            self._send_sse_message(
                task_id,
                SseMessageTypeEnum.OUTLINE_GENERATED,
                {
                    "outline": [
                        item.model_dump() for item in (state.outline.sections if state.outline else [])
                    ]
                },
            )
            logger.info("阶段2异步任务完成, taskId=%s", task_id)
        except Exception as e:
            logger.error("阶段2异步任务失败, taskId=%s, error=%s", task_id, e)
            await article_service.update_article_status(task_id, ArticleStatusEnum.FAILED, str(e))
            self._send_sse_message(task_id, SseMessageTypeEnum.ERROR, {"message": str(e)})
            sse_emitter_manager.complete(task_id)

    async def execute_phase3(self, task_id: str):
        """阶段3：异步生成正文与配图"""
        print(f"[文章创作] 阶段3开始（正文+配图+合并）taskId={task_id}", flush=True)
        logger.warning("阶段3异步任务开始, taskId=%s（通义万相配图会排队，可能需数分钟）", task_id)
        article_agent_service = ArticleAgentService()
        article_service = ArticleService(database)

        try:
            await article_service.update_article_status(task_id, ArticleStatusEnum.PROCESSING)
            self._send_sse_message(
                task_id,
                SseMessageTypeEnum.PHASE3_STARTED,
                {"taskId": task_id},
            )

            article = await article_service.get_by_task_id(task_id)
            if not article:
                raise RuntimeError("文章不存在")

            outline_data = json.loads(article["outline"]) if article["outline"] else []
            state = ArticleState()
            state.task_id = task_id
            state.style = article["style"]
            state.enabled_image_methods = (
                json.loads(article["enabledImageMethods"])
                if article["enabledImageMethods"]
                else None
            )
            state.title = TitleResult(
                mainTitle=article["mainTitle"],
                subTitle=article["subTitle"],
            )
            state.outline = OutlineResult(
                sections=[OutlineSection(**item) for item in outline_data]
            )

            await article_agent_service.execute_phase3_generate_content(
                state,
                lambda message: self._handle_agent_message(task_id, message, state)
            )
            await article_service.save_article_content(task_id, state)
            await article_service.update_article_status(task_id, ArticleStatusEnum.COMPLETED)

            self._send_sse_message(
                task_id,
                SseMessageTypeEnum.ALL_COMPLETE,
                {"taskId": task_id}
            )
            sse_emitter_manager.complete(task_id)
            logger.info("阶段3异步任务完成, taskId=%s", task_id)
            print(f"[文章创作] 阶段3完成 taskId={task_id}", flush=True)
        except Exception as e:
            logger.error("阶段3异步任务失败, taskId=%s, error=%s", task_id, e, exc_info=True)
            print(f"[文章创作] 阶段3失败 taskId={task_id} err={e!r}", flush=True)
            await article_service.update_article_status(task_id, ArticleStatusEnum.FAILED, str(e))
            self._send_sse_message(task_id, SseMessageTypeEnum.ERROR, {"message": str(e)})
            sse_emitter_manager.complete(task_id)

    def _handle_agent_message(self, task_id: str, message: str, state: ArticleState):
        """处理智能体消息并推送"""
        data = self._build_message_data(message, state)
        if data is not None:
            sse_emitter_manager.send(task_id, json.dumps(data, ensure_ascii=False))
    
    def _build_message_data(self, message: str, state: ArticleState) -> Dict[str, Any]:
        """构建消息数据"""
        # 处理流式消息（带冒号分隔符）
        streaming_prefix2 = SseMessageTypeEnum.AGENT2_STREAMING.get_streaming_prefix()
        streaming_prefix3 = SseMessageTypeEnum.AGENT3_STREAMING.get_streaming_prefix()
        image_complete_prefix = SseMessageTypeEnum.IMAGE_COMPLETE.get_streaming_prefix()
        
        if message.startswith(streaming_prefix2):
            return self._build_streaming_data(
                SseMessageTypeEnum.AGENT2_STREAMING,
                message[len(streaming_prefix2):]
            )
        
        if message.startswith(streaming_prefix3):
            return self._build_streaming_data(
                SseMessageTypeEnum.AGENT3_STREAMING,
                message[len(streaming_prefix3):]
            )
        
        if message.startswith(image_complete_prefix):
            image_json = message[len(image_complete_prefix):]
            return self._build_image_complete_data(image_json)
        
        # 处理完成消息（枚举值）
        return self._build_complete_message_data(message, state)
    
    def _build_streaming_data(self, type_enum: SseMessageTypeEnum, content: str) -> Dict[str, Any]:
        """构建流式输出数据"""
        return {
            "type": type_enum.value,
            "content": content
        }
    
    def _build_image_complete_data(self, image_json: str) -> Dict[str, Any]:
        """构建图片完成数据"""
        return {
            "type": SseMessageTypeEnum.IMAGE_COMPLETE.value,
            "image": json.loads(image_json)
        }
    
    def _build_complete_message_data(self, message: str, state: ArticleState) -> Dict[str, Any]:
        """构建完成消息数据"""
        data = {}
        
        if message == SseMessageTypeEnum.AGENT1_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.AGENT1_COMPLETE.value
            data["titleOptions"] = [
                item.model_dump(by_alias=True) for item in (state.title_options or [])
            ]
        elif message == SseMessageTypeEnum.AGENT2_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.AGENT2_COMPLETE.value
            data["outline"] = [s.model_dump() for s in state.outline.sections] if state.outline else []
        elif message == SseMessageTypeEnum.AGENT3_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.AGENT3_COMPLETE.value
        elif message == SseMessageTypeEnum.AGENT_REVIEWER_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.AGENT_REVIEWER_COMPLETE.value
            data["reviewScore"] = state.review_score
            data["reviewPassed"] = state.review_passed
        elif message == SseMessageTypeEnum.AGENT4_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.AGENT4_COMPLETE.value
            data["imageRequirements"] = [
                req.model_dump(by_alias=True) for req in state.image_requirements
            ] if state.image_requirements else []
        elif message == SseMessageTypeEnum.AGENT5_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.AGENT5_COMPLETE.value
            data["images"] = [
                img.model_dump(by_alias=True) for img in state.images
            ] if state.images else []
        elif message == SseMessageTypeEnum.MERGE_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.MERGE_COMPLETE.value
            data["fullContent"] = state.full_content
        else:
            return None
        
        return data
    
    def _send_sse_message(
        self,
        task_id: str,
        type_enum: SseMessageTypeEnum,
        additional_data: Dict[str, Any]
    ):
        """发送 SSE 消息"""
        data = {"type": type_enum.value}
        data.update(additional_data)
        sse_emitter_manager.send(task_id, json.dumps(data, ensure_ascii=False))


# 全局单例
article_async_service = ArticleAsyncService()
