#!/bin/bash

# ChatGPT Team Manager 一键部署脚本
# 使用方法: curl -fsSL https://raw.githubusercontent.com/1307929582/team-invite/main/install.sh | bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        error "$1 未安装，请先安装 $1"
    fi
}

# 生成随机密钥
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
check_command git

# 检查 docker compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    error "docker compose 未安装"
fi
success "依赖检查通过"

# 选择安装目录
DEFAULT_DIR="$HOME/chatgpt-team-manager"
read -p "安装目录 [$DEFAULT_DIR]: " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_DIR}

# 选择数据库类型
echo ""
info "选择数据库类型:"
echo "  1) SQLite (默认，简单部署，适合小型使用)"
echo "  2) PostgreSQL (推荐生产环境，更稳定)"
read -p "请选择 [1/2]: " DB_CHOICE
DB_CHOICE=${DB_CHOICE:-1}

# 克隆或更新代码
if [ -d "$INSTALL_DIR" ]; then
    warn "目录已存在，正在更新..."
    cd "$INSTALL_DIR"
    git pull
else
    info "克隆代码..."
    git clone https://github.com/1307929582/team-invite.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 生成环境变量
SECRET_KEY=$(generate_secret)
info "生成安全密钥..."

# 创建 .env 文件
if [ "$DB_CHOICE" = "2" ]; then
    # PostgreSQL
    read -p "PostgreSQL 用户名 [teamadmin]: " PG_USER
    PG_USER=${PG_USER:-teamadmin}
    
    read -p "PostgreSQL 密码 [自动生成]: " PG_PASS
    PG_PASS=${PG_PASS:-$(generate_secret | cut -c1-16)}
    
    read -p "PostgreSQL 数据库名 [team_manager]: " PG_DB
    PG_DB=${PG_DB:-team_manager}
    
    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
POSTGRES_USER=$PG_USER
POSTGRES_PASSWORD=$PG_PASS
POSTGRES_DB=$PG_DB
EOF
    
    COMPOSE_FILE="docker-compose.postgres.yml"
    info "使用 PostgreSQL 数据库"
else
    # SQLite
    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
EOF
    
    COMPOSE_FILE="docker-compose.yml"
    info "使用 SQLite 数据库"
fi

success ".env 文件已创建"

# 启动服务
echo ""
info "启动服务..."
$DOCKER_COMPOSE -f $COMPOSE_FILE up -d --build

# 等待服务启动
info "等待服务启动..."
sleep 5

# 检查服务状态
if $DOCKER_COMPOSE -f $COMPOSE_FILE ps | grep -q "Up"; then
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
    info "常用命令:"
    echo "  查看日志:   $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f"
    echo "  停止服务:   $DOCKER_COMPOSE -f $COMPOSE_FILE down"
    echo "  重启服务:   $DOCKER_COMPOSE -f $COMPOSE_FILE restart"
    echo ""
else
    error "服务启动失败，请检查日志: $DOCKER_COMPOSE -f $COMPOSE_FILE logs"
fi
