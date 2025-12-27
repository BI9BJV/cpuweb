#!/bin/bash
# 树莓派温度控制风扇项目安装脚本

echo "树莓派温度控制风扇项目安装脚本"
echo "================================"

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
  echo "请以root权限运行此安装脚本"
  echo "使用: sudo ./install.sh"
  exit 1
fi

echo "1. 检查并安装依赖..."
if ! python3 -c "import RPi.GPIO" &> /dev/null; then
    echo "正在安装RPi.GPIO库..."
    apt update && apt install -y python3-rpi.gpio
else
    echo "RPi.GPIO库已安装"
fi

echo ""
echo "2. 验证温度传感器..."
if [ -f "/sys/class/thermal/thermal_zone0/temp" ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    TEMP_C=$(echo "$TEMP / 1000" | bc -l)
    echo "温度传感器正常，当前温度: $TEMP_C°C"
else
    echo "警告: 无法访问温度传感器"
    exit 1
fi

echo ""
echo "3. 设置开机自启动..."
# 复制服务文件
cp /home/bi9bjv/python/温度管控/fan_control.service /etc/systemd/system/

# 重新加载systemd配置
systemctl daemon-reload

# 启用服务
systemctl enable fan_control

echo ""
echo "4. 启动服务..."
systemctl start fan_control

echo ""
echo "5. 检查服务状态..."
systemctl status fan_control --no-pager -l

echo ""
echo "安装完成！"
echo "服务已设置为开机自启"
echo ""
echo "常用命令："
echo "  查看服务状态: sudo systemctl status fan_control"
echo "  停止服务: sudo systemctl stop fan_control"
echo "  重启服务: sudo systemctl restart fan_control"
echo "  查看日志: sudo journalctl -u fan_control -f"