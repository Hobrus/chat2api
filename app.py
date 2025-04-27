import warnings

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from utils.configs import enable_gateway, api_prefix

warnings.filterwarnings("ignore")

log_config = uvicorn.config.LOGGING_CONFIG
default_format = "%(asctime)s | %(levelname)s | %(message)s"
access_format = r'%(asctime)s | %(levelname)s | %(client_addr)s: %(request_line)s %(status_code)s'
log_config["formatters"]["default"]["fmt"] = default_format
log_config["formatters"]["access"]["fmt"] = access_format

app = FastAPI(
    docs_url=f"/{api_prefix}/docs",  # 设置 Swagger UI 文档路径
    redoc_url=f"/{api_prefix}/redoc",  # 设置 Redoc 文档路径
    openapi_url=f"/{api_prefix}/openapi.json"  # 设置 OpenAPI JSON 路径
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
security_scheme = HTTPBearer()

# Добавляем middleware перед импортом модулей
if not enable_gateway:
    # Используем middleware вместо catch-all маршрута
    @app.middleware("http")
    async def gateway_disabled_middleware(request: Request, call_next):
        path = request.url.path.lstrip('/')

        # Определяем разрешенные пути
        allowed_paths = [
            "api/v0/chat/completions",
            "v1/chat/completions",
            "v1/models",
            "api/v0/models",  # Добавлено
            "tokens",
            "tokens/upload",
            "tokens/clear",
            "tokens/error",
            "seed_tokens/clear"
        ]

        if api_prefix:
            allowed_paths += [f"{api_prefix}/{p}" for p in allowed_paths]

        # Проверяем, соответствует ли путь запроса разрешенным
        for allowed_path in allowed_paths:
            if path == allowed_path:
                return await call_next(request)

        # Проверяем пути с динамическими параметрами
        if (path.startswith("tokens/add/") or
                (api_prefix and path.startswith(f"{api_prefix}/tokens/add/"))):
            return await call_next(request)

        # Все остальные пути возвращают ошибку
        return JSONResponse(
            status_code=404,
            content={"detail": "Gateway is disabled"}
        )

# Теперь импортируем модули
from app import app

import api.chat2api

if enable_gateway:
    import gateway.share
    import gateway.login
    import gateway.chatgpt
    import gateway.gpts
    import gateway.admin
    import gateway.v1
    import gateway.backend

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5005)
    # uvicorn.run("app:app", host="0.0.0.0", port=5005, ssl_keyfile="key.pem", ssl_certfile="cert.pem")