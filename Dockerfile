FROM python:3.11-slim

WORKDIR /app

ARG APT_MIRROR_URL=""
ARG PIP_INDEX_URL=""

# 默认使用官方源；国内构建可通过 --build-arg 覆盖：
# docker build --build-arg APT_MIRROR_URL=https://mirrors.aliyun.com --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN if [ -n "$APT_MIRROR_URL" ]; then \
        sed -i "s|deb.debian.org|$APT_MIRROR_URL|g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
        sed -i "s|deb.debian.org|$APT_MIRROR_URL|g" /etc/apt/sources.list 2>/dev/null || true; \
    fi
RUN if [ -n "$PIP_INDEX_URL" ]; then \
        pip config set global.index-url "$PIP_INDEX_URL"; \
    fi

# 系统依赖 (PostgreSQL 客户端库给 psycopg2 用)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 层缓存
COPY pyproject.toml .

# 安装 Python 依赖
RUN pip install --no-cache-dir \
    "fastapi>=0.104.0" \
    "uvicorn[standard]>=0.24.0" \
    "python-multipart>=0.0.6" \
    "pydantic>=2.5.0" \
    "pydantic-settings>=2.1.0" \
    "neo4j>=5.14.0" \
    "langchain>=0.1.0" \
    "langchain-ollama>=0.1.0" \
    "langchain-core>=0.1.0" \
    "scikit-learn>=1.3.0" \
    "numpy>=1.24.0" \
    "requests>=2.31.0" \
    "pandas>=2.1.0" \
    "openpyxl>=3.1.0" \
    "httpx>=0.25.0" \
    "python-jose[cryptography]>=3.3.0" \
    "passlib[bcrypt]>=1.7.4" \
    "bcrypt>=4.0.0,<4.1.0" \
    "chromadb>=0.4.22" \
    "pymupdf>=1.23.0" \
    "python-docx>=1.1.0" \
    "beautifulsoup4>=4.12.0" \
    "lxml>=4.9.0" \
    "langchain-text-splitters>=0.0.1" \
    "psycopg2-binary>=2.9.9" \
    "pymysql>=1.1.0"

# 复制项目代码
COPY . .

# 以可编辑模式安装项目（使模块可导入）
RUN pip install --no-cache-dir -e .

EXPOSE 8000 8501
