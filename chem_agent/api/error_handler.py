"""统一错误处理模块 - 错误码定义、异常类和全局处理器。"""

import logging
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ============ 错误码常量 ============

class ErrorCode:
    """错误码定义。E1xxx 数据库, E2xxx LLM/AI, E3xxx 权限, E4xxx 输入, E5xxx 系统。"""
    # 数据库
    DB_CONNECTION = "E1001"
    DB_QUERY_FAILED = "E1002"
    DB_NOT_FOUND = "E1003"
    DB_DUPLICATE = "E1004"

    # LLM / AI
    LLM_UNAVAILABLE = "E2001"
    LLM_TIMEOUT = "E2002"
    LLM_PARSE_ERROR = "E2003"
    AGENT_FAILED = "E2004"

    # 权限
    AUTH_INVALID = "E3001"
    AUTH_EXPIRED = "E3002"
    PERMISSION_DENIED = "E3003"

    # 输入
    INPUT_INVALID = "E4001"
    FILE_TOO_LARGE = "E4002"
    FILE_FORMAT = "E4003"
    MISSING_PARAM = "E4004"

    # 系统
    INTERNAL = "E5000"
    SERVICE_UNAVAILABLE = "E5001"
    NOT_INITIALIZED = "E5002"


# ============ 错误码 -> 用户友好消息映射 ============

_USER_MESSAGES = {
    ErrorCode.DB_CONNECTION: "数据库连接异常，请联系管理员",
    ErrorCode.DB_QUERY_FAILED: "数据查询失败，请稍后重试",
    ErrorCode.DB_NOT_FOUND: "未找到请求的数据",
    ErrorCode.DB_DUPLICATE: "数据已存在",
    ErrorCode.LLM_UNAVAILABLE: "AI 服务暂时不可用，请检查 Ollama 是否运行",
    ErrorCode.LLM_TIMEOUT: "AI 响应超时，请简化问题后重试",
    ErrorCode.LLM_PARSE_ERROR: "AI 响应解析失败，请重试",
    ErrorCode.AGENT_FAILED: "智能体执行异常，请重试",
    ErrorCode.AUTH_INVALID: "认证信息无效，请重新登录",
    ErrorCode.AUTH_EXPIRED: "会话已过期，请重新登录",
    ErrorCode.PERMISSION_DENIED: "您没有此操作的权限",
    ErrorCode.INPUT_INVALID: "输入参数不合法",
    ErrorCode.FILE_TOO_LARGE: "文件大小超过限制",
    ErrorCode.FILE_FORMAT: "不支持的文件格式",
    ErrorCode.MISSING_PARAM: "缺少必填参数",
    ErrorCode.INTERNAL: "服务内部错误，请稍后重试",
    ErrorCode.SERVICE_UNAVAILABLE: "服务暂时不可用",
    ErrorCode.NOT_INITIALIZED: "服务尚未初始化，请稍后重试",
}


# ============ 自定义异常 ============

class ChemAgentError(Exception):
    """ChemAgent 业务异常基类。"""

    def __init__(
        self,
        error_code: str = ErrorCode.INTERNAL,
        user_message: Optional[str] = None,
        internal_detail: Optional[str] = None,
        status_code: int = 500,
    ):
        self.error_code = error_code
        self.user_message = user_message or _USER_MESSAGES.get(error_code, "服务异常")
        self.internal_detail = internal_detail
        self.status_code = status_code
        super().__init__(self.user_message)


# ============ 全局异常处理器 ============

async def chemagent_error_handler(_request: Request, exc: ChemAgentError) -> JSONResponse:
    """处理 ChemAgentError 业务异常。"""
    logger.error(
        "[%s] %s | internal: %s",
        exc.error_code, exc.user_message, exc.internal_detail or "-",
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.user_message,
        },
    )


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    """处理 FastAPI HTTPException，统一响应格式。"""
    # 对于 4xx 错误，detail 可以直接返回（通常是业务提示）
    # 对于 5xx 错误，脱敏处理
    if exc.status_code >= 500:
        logger.error("HTTPException %d: %s", exc.status_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": ErrorCode.INTERNAL,
                "message": "服务内部错误，请稍后重试",
            },
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": f"E{exc.status_code}",
            "message": str(exc.detail),
        },
    )


async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """兜底：捕获所有未处理的异常，不泄露内部信息。"""
    logger.error("未处理异常: %s: %s", type(exc).__name__, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": ErrorCode.INTERNAL,
            "message": "服务内部错误，请稍后重试",
        },
    )


def register_error_handlers(app):
    """注册所有异常处理器到 FastAPI 应用。"""
    app.add_exception_handler(ChemAgentError, chemagent_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
