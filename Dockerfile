FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.10.9 /uv /uvx /bin/

# Ref: https://docs.astral.sh/uv/guides/integration/docker
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

EXPOSE 8000

CMD ["uv", "run", "main.py"]