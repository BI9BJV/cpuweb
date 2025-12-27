#!/bin/bash
# 系统监控Web应用启动脚本

echo "正在启动系统监控Web应用..."

# 激活conda环境
source /home/bi9bjv/miniconda3/etc/profile.d/conda.sh
conda activate cpuweb

# 切换到项目目录
cd /home/bi9bjv/python/cpuweb

# 启动应用
echo "启动系统监控服务，访问地址: http://$(hostname -I | awk '{print $1}'):9001"
echo "本地访问地址: http://localhost:9001"
echo "按 Ctrl+C 停止服务"

python app.py