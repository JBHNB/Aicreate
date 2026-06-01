"""SSE Emitter 管理器"""

import logging
import asyncio
from collections import defaultdict
from typing import Dict, List
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

_KEEPALIVE_INTERVAL = 15.0
_MAX_PENDING_PER_TASK = 64


class SseEmitterManager:
    """SSE Emitter 管理器"""
    
    def __init__(self):
        # 存储所有的队列
        self._queues: Dict[str, asyncio.Queue] = {}
        # 客户端尚未连接时暂存的消息（避免 phase1 早于 SSE 导致永远卡住）
        self._pending: Dict[str, List[str]] = defaultdict(list)
    
    def _flush_pending(self, task_id: str, queue: asyncio.Queue) -> None:
        pending = self._pending.pop(task_id, [])
        if pending:
            logger.info("SSE 回放缓冲消息, taskId=%s, count=%s", task_id, len(pending))
        for msg in pending:
            queue.put_nowait(msg)

    def create_emitter(self, task_id: str) -> StreamingResponse:
        """
        创建 SSE Emitter
        
        Args:
            task_id: 任务ID
            
        Returns:
            StreamingResponse
        """
        # 创建队列
        queue = asyncio.Queue()
        self._queues[task_id] = queue
        self._flush_pending(task_id, queue)
        
        logger.info("SSE 连接已创建, taskId=%s", task_id)
        
        # 创建事件流生成器
        async def event_generator():
            try:
                while True:
                    try:
                        message = await asyncio.wait_for(
                            queue.get(), timeout=_KEEPALIVE_INTERVAL
                        )
                    except asyncio.TimeoutError:
                        yield ": keepalive\n\n"
                        continue
                    
                    # 如果是完成信号，结束流
                    if message == "__COMPLETE__":
                        break
                    
                    # 格式化为 SSE 格式
                    yield f"data: {message}\n\n"
            except asyncio.CancelledError:
                logger.info(f"SSE 连接被取消, taskId={task_id}")
            except Exception as e:
                logger.error(f"SSE 连接错误, taskId={task_id}, error={e}")
            finally:
                # 清理队列
                if task_id in self._queues:
                    del self._queues[task_id]
                logger.info(f"SSE 连接已关闭, taskId={task_id}")
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    def send(self, task_id: str, message: str):
        """
        发送消息
        
        Args:
            task_id: 任务ID
            message: 消息内容
        """
        queue = self._queues.get(task_id)
        if queue is None:
            buf = self._pending[task_id]
            if len(buf) >= _MAX_PENDING_PER_TASK:
                buf.pop(0)
            buf.append(message)
            logger.info(
                "SSE 尚未连接，消息已缓冲, taskId=%s, pending=%s",
                task_id,
                len(buf),
            )
            return
        
        try:
            queue.put_nowait(message)
            logger.debug("SSE 消息发送成功, taskId=%s", task_id)
        except Exception as e:
            logger.error(f"SSE 消息发送失败, taskId={task_id}, error={e}")
    
    def complete(self, task_id: str):
        """
        完成连接
        
        Args:
            task_id: 任务ID
        """
        queue = self._queues.get(task_id)
        if queue is None:
            buf = self._pending[task_id]
            if len(buf) >= _MAX_PENDING_PER_TASK:
                buf.pop(0)
            buf.append("__COMPLETE__")
            logger.info("SSE 尚未连接，完成信号已缓冲, taskId=%s", task_id)
            return
        
        try:
            queue.put_nowait("__COMPLETE__")
            logger.info(f"SSE 连接已完成, taskId={task_id}")
        except Exception as e:
            logger.error(f"SSE 连接完成失败, taskId={task_id}, error={e}")
    
    def exists(self, task_id: str) -> bool:
        """
        检查 Emitter 是否存在
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否存在
        """
        return task_id in self._queues


# 全局单例
sse_emitter_manager = SseEmitterManager()
