#!/bin/bash

# ChatGPT Team Manager 一键部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

check_command() {
    if ! command -v $1 &> /dev/null; then
        error "$1 未安装，请先安装 $1"
    fi
}

generate_secret() {
    openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1
}

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       🚀 ChatGPT Team Manager 一键部署脚本                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检查依赖
info "检查依赖..."
check_command docker

if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    error "docker compose 未安装"
fi
success "依赖检查通过"

# 选择数据库类型
echo ""
info "选择数据库类型:"
echo "  1) SQLite (默认，简单部署，适合小型使用)"
echo "  2) PostgreSQL (推荐生产环境，更稳定)"
echo ""
echo -n "请选择 [1/2] (默认 1): "
read -r DB_CHOICE </dev/tty || DB_CHOICE="1"
DB_CHOICE=${DB_CHOICE:-1}

# 生成环境变量
SECRET_KEY=$(generate_secret)
info "生成安全密钥..."

# 创建 .env 文件
if [ "$DB_CHOICE" = "2" ]; then
    PG_USER="teamadmin"
    PG_PASS=$(generate_secret | cut -c1-16)
    PG_DB="team_manager"
    
    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
POSTGRES_USER=$PG_USER
POSTGRES_PASSWORD=$PG_PASS
POSTGRES_DB=$PG_DB
EOF
    
    COMPOSE_FILE="docker-compose.postgres.yml"
    info "使用 PostgreSQL 数据库"
else
    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
EOF
    
    COMPOSE_FILE="docker-compose.yml"
    info "使用 SQLite 数据库"
fi

success ".env 文件已创建"

# 启动服务
echo ""
info "启动服务（首次构建可能需要几分钟）..."
$DOCKER_COMPOSE -f $COMPOSE_FILE up -d --build

# 等待服务启动
info "等待服务启动..."
sleep 10

# 检查服务状态
if $DOCKER_COMPOSE -f $COMPOSE_FILE ps | grep -q "Up\|running"; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🎉 部署成功！                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    success "用户端:     http://localhost:3456"
    success "管理后台:   http://localhost:3456/admin"
    success "API 文档:   http://localhost:4567/docs"
    echo ""
    info "首次访问会跳转到初始化页面，请设置管理员账号"
    echo ""
else
    error "服务启动失败，请检查日志: $DOCKER_COMPOSE -f $COMPOSE_FILE logs"
fi
