#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控Web应用 - 优化版
"""
import os
import time
import json
import threading
import subprocess
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
import psutil
from file_manager import file_manager

app = Flask(__name__)

# 全局变量存储系统信息
system_info = {
    'cpu': {'percent': 0, 'temp': 0, 'freq': 0, 'count': 0, 'voltage': 0, 'model': ''},
    'power': {'watts': 0},
    'memory': {'total': 0, 'used': 0, 'free': 0, 'percent': 0},
    'disk': {'total': 0, 'used': 0, 'free': 0, 'percent': 0},
    'network': {'bytes_sent': 0, 'bytes_recv': 0, 'upload_speed': 0, 'download_speed': 0},
    'io': {'read_bytes': 0, 'write_bytes': 0, 'read_speed': 0, 'write_speed': 0},
    'uptime': 0,
    'timestamp': '',
    'system': {'system': '', 'release': '', 'version': '', 'machine': ''}
}

# 上一次的网络和IO统计
last_network_stats = None
last_io_stats = None
last_update_time = time.time()

# 缓存不常变化的数据
cached_data = {
    'cpu_model': None,
    'cpu_count': None,
    'disk_total': None,
    'memory_total': None,
    'system_info': None,
    'last_cache_time': 0
}

# 缓存有效期（秒）
CACHE_TTL = 60

def get_cpu_temperature():
    """获取CPU温度"""
    try:
        # 尝试从不同路径读取CPU温度
        temp_paths = [
            '/sys/class/thermal/thermal_zone0/temp',
            '/sys/class/thermal/thermal_zone1/temp',
            '/sys/devices/virtual/thermal/thermal_zone0/temp'
        ]
        
        for path in temp_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    temp = float(f.read()) / 1000.0
                    if 0 < temp < 150:  # 合理的温度范围
                        return round(temp, 1)
        
        # 如果无法读取，返回0
        return 0
    except:
        return 0

def get_cpu_voltage():
    """获取CPU电压"""
    try:
        # 使用 vcgencmd 获取树莓派CPU电压
        result = subprocess.run(['vcgencmd', 'measure_volts'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # 输出格式: volt=0.9260V
            output = result.stdout.strip()
            if 'volt=' in output:
                voltage_str = output.replace('volt=', '').replace('V', '')
                voltage = float(voltage_str)
                return round(voltage, 3)
        
        return 0
    except:
        return 0

def get_power_consumption():
    """获取系统功耗"""
    try:
        # 尝试从不同路径读取功耗信息
        power_paths = [
            '/sys/class/power_supply/battery/current_now',
            '/sys/class/power_supply/battery/voltage_now',
            '/sys/class/hwmon/hwmon0/power1_input'
        ]
        
        for path in power_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    value = float(f.read().strip())
                    if 'current' in path:
                        # 电流值，单位uA
                        current_ma = value / 1000.0
                        return round(current_ma, 2)
                    elif 'voltage' in path:
                        # 电压值，单位uV
                        voltage_mv = value / 1000.0
                        return round(voltage_mv, 2)
                    elif 'power' in path:
                        # 功耗值，单位uW
                        power_mw = value / 1000.0
                        return round(power_mw / 1000.0, 2)  # 转换为W
        
        # 如果无法直接读取，使用估算方法
        # 根据CPU使用率估算功耗（树莓派典型功耗：空闲2-3W，满载5-7W）
        cpu_percent = system_info['cpu']['percent']
        estimated_power = 2.5 + (cpu_percent / 100.0) * 4.5
        return round(estimated_power, 2)
    except:
        return 0

def get_cpu_model():
    """获取CPU型号"""
    try:
        # 尝试从 /proc/cpuinfo 读取
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                # 先尝试查找 model name 字段（x86 架构）
                for line in f:
                    if line.startswith('model name'):
                        return line.split(':', 1)[1].strip()
                
                # 如果没有 model name，尝试从 ARM 处理器信息中识别
                f.seek(0)
                cpu_part = None
                cpu_implementer = None
                
                for line in f:
                    if line.startswith('CPU part'):
                        cpu_part = line.split(':')[1].strip()
                    elif line.startswith('CPU implementer'):
                        cpu_implementer = line.split(':')[1].strip()
                
                # ARM 处理器型号映射
                if cpu_part and cpu_implementer:
                    # ARM 实现者 0x41 = ARM
                    if cpu_implementer == '0x41':
                        cpu_models = {
                            '0xd08': 'ARM Cortex-A76',
                            '0xd0b': 'ARM Cortex-A78',
                            '0xd07': 'ARM Cortex-A57',
                            '0xd03': 'ARM Cortex-A53',
                            '0xd0c': 'ARM Cortex-A65',
                            '0xd40': 'ARM Cortex-A78AE',
                            '0xd44': 'ARM Cortex-X1',
                            '0xd4c': 'ARM Cortex-A710',
                            '0xd47': 'ARM Cortex-A715',
                            '0xd4e': 'ARM Cortex-A720',
                            '0xd4f': 'ARM Cortex-X2',
                            '0xd05': 'ARM Cortex-A55',
                            '0xd02': 'ARM Cortex-A34',
                        }
                        return cpu_models.get(cpu_part, f'ARM CPU (Part: {cpu_part})')
                    
                    # ARM 实现者 0x51 = Qualcomm
                    elif cpu_implementer == '0x51':
                        cpu_models = {
                            '0x802': 'Snapdragon 8 Gen 1',
                            '0x804': 'Snapdragon 8 Gen 2',
                            '0x805': 'Snapdragon 8 Gen 3',
                        }
                        return cpu_models.get(cpu_part, f'Qualcomm CPU (Part: {cpu_part})')
                    
                    # ARM 实现者 0x42 = Broadcom (树莓派)
                    elif cpu_implementer == '0x42':
                        cpu_models = {
                            '0xd03': 'Broadcom BCM2835 (ARM Cortex-A53)',
                            '0xd07': 'Broadcom BCM2836 (ARM Cortex-A53)',
                            '0xd08': 'Broadcom BCM2711 (ARM Cortex-A72)',
                            '0xd0b': 'Broadcom BCM2712 (ARM Cortex-A76)',
                        }
                        return cpu_models.get(cpu_part, f'Broadcom CPU (Part: {cpu_part})')
                    
                    return f'ARM CPU (Implementer: {cpu_implementer}, Part: {cpu_part})'
                
        return 'Unknown'
    except:
        return 'Unknown'

def get_system_info():
    """获取系统版本信息"""
    try:
        import platform
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine()
        }
    except:
        return {
            'system': 'Unknown',
            'release': 'Unknown',
            'version': 'Unknown',
            'machine': 'Unknown'
        }



def update_system_info():
    """更新系统信息 - 优化版"""
    global last_network_stats, last_io_stats, last_update_time, cached_data
    
    current_time = time.time()
    time_delta = current_time - last_update_time
    
    # 检查是否需要更新缓存
    need_cache_update = (current_time - cached_data['last_cache_time']) > CACHE_TTL
    
    # 更新缓存数据（低频数据，60秒一次）
    if need_cache_update:
        cached_data['cpu_model'] = get_cpu_model()
        cached_data['cpu_count'] = psutil.cpu_count()
        
        disk = psutil.disk_usage('/')
        cached_data['disk_total'] = round(disk.total / (1024**3), 2)
        
        memory = psutil.virtual_memory()
        cached_data['memory_total'] = round(memory.total / (1024**3), 2)
        
        cached_data['system_info'] = get_system_info()
        cached_data['last_cache_time'] = current_time
    
    # 高频数据采集（每2秒一次）
    
    # CPU信息 - 使用非阻塞模式，减少采样开销
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_freq = psutil.cpu_freq()
    
    # 只在需要时获取温度和电压（减少subprocess调用）
    if current_time - cached_data['last_cache_time'] > 10:  # 每10秒更新一次温度和电压
        cpu_temp = get_cpu_temperature()
        cpu_voltage = get_cpu_voltage()
    else:
        cpu_temp = system_info['cpu'].get('temp', 0)
        cpu_voltage = system_info['cpu'].get('voltage', 0)
    
    system_info['cpu'] = {
        'percent': round(cpu_percent, 1),
        'temp': cpu_temp,
        'freq': round(cpu_freq.current if cpu_freq else 0, 1),
        'count': cached_data['cpu_count'] or 0,
        'model': cached_data['cpu_model'] or '',
        'voltage': cpu_voltage
    }
    
    # 功耗信息 - 基于CPU使用率估算，减少系统调用
    cpu_percent_value = system_info['cpu']['percent']
    estimated_power = 2.5 + (cpu_percent_value / 100.0) * 4.5
    system_info['power'] = {
        'watts': round(estimated_power, 2)
    }
    
    # 内存信息 - 从缓存获取总量
    memory = psutil.virtual_memory()
    system_info['memory'] = {
        'total': cached_data['memory_total'] or round(memory.total / (1024**3), 2),
        'used': round(memory.used / (1024**3), 2),
        'free': round(memory.available / (1024**3), 2),
        'percent': round(memory.percent, 1)
    }
    
    # 磁盘信息 - 从缓存获取总量
    disk = psutil.disk_usage('/')
    system_info['disk'] = {
        'total': cached_data['disk_total'] or round(disk.total / (1024**3), 2),
        'used': round(disk.used / (1024**3), 2),
        'free': round(disk.free / (1024**3), 2),
        'percent': round((disk.used / disk.total) * 100, 1)
    }
    
    # 网络信息
    current_network_stats = psutil.net_io_counters()
    if last_network_stats and time_delta > 0:
        bytes_sent_delta = current_network_stats.bytes_sent - last_network_stats.bytes_sent
        bytes_recv_delta = current_network_stats.bytes_recv - last_network_stats.bytes_recv
        
        upload_speed = round(bytes_sent_delta / time_delta / 1024, 2)  # KB/s
        download_speed = round(bytes_recv_delta / time_delta / 1024, 2)  # KB/s
    else:
        upload_speed = 0
        download_speed = 0
    
    last_network_stats = current_network_stats
    
    system_info['network'] = {
        'bytes_sent': round(current_network_stats.bytes_sent / (1024**2), 2),  # MB
        'bytes_recv': round(current_network_stats.bytes_recv / (1024**2), 2),  # MB
        'upload_speed': upload_speed,
        'download_speed': download_speed
    }
    
    # IO信息
    current_io_stats = psutil.disk_io_counters()
    if current_io_stats and last_io_stats and time_delta > 0:
        read_bytes_delta = current_io_stats.read_bytes - last_io_stats.read_bytes
        write_bytes_delta = current_io_stats.write_bytes - last_io_stats.write_bytes
        
        read_speed = round(read_bytes_delta / time_delta / 1024, 2)  # KB/s
        write_speed = round(write_bytes_delta / time_delta / 1024, 2)  # KB/s
    else:
        read_speed = 0
        write_speed = 0
    
    if current_io_stats:
        last_io_stats = current_io_stats
    
    system_info['io'] = {
        'read_bytes': round(current_io_stats.read_bytes / (1024**2), 2) if current_io_stats else 0,  # MB
        'write_bytes': round(current_io_stats.write_bytes / (1024**2), 2) if current_io_stats else 0,  # MB
        'read_speed': read_speed,
        'write_speed': write_speed
    }
    
    # 系统运行时间
    system_info['uptime'] = round(time.time() - psutil.boot_time(), 1)
    
    # 时间戳
    system_info['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 系统版本信息 - 从缓存获取
    system_info['system'] = cached_data['system_info'] or {
        'system': 'Unknown',
        'release': 'Unknown',
        'version': 'Unknown',
        'machine': 'Unknown'
    }
    
    last_update_time = current_time

def background_update():
    """后台更新系统信息"""
    while True:
        update_system_info()
        time.sleep(1)  # 每1秒更新一次

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统监控面板</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', 'Consolas', 'VT323', monospace;
            background: #000000;
            min-height: 100vh;
            padding: 10px;
            color: #00ffff;
            position: relative;
            overflow-x: hidden;
        }

        /* CRT屏幕效果 */
        body::before {
            content: " ";
            display: block;
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background: linear-gradient(
                rgba(18, 16, 16, 0) 50%,
                rgba(0, 0, 0, 0.25) 50%
            );
            background-size: 100% 4px;
            z-index: 2;
            pointer-events: none;
        }

        /* CRT荧光效果 */
        body::after {
            content: " ";
            display: block;
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background: rgba(18, 16, 16, 0.1);
            opacity: 0;
            z-index: 2;
            pointer-events: none;
            animation: flicker 0.15s infinite;
        }

        @keyframes flicker {
            0% { opacity: 0.027906; }
            5% { opacity: 0.048532; }
            10% { opacity: 0.032642; }
            15% { opacity: 0.022874; }
            20% { opacity: 0.035263; }
            25% { opacity: 0.038943; }
            30% { opacity: 0.042762; }
            35% { opacity: 0.029821; }
            40% { opacity: 0.047685; }
            45% { opacity: 0.036628; }
            50% { opacity: 0.044725; }
            55% { opacity: 0.041531; }
            60% { opacity: 0.049376; }
            65% { opacity: 0.039876; }
            70% { opacity: 0.045823; }
            75% { opacity: 0.041847; }
            80% { opacity: 0.048532; }
            85% { opacity: 0.032642; }
            90% { opacity: 0.022874; }
            95% { opacity: 0.035263; }
            100% { opacity: 0.038943; }
        }

        /* 屏幕轻微弯曲效果 */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }

        /* 文本发光效果 */
        .glow-text {
            text-shadow:
                0 0 5px #00ffff,
                0 0 10px #00ffff,
                0 0 20px #00ffff,
                0 0 40px #00ffff;
        }

        .header {
            margin-bottom: 20px;
            text-shadow: 0 0 10px #00ffff;
        }

        .header h1 {
            font-size: 1.5em;
            margin-bottom: 10px;
            color: #00ffff;
            text-transform: uppercase;
            text-shadow:
                0 0 5px #00ffff,
                0 0 10px #00ffff,
                0 0 20px #00ffff;
        }

        .header .time {
            font-size: 1em;
            color: #00ffff;
            text-shadow: 0 0 5px #00ffff;
        }

        .nav-menu {
            margin-top: 15px;
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        .nav-btn {
            display: inline-block;
            padding: 8px 16px;
            background: #000000;
            color: #00ffff;
            text-decoration: none;
            border: 1px solid #00ffff;
            font-weight: bold;
            font-family: 'Courier New', monospace;
            text-transform: uppercase;
            letter-spacing: 1px;
            text-shadow: 0 0 5px #00ffff;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
            transition: all 0.3s ease;
        }

        .nav-btn:hover {
            background: #00ffff;
            color: #000000;
            text-shadow: none;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
        }

        .nav-btn.active {
            background: #00ffff;
            color: #000000;
            text-shadow: none;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
        }

        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }

        .card {
            background: #000000;
            border: 1px solid #00ffff;
            padding: 15px;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
            transition: all 0.3s ease;
        }

        .card:hover {
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.6);
        }
        
        .card h2 {
            color: #00ffff;
            margin-bottom: 15px;
            font-size: 1.1em;
            display: flex;
            align-items: center;
            gap: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid #00ffff;
            padding-bottom: 8px;
            background: #000000;
            padding: 5px 10px;
            margin: -15px -15px 15px -15px;
            text-shadow: 0 0 5px #00ffff;
        }

        .card .icon {
            font-size: 1.2em;
        }

        .info-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            padding: 5px 0;
            border-bottom: 1px solid rgba(0, 255, 255, 0.3);
        }

        .info-item:last-child {
            border-bottom: none;
        }

        .info-label {
            color: #00ffff;
            font-weight: bold;
            text-shadow: 0 0 3px #00ffff;
        }

        .info-value {
            font-weight: bold;
            color: #ffffff;
            text-shadow: 0 0 3px #00ffff;
        }

        .progress-bar {
            width: 100%;
            height: 20px;
            background: #000000;
            border: 1px solid #00ffff;
            overflow: hidden;
            margin-top: 5px;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
            position: relative;
        }

        .progress-fill {
            height: 100%;
            background: #00ffff;
            transition: width 0.3s ease;
            box-shadow: 0 0 10px #00ffff;
        }

        .progress-fill.warning {
            background: #ffff00;
            box-shadow: 0 0 10px #ffff00;
        }

        .progress-fill.danger {
            background: #ff0000;
            box-shadow: 0 0 10px #ff0000;
        }

        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            margin-right: 8px;
            border-radius: 50%;
        }

        .status-good {
            background: #00ff00;
            box-shadow: 0 0 10px #00ff00;
            animation: pulse 1s infinite;
        }

        .status-warning {
            background: #ffff00;
            box-shadow: 0 0 10px #ffff00;
            animation: pulse 1s infinite;
        }

        .status-danger {
            background: #ff0000;
            box-shadow: 0 0 10px #ff0000;
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .gpu-card {
            grid-column: span 2;
        }
        
        .gpu-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .no-gpu {
            text-align: center;
            color: #808080;
            font-style: italic;
        }
        
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            
            .gpu-card {
                grid-column: span 1;
            }
        }
        
        .btn-warning {
            background: #000000;
            color: #ffff00;
            border: 1px solid #ffff00;
            font-family: 'Courier New', monospace;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 6px 12px;
            text-shadow: 0 0 5px #ffff00;
            box-shadow: 0 0 10px rgba(255, 255, 0, 0.3);
            transition: all 0.3s ease;
        }

        .btn-warning:hover {
            background: #ffff00;
            color: #000000;
            text-shadow: none;
            box-shadow: 0 0 20px rgba(255, 255, 0, 0.8);
        }

        .btn-success {
            background: #000000;
            color: #00ff00;
            border: 1px solid #00ff00;
            font-family: 'Courier New', monospace;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 6px 12px;
            text-shadow: 0 0 5px #00ff00;
            box-shadow: 0 0 10px rgba(0, 255, 0, 0.3);
            transition: all 0.3s ease;
        }

        .btn-success:hover {
            background: #00ff00;
            color: #000000;
            text-shadow: none;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.8);
        }

        .btn-danger {
            background: #000000;
            color: #ff0000;
            border: 1px solid #ff0000;
            font-family: 'Courier New', monospace;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 6px 12px;
            text-shadow: 0 0 5px #ff0000;
            box-shadow: 0 0 10px rgba(255, 0, 0, 0.3);
            transition: all 0.3s ease;
        }

        .btn-danger:hover {
            background: #ff0000;
            color: #000000;
            text-shadow: none;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.8);
        }

        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }

        .controls button {
            padding: 6px 12px;
            font-size: 0.9em;
            min-width: 80px;
            background: #000000;
            color: #00ffff;
            border: 1px solid #00ffff;
            font-family: 'Courier New', monospace;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
            text-shadow: 0 0 5px #00ffff;
            box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
            transition: all 0.3s ease;
        }

        .controls button:hover {
            background: #00ffff;
            color: #000000;
            text-shadow: none;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border: 1px solid #00ffff;
            color: #00ffff;
            font-weight: bold;
            font-family: 'Courier New', monospace;
            text-transform: uppercase;
            z-index: 1000;
            max-width: 300px;
            background: #000000;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
            text-shadow: 0 0 5px #00ffff;
            animation: slideIn 0.3s ease;
        }

        .notification.success {
            border-color: #00ff00;
            color: #00ff00;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.5);
            text-shadow: 0 0 5px #00ff00;
        }

        .notification.error {
            border-color: #ff0000;
            color: #ff0000;
            box-shadow: 0 0 20px rgba(255, 0, 0, 0.5);
            text-shadow: 0 0 5px #ff0000;
        }

        .notification.info {
            border-color: #00ffff;
            color: #00ffff;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ 系统监控面板</h1>
            <div class="time" id="currentTime">加载中...</div>
            <div class="nav-menu">
                <a href="/" class="nav-btn active">🖥️ 系统监控</a>
                <a href="/filemanager" class="nav-btn">📁 文件管理</a>
            </div>
        </div>
        
        <div class="dashboard">
            <!-- CPU信息卡片 -->
            <div class="card">
                <h2><span class="icon">🔥</span>CPU信息</h2>
                <div class="info-item">
                    <span class="info-label">使用率</span>
                    <span class="info-value" id="cpuPercent">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpuProgress"></div>
                </div>
                <div class="info-item">
                    <span class="info-label">频率</span>
                    <span class="info-value" id="cpuFreq">0 MHz</span>
                </div>
                <div class="info-item">
                    <span class="info-label">核心数</span>
                    <span class="info-value" id="cpuCount">0</span>
                </div>
                <div class="info-item">
                    <span class="info-label">型号</span>
                    <span class="info-value" id="cpuModel">Unknown</span>
                </div>
            </div>
            
            <!-- 功耗监控卡片 -->
            <div class="card">
                <h2><span class="icon">⚡</span>功耗监控</h2>
                <div class="info-item">
                    <span class="info-label">实时功耗</span>
                    <span class="info-value" id="powerWatts">0 W</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="powerProgress"></div>
                </div>
                <div class="info-item">
                    <span class="info-label">CPU电压</span>
                    <span class="info-value" id="cpuVoltage">0 V</span>
                </div>
                <div class="info-item">
                    <span class="info-label">CPU温度</span>
                    <span class="info-value" id="powerCpuTemp">0°C</span>
                </div>
            </div>
            
            <!-- 内存信息卡片 -->
            <div class="card">
                <h2><span class="icon">💾</span>内存信息</h2>
                <div class="info-item">
                    <span class="info-label">使用率</span>
                    <span class="info-value" id="memoryPercent">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="memoryProgress"></div>
                </div>
                <div class="info-item">
                    <span class="info-label">已使用</span>
                    <span class="info-value" id="memoryUsed">0 GB</span>
                </div>
                <div class="info-item">
                    <span class="info-label">可用</span>
                    <span class="info-value" id="memoryFree">0 GB</span>
                </div>
                <div class="info-item">
                    <span class="info-label">总容量</span>
                    <span class="info-value" id="memoryTotal">0 GB</span>
                </div>
            </div>
            
            <!-- 磁盘信息卡片 -->
            <div class="card">
                <h2><span class="icon">💿</span>磁盘信息</h2>
                <div class="info-item">
                    <span class="info-label">使用率</span>
                    <span class="info-value" id="diskPercent">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="diskProgress"></div>
                </div>
                <div class="info-item">
                    <span class="info-label">已使用</span>
                    <span class="info-value" id="diskUsed">0 GB</span>
                </div>
                <div class="info-item">
                    <span class="info-label">可用</span>
                    <span class="info-value" id="diskFree">0 GB</span>
                </div>
                <div class="info-item">
                    <span class="info-label">总容量</span>
                    <span class="info-value" id="diskTotal">0 GB</span>
                </div>
            </div>
            
            <!-- 网络信息卡片 -->
            <div class="card">
                <h2><span class="icon">🌐</span>网络信息</h2>
                <div class="info-item">
                    <span class="info-label">上传速度</span>
                    <span class="info-value" id="networkUpload">0 KB/s</span>
                </div>
                <div class="info-item">
                    <span class="info-label">下载速度</span>
                    <span class="info-value" id="networkDownload">0 KB/s</span>
                </div>
                <div class="info-item">
                    <span class="info-label">总上传</span>
                    <span class="info-value" id="networkSent">0 MB</span>
                </div>
                <div class="info-item">
                    <span class="info-label">总下载</span>
                    <span class="info-value" id="networkRecv">0 MB</span>
                </div>
            </div>
            
            <!-- IO信息卡片 -->
            <div class="card">
                <h2><span class="icon">📊</span>磁盘IO</h2>
                <div class="info-item">
                    <span class="info-label">读取速度</span>
                    <span class="info-value" id="ioReadSpeed">0 KB/s</span>
                </div>
                <div class="info-item">
                    <span class="info-label">写入速度</span>
                    <span class="info-value" id="ioWriteSpeed">0 KB/s</span>
                </div>
                <div class="info-item">
                    <span class="info-label">总读取</span>
                    <span class="info-value" id="ioReadBytes">0 MB</span>
                </div>
                <div class="info-item">
                    <span class="info-label">总写入</span>
                    <span class="info-value" id="ioWriteBytes">0 MB</span>
                </div>
            </div>
            
            
            
            <!-- 系统信息卡片 -->
            <div class="card">
                <h2><span class="icon">⚙️</span>系统信息</h2>
                <div class="info-item">
                    <span class="info-label">运行时间</span>
                    <span class="info-value" id="uptime">0 秒</span>
                </div>
                <div class="info-item">
                    <span class="info-label">更新时间</span>
                    <span class="info-value" id="updateTime">--:--:--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">系统状态</span>
                    <span class="info-value">
                        <span class="status-indicator status-good"></span>
                        正常运行
                    </span>
                </div>
                <div class="info-item">
                    <span class="info-label">操作系统</span>
                    <span class="info-value" id="osSystem">Unknown</span>
                </div>
                <div class="info-item">
                    <span class="info-label">内核版本</span>
                    <span class="info-value" id="osRelease">Unknown</span>
                </div>
                <div class="info-item">
                    <span class="info-label">系统架构</span>
                    <span class="info-value" id="osMachine">Unknown</span>
                </div>
            </div>
            
            <!-- 文件管理卡片 -->
            <div class="card">
                <h2><span class="icon">📁</span>文件管理</h2>
                <div class="info-item">
                    <span class="info-label">当前路径</span>
                    <span class="info-value" id="currentPath">/home/bi9bjv</span>
                </div>
                <div class="info-item">
                    <span class="info-label">文件数量</span>
                    <span class="info-value" id="fileCount">0</span>
                </div>
                <div class="info-item">
                    <span class="info-label">目录大小</span>
                    <span class="info-value" id="dirSize">0 MB</span>
                </div>
                <div class="controls" style="margin-top: 15px;">
                    <button onclick="openFileManager()" class="btn-success">打开文件管理</button>
                    <button onclick="refreshFileStats()" class="btn-warning">刷新统计</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function formatBytes(bytes, unit = 'B') {
            if (bytes === 0) return '0 ' + unit;
            
            const k = 1024;
            const sizes = ['', 'K', 'M', 'G', 'T'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i] + unit;
        }
        
        function formatUptime(seconds) {
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            
            if (days > 0) {
                return days + ' 天 ' + hours + ' 小时 ' + minutes + ' 分钟';
            } else if (hours > 0) {
                return hours + ' 小时 ' + minutes + ' 分钟';
            } else {
                return minutes + ' 分钟';
            }
        }
        
        function getProgressClass(percent) {
            if (percent < 60) return '';
            if (percent < 80) return 'warning';
            return 'danger';
        }
        
        function updateDisplay(data) {
            // 更新时间
            document.getElementById('currentTime').textContent = data.timestamp;
            document.getElementById('updateTime').textContent = new Date().toLocaleTimeString();
            
            // 更新CPU信息
            document.getElementById('cpuPercent').textContent = data.cpu.percent + '%';
            document.getElementById('cpuFreq').textContent = data.cpu.freq + ' MHz';
            document.getElementById('cpuCount').textContent = data.cpu.count;
            document.getElementById('cpuModel').textContent = data.cpu.model || 'Unknown';
            
            const cpuProgress = document.getElementById('cpuProgress');
            cpuProgress.style.width = data.cpu.percent + '%';
            cpuProgress.className = 'progress-fill ' + getProgressClass(data.cpu.percent);
            
            // 更新功耗信息
            document.getElementById('powerWatts').textContent = data.power.watts + ' W';
            document.getElementById('cpuVoltage').textContent = (data.cpu.voltage > 0) ? data.cpu.voltage + ' V' : 'N/A';
            document.getElementById('powerCpuTemp').textContent = data.cpu.temp + '°C';
            const powerProgress = document.getElementById('powerProgress');
            const powerPercent = Math.min((data.power.watts / 10) * 100, 100);
            powerProgress.style.width = powerPercent + '%';
            powerProgress.className = 'progress-fill ' + getProgressClass(powerPercent);
            
            // 更新内存信息
            document.getElementById('memoryPercent').textContent = data.memory.percent + '%';
            document.getElementById('memoryUsed').textContent = data.memory.used + ' GB';
            document.getElementById('memoryFree').textContent = data.memory.free + ' GB';
            document.getElementById('memoryTotal').textContent = data.memory.total + ' GB';
            
            const memoryProgress = document.getElementById('memoryProgress');
            memoryProgress.style.width = data.memory.percent + '%';
            memoryProgress.className = 'progress-fill ' + getProgressClass(data.memory.percent);
            
            // 更新磁盘信息
            document.getElementById('diskPercent').textContent = data.disk.percent + '%';
            document.getElementById('diskUsed').textContent = data.disk.used + ' GB';
            document.getElementById('diskFree').textContent = data.disk.free + ' GB';
            document.getElementById('diskTotal').textContent = data.disk.total + ' GB';
            
            const diskProgress = document.getElementById('diskProgress');
            diskProgress.style.width = data.disk.percent + '%';
            diskProgress.className = 'progress-fill ' + getProgressClass(data.disk.percent);
            
            // 更新网络信息
            document.getElementById('networkUpload').textContent = data.network.upload_speed + ' KB/s';
            document.getElementById('networkDownload').textContent = data.network.download_speed + ' KB/s';
            document.getElementById('networkSent').textContent = data.network.bytes_sent + ' MB';
            document.getElementById('networkRecv').textContent = data.network.bytes_recv + ' MB';
            
            // 更新IO信息
            document.getElementById('ioReadSpeed').textContent = data.io.read_speed + ' KB/s';
            document.getElementById('ioWriteSpeed').textContent = data.io.write_speed + ' KB/s';
            document.getElementById('ioReadBytes').textContent = data.io.read_bytes + ' MB';
            document.getElementById('ioWriteBytes').textContent = data.io.write_bytes + ' MB';
            
            // 更新系统信息
            document.getElementById('uptime').textContent = formatUptime(data.uptime);
            
            // 更新系统版本信息
            if (data.system) {
                document.getElementById('osSystem').textContent = data.system.system || 'Unknown';
                document.getElementById('osRelease').textContent = data.system.release || 'Unknown';
                document.getElementById('osMachine').textContent = data.system.machine || 'Unknown';
            }
        }
        
        // 定期获取系统信息
        async function fetchSystemInfo() {
            try {
                const response = await fetch('/api/system');
                const data = await response.json();
                updateDisplay(data);
            } catch (error) {
                console.error('获取系统信息失败:', error);
            }
        }
        
        // 远程控制功能
        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.opacity = '0';
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 3000);
        }
        
        function openFileManager() {
            window.open('/filemanager', '_blank');
        }
        
        async function refreshFileStats() {
            try {
                const response = await fetch('/api/files/stats');
                const data = await response.json();
                if (data.success) {
                    document.getElementById('currentPath').textContent = data.path;
                    document.getElementById('fileCount').textContent = data.file_count;
                    document.getElementById('dirSize').textContent = data.size;
                }
            } catch (error) {
                console.error('刷新文件统计失败:', error);
            }
        }
        
        // 启动监控
        fetchSystemInfo();
        setInterval(fetchSystemInfo, 1000);  // 每1秒更新一次，降低CPU占用
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/system')
def api_system():
    """系统信息API"""
    return jsonify(system_info)

# iFlow 命令缓存
iflow_cache = {}
iflow_cache_timeout = 300  # 5分钟缓存

@app.route('/api/iflow/execute', methods=['POST'])
def api_iflow_execute():
    """执行 iFlow 命令（优化版）"""
    data = request.get_json() or {}
    command = data.get('command', '')
    
    if not command:
        return jsonify({"success": False, "message": "命令不能为空"})
    
    # 检查缓存（仅对只读命令）
    cache_key = command
    if cache_key in iflow_cache:
        cached_data = iflow_cache[cache_key]
        if time.time() - cached_data['timestamp'] < iflow_cache_timeout:
            return jsonify({
                "success": True,
                "output": cached_data['output'],
                "message": "命令执行完成（缓存）"
            })
    
    try:
        import subprocess
        import os
        
        # 获取当前环境变量并确保 PATH 正确
        env = os.environ.copy()
        
        # 添加 nvm 的路径到环境变量
        nvm_path = '/home/bi9bjv/.nvm/versions/node/v24.12.0/bin'
        if 'PATH' in env:
            env['PATH'] = f"{nvm_path}:{env['PATH']}"
        else:
            env['PATH'] = nvm_path
        
        # 优化 Node.js 性能
        env['NODE_OPTIONS'] = '--max-old-space-size=512'
        
        # 使用完整路径执行 iflow 命令（使用列表形式，避免 shell=True）
        iflow_path = '/home/bi9bjv/.nvm/versions/node/v24.12.0/bin/iflow'
        
        # 解析命令参数
        cmd_args = command.split()
        full_command = [iflow_path] + cmd_args
        
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=120,
            env=env
        )
        
        output = result.stdout
        if result.stderr:
            output += '\n' + result.stderr
        
        # 缓存结果（仅对成功的结果）
        if result.returncode == 0 and len(output) < 10000:  # 只缓存小于10KB的结果
            iflow_cache[cache_key] = {
                'output': output,
                'timestamp': time.time()
            }
        
        return jsonify({
            "success": result.returncode == 0,
            "output": output,
            "message": "命令执行完成"
        })
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "message": "命令执行超时"})
    except Exception as e:
        return jsonify({"success": False, "message": f"命令执行失败: {str(e)}"})

# 文件管理API
@app.route('/api/files/list', methods=['GET'])
def api_files_list():
    """列出目录内容"""
    path = request.args.get('path', '')
    result = file_manager.list_directory(path)
    return jsonify(result)

@app.route('/api/files/info', methods=['GET'])
def api_files_info():
    """获取文件信息"""
    path = request.args.get('path', '')
    if not path:
        return jsonify({"success": False, "message": "路径不能为空"})
    
    result = file_manager.get_file_info(path)
    return jsonify(result)

@app.route('/api/files/upload', methods=['POST'])
def api_files_upload():
    """上传文件"""
    path = request.form.get('path', '')
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "没有文件"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "文件名为空"})
    
    safe_path = file_manager._safe_path(path)
    if not safe_path or not safe_path.exists():
        return jsonify({"success": False, "message": "目标路径不存在"})
    
    try:
        filename = file.filename
        file_path = safe_path / filename
        
        # 检查文件是否已存在
        if file_path.exists():
            return jsonify({"success": False, "message": "文件已存在"})
        
        file.save(str(file_path))
        return jsonify({"success": True, "message": "文件上传成功"})
    except Exception as e:
        return jsonify({"success": False, "message": f"上传失败: {str(e)}"})

@app.route('/api/files/download', methods=['GET'])
def api_files_download():
    """下载文件"""
    path = request.args.get('path', '')
    if not path:
        return jsonify({"success": False, "message": "路径不能为空"})
    
    safe_path = file_manager._safe_path(path)
    if not safe_path or not safe_path.exists():
        return jsonify({"success": False, "message": "文件不存在"})
    
    if safe_path.is_dir():
        return jsonify({"success": False, "message": "不能下载目录"})
    
    try:
        from flask import send_file
        return send_file(str(safe_path), as_attachment=True, download_name=safe_path.name)
    except Exception as e:
        return jsonify({"success": False, "message": f"下载失败: {str(e)}"})

@app.route('/api/files/create_dir', methods=['POST'])
def api_files_create_dir():
    """创建目录"""
    data = request.get_json() or {}
    path = data.get('path', '')
    name = data.get('name', '')
    
    if not name:
        return jsonify({"success": False, "message": "目录名不能为空"})
    
    result = file_manager.create_directory(path, name)
    return jsonify(result)

@app.route('/api/files/delete', methods=['POST'])
def api_files_delete():
    """删除文件或目录"""
    data = request.get_json() or {}
    path = data.get('path', '')
    
    if not path:
        return jsonify({"success": False, "message": "路径不能为空"})
    
    result = file_manager.delete_item(path)
    return jsonify(result)

@app.route('/api/files/rename', methods=['POST'])
def api_files_rename():
    """重命名文件或目录"""
    data = request.get_json() or {}
    path = data.get('path', '')
    new_name = data.get('new_name', '')
    
    if not path or not new_name:
        return jsonify({"success": False, "message": "路径和新名称不能为空"})
    
    result = file_manager.rename_item(path, new_name)
    return jsonify(result)

@app.route('/api/files/stats', methods=['GET'])
def api_files_stats():
    """获取目录统计信息"""
    path = request.args.get('path', '')
    result = file_manager.get_directory_stats(path)
    return jsonify(result)



@app.route('/filemanager')
def filemanager_page():
    with open("file_manager.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == '__main__':
    # 启动后台更新线程
    update_thread = threading.Thread(target=background_update, daemon=True)
    update_thread.start()
    
    # 初始化一次系统信息
    update_system_info()
    
    # 启动Flask应用，使用9001端口（避免冲突）
    app.run(host='0.0.0.0', port=9001, debug=False, threaded=True)