#!/bin/bash
# 树莓派温度控制风扇启动脚本

echo "正在启动树莓派温度控制风扇系统..."

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
  echo "警告: 建议以root权限运行此脚本以确保GPIO正常工作"
  echo "使用: sudo ./start.sh"
fi

# 检查是否已安装RPi.GPIO
python3 -c "import RPi.GPIO" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "正在安装RPi.GPIO库..."
  pip3 install RPi.GPIO
fi

echo "启动温度控制风扇系统"
python3 /home/bi9bjv/python/温度管控/fan_control.py

echo "系统已停止"