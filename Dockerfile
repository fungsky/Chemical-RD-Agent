FROM docker.m.daocloud.io/library/python:3.11-slim

WORKDIR /app

# 配置 Debian 国内镜像源（阿里云）
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# 配置 pip 国内镜像源（清华）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

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
