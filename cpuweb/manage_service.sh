#!/bin/bash
# CPUWeb服务管理脚本

# 服务配置
SERVICE_NAME="cpuweb"
SERVICE_USER="bi9bjv"
PYTHON_ENV="/home/bi9bjv/miniconda3/envs/cpuweb/bin/python"
APP_PATH="/home/bi9bjv/python/cpuweb/app.py"
LOG_FILE="/home/bi9bjv/python/cpuweb/service.log"
PID_FILE="/home/bi9bjv/python/cpuweb/service.pid"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查服务是否运行
is_running() {
    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            return 0
        else
            # PID文件存在但进程不存在，清理PID文件
            rm -f $PID_FILE
            return 1
        fi
    else
        return 1
    fi
}

# 启动服务
start_service() {
    echo "正在启动 $SERVICE_NAME 服务..."
    
    if is_running; then
        echo -e "${YELLOW}⚠ $SERVICE_NAME 服务已在运行中${NC}"
        exit 1
    fi
    
    # 激活conda环境并启动服务
    su - $SERVICE_USER -c "
        source /home/bi9bjv/miniconda3/etc/profile.d/conda.sh
        conda activate cpuweb
        nohup $PYTHON_ENV $APP_PATH > $LOG_FILE 2>&1 &
        echo \$! > $PID_FILE
    "
    
    sleep 2
    
    if is_running; then
        echo -e "${GREEN}✓ $SERVICE_NAME 服务启动成功${NC}"
        echo "服务PID: $(cat $PID_FILE)"
        echo "访问地址: http://localhost:9001"
    else
        echo -e "${RED}✗ $SERVICE_NAME 服务启动失败${NC}"
        cat $LOG_FILE
        exit 1
    fi
}

# 停止服务
stop_service() {
    echo "正在停止 $SERVICE_NAME 服务..."
    
    if ! is_running; then
        echo -e "${YELLOW}⚠ $SERVICE_NAME 服务未运行${NC}"
        exit 0
    fi
    
    PID=$(cat $PID_FILE)
    kill $PID
    
    # 等待进程结束
    for i in {1..30}; do
        if ps -p $PID > /dev/null 2>&1; then
            sleep 1
        else
            break
        fi
    done
    
    # 如果进程仍未结束，强制终止
    if ps -p $PID > /dev/null 2>&1; then
        kill -9 $PID
    fi
    
    rm -f $PID_FILE
    echo -e "${GREEN}✓ $SERVICE_NAME 服务已停止${NC}"
}

# 重启服务
restart_service() {
    if is_running; then
        stop_service
        sleep 2
    fi
    start_service
}

# 查看服务状态
status_service() {
    if is_running; then
        PID=$(cat $PID_FILE)
        echo -e "${GREEN}✓ $SERVICE_NAME 服务正在运行${NC}"
        echo "PID: $PID"
        # 显示服务监听端口
        if command -v netstat >/dev/null 2>&1; then
            netstat -tlnp 2>/dev/null | grep -q ":9001 " && echo "端口: 9001 (已监听)"
        fi
    else
        echo -e "${RED}✗ $SERVICE_NAME 服务未运行${NC}"
    fi
}

# 查看服务日志
logs_service() {
    if [ -f $LOG_FILE ]; then
        echo "服务日志 ($LOG_FILE):"
        tail -n 50 $LOG_FILE
    else
        echo "日志文件不存在: $LOG_FILE"
    fi
}

# 启用开机自启
enable_service() {
    echo "设置 $SERVICE_NAME 开机自启..."
    
    # 创建systemd服务文件
    sudo tee /etc/systemd/system/cpuweb.service > /dev/null <<EOF
[Unit]
Description=CPUWeb System Monitor Service
After=network.target

[Service]
Type=forking
User=bi9bjv
Group=bi9bjv
WorkingDirectory=/home/bi9bjv/python/cpuweb
ExecStart=/bin/bash -c 'source /home/bi9bjv/miniconda3/etc/profile.d/conda.sh && conda activate cpuweb && /home/bi9bjv/miniconda3/envs/cpuweb/bin/python /home/bi9bjv/python/cpuweb/app.py'
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable cpuweb
    echo -e "${GREEN}✓ $SERVICE_NAME 开机自启已设置${NC}"
}

# 禁用开机自启
disable_service() {
    echo "禁用 $SERVICE_NAME 开机自启..."
    sudo systemctl disable cpuweb
    sudo rm -f /etc/systemd/system/cpuweb.service
    sudo systemctl daemon-reload
    echo -e "${GREEN}✓ $SERVICE_NAME 开机自启已禁用${NC}"
}

# 显示帮助
show_help() {
    echo "CPUWeb 服务管理脚本"
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start     - 启动服务"
    echo "  stop      - 停止服务"
    echo "  restart   - 重启服务"
    echo "  status    - 查看服务状态"
    echo "  logs      - 查看服务日志"
    echo "  enable    - 设置开机自启"
    echo "  disable   - 禁用开机自启"
    echo "  help      - 显示此帮助"
}

# 主逻辑
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        logs_service
        ;;
    enable)
        enable_service
        ;;
    disable)
        disable_service
        ;;
    help|*)
        show_help
        ;;
esac