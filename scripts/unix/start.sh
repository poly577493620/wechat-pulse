#!/usr/bin/env sh
set -eu
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
project_root="$(CDPATH= cd -- "$script_dir/../.." && pwd)"
cd "$project_root"

if ! command -v docker >/dev/null 2>&1; then
  echo "未找到 Docker，请先安装并启动 Docker Desktop 或 Docker Engine。" >&2
  exit 1
fi
docker compose version >/dev/null

if [ ! -f .env ]; then
  cp .env.example .env
  if command -v openssl >/dev/null 2>&1; then
    token="$(openssl rand -hex 32)"
  else
    token="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
  fi
  sed "s/ADMIN_TOKEN=change-me/ADMIN_TOKEN=$token/" .env > .env.tmp
  mv .env.tmp .env
  chmod 600 .env
  echo "已创建 .env 并生成随机管理令牌。"
else
  echo "检测到现有 .env，将保留已有配置。"
fi

docker compose up -d --build
echo "WePulse 已启动：http://localhost:8765/admin"
echo "管理令牌保存在 .env 的 ADMIN_TOKEN 中。"
