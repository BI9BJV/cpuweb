#!/bin/bash
# CPUWeb 服务管理脚本

SERVICE_NAME="cpuweb"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "CPUWeb 服务管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start      启动服务"
    echo "  stop       停止服务"
    echo "  restart    重启服务"
    echo "  status     查看服务状态"
    echo "  enable     启用开机自启"
    echo "  disable    禁用开机自启"
    echo "  logs       查看服务日志"
    echo "  help       显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 status"
    echo "  $0 restart"
}

# 检查服务状态
check_status() {
    sudo systemctl status $SERVICE_NAME.service --no-pager
}

# 查看日志
view_logs() {
    echo "查看最近50行日志:"
    sudo journalctl -u $SERVICE_NAME.service -n 50 --no-pager
}

# 主逻辑
case "$1" in
    start)
        echo -e "${GREEN}正在启动 $SERVICE_NAME 服务...${NC}"
        sudo systemctl start $SERVICE_NAME.service
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $SERVICE_NAME 服务启动成功${NC}"
            sleep 2
            check_status
        else
            echo -e "${RED}✗ $SERVICE_NAME 服务启动失败${NC}"
            exit 1
        fi
        ;;
    stop)
        echo -e "${YELLOW}正在停止 $SERVICE_NAME 服务...${NC}"
        sudo systemctl stop $SERVICE_NAME.service
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $SERVICE_NAME 服务已停止${NC}"
        else
            echo -e "${RED}✗ $SERVICE_NAME 服务停止失败${NC}"
            exit 1
        fi
        ;;
    restart)
        echo -e "${YELLOW}正在重启 $SERVICE_NAME 服务...${NC}"
        sudo systemctl restart $SERVICE_NAME.service
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $SERVICE_NAME 服务重启成功${NC}"
            sleep 2
            check_status
        else
            echo -e "${RED}✗ $SERVICE_NAME 服务重启失败${NC}"
            exit 1
        fi
        ;;
    status)
        check_status
        ;;
    enable)
        echo -e "${GREEN}正在启用 $SERVICE_NAME 服务开机自启...${NC}"
        sudo systemctl enable $SERVICE_NAME.service
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $SERVICE_NAME 服务已启用开机自启${NC}"
        else
            echo -e "${RED}✗ 启用开机自启失败${NC}"
            exit 1
        fi
        ;;
    disable)
        echo -e "${YELLOW}正在禁用 $SERVICE_NAME 服务开机自启...${NC}"
        sudo systemctl disable $SERVICE_NAME.service
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $SERVICE_NAME 服务已禁用开机自启${NC}"
        else
            echo -e "${RED}✗ 禁用开机自启失败${NC}"
            exit 1
        fi
        ;;
    logs)
        view_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}错误: 未知命令 '$1'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac