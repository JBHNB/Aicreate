"""内容审核智能体适配器"""

from app.schemas.article import ArticleState


class ReviewerAgent:
    """正文质量审核（阈值未达标时可重写）"""

    async def run(self, service, state: ArticleState):
        await service.agent_reviewer_review_content(state)
