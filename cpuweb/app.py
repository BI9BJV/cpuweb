#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控Web应用 - 优化版
作者：BI9BJV
"""
import os
import time
import json
import threading
import subprocess
import logging
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request, send_from_directory
import psutil
from file_manager import file_manager
import traceback

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# 风扇状态监控相关全局变量
fan_control = {
    'enabled': True,  # 风扇控制是否启用
    'status': 'off',  # 'off', 'on', 'auto'
    'mode': 'auto',   # 'manual', 'auto'
    'speed': 50,      # 风扇转速 (0-100)
    'target_temp': 60,  # 自动模式下的目标温度
    'last_control_time': time.time(),  # 上次控制时间
    'next_switch_time': None,  # 下次开关时间
    'running_duration': 300,  # 连续运行时间（秒）5分钟
    'stop_duration': 300,     # 停止时间（秒）5分钟
    'current_state_start': time.time(),  # 当前状态开始时间
    'current_cycle_remaining': 0,  # 当前周期剩余时间
    'is_running': False  # 风扇当前是否运行
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
    
    # 格式化的运行时间字符串
    uptime_seconds = int(system_info['uptime'])
    days = uptime_seconds // (24 * 3600)
    hours = (uptime_seconds % (24 * 3600)) // 3600
    minutes = (uptime_seconds % 3600) // 60
    system_info['uptime_str'] = f"{days}天 {hours}小时 {minutes}分钟"
    
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

def update_fan_status():
    """更新风扇状态"""
    global fan_control
    
    current_time = time.time()
    
    # 获取当前CPU温度
    cpu_temp = get_cpu_temperature()
    
    # 更新当前周期剩余时间
    if fan_control["next_switch_time"]:
        remaining_time = max(0, fan_control["next_switch_time"] - current_time)
        fan_control["current_cycle_remaining"] = int(remaining_time)
    else:
        fan_control["current_cycle_remaining"] = 0
    
    # 根据模式控制风扇
    if fan_control["mode"] == "auto":
        # 自动模式：根据温度和循环控制
        if cpu_temp >= fan_control["target_temp"]:
            # 温度高于目标值时持续运行
            fan_control["status"] = "on"
            fan_control["is_running"] = True
            fan_control["next_switch_time"] = None  # 清除切换时间
        else:
            # 温度低于目标值时循环运行
            if fan_control["next_switch_time"] is None:
                # 初始化循环：如果风扇当前运行，设置停止时间；如果停止，设置运行时间
                if fan_control["is_running"]:
                    fan_control["next_switch_time"] = current_time + fan_control["running_duration"]
                else:
                    fan_control["next_switch_time"] = current_time + fan_control["stop_duration"]
            
            # 检查是否需要切换状态
            if current_time >= fan_control["next_switch_time"]:
                # 切换风扇状态
                fan_control["is_running"] = not fan_control["is_running"]
                if fan_control["is_running"]:
                    # 风扇开启：下次切换时间为开启持续时间后
                    fan_control["next_switch_time"] = current_time + fan_control["running_duration"]
                    fan_control["status"] = "on"
                else:
                    # 风扇关闭：下次切换时间为关闭持续时间后
                    fan_control["next_switch_time"] = current_time + fan_control["stop_duration"]
                    fan_control["status"] = "off"
    elif fan_control["mode"] == "manual":
        # 手动模式：按照设定状态运行
        fan_control["is_running"] = (fan_control["status"] == "on")
        
        # 在手动模式下，如果设置了运行状态，但next_switch_time存在（之前在自动模式下设置的）
        # 则清除next_switch_time以避免自动切换
        if fan_control["status"] == "on":
            fan_control["is_running"] = True
            fan_control["next_switch_time"] = None
        elif fan_control["status"] == "off":
            fan_control["is_running"] = False
            fan_control["next_switch_time"] = None
        fan_control['remaining_stopped_minutes'] = 0


def background_update():
    """后台更新系统信息"""
    while True:
        update_system_info()
        
        # 每10秒检查一次温度，但不进行硬件控制（硬件控制由独立程序处理）
        if int(time.time()) % 10 == 0:
            # 仅获取当前温度用于显示，不进行控制操作
            temp = get_cpu_temperature()
            # 更新内部状态但不执行控制
            print(f"[TEMP] CPU温度: {temp}°C (状态监控，无硬件控制)")  # 仅日志记录
        
        # 每秒更新风扇状态
        update_fan_status()
        
        time.sleep(0.5)  # 每0.5秒更新一次

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
        
        <div class="dashboard" id="dashboard">
            <!-- CPU信息卡片 -->
            <div class="card">
                <h2><span class="icon">⚙️</span>CPU信息</h2>
                <div class="info-item">
                    <span class="info-label">使用率</span>
                    <span class="info-value" id="cpuPercent">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpuProgress"></div>
                </div>
                <div class="info-item">
                    <span class="info-label">温度</span>
                    <span class="info-value" id="cpuTemp">0°C</span>
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
            
            <!-- 风扇控制卡片 -->
            <div class="card">
                <h2><span class="icon">🌀</span>风扇控制</h2>
                <div class="info-item">
                    <span class="info-label">运行状态</span>
                    <span class="info-value" id="fanStatus">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">运行模式</span>
                    <span class="info-value" id="fanMode">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">当前周期剩余</span>
                    <span class="info-value" id="fanCycleRemaining">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">运行时长</span>
                    <span class="info-value" id="fanRunningDuration">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">停止时长</span>
                    <span class="info-value" id="fanStopDuration">--</span>
                </div>
                <div class="controls">
                    <button class="btn-success" onclick="setFanMode('auto')">自动模式</button>
                    <button class="btn-warning" onclick="setFanMode('manual')">手动模式</button>
                    <button class="btn-success" onclick="setFanStatus('on')">开启</button>
                    <button class="btn-danger" onclick="setFanStatus('off')">关闭</button>
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
                    <span class="info-label">总量</span>
                    <span class="info-value" id="memoryTotal">0 GB</span>
                </div>
            </div>
            
            <!-- 磁盘信息卡片 -->
            <div class="card">
                <h2><span class="icon">💽</span>磁盘信息</h2>
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
                    <span class="info-label">总量</span>
                    <span class="info-value" id="diskTotal">0 GB</span>
                </div>
            </div>
            
            <!-- 网络信息卡片 -->
            <div class="card">
                <h2><span class="icon">🌐</span>网络信息</h2>
                <div class="info-item">
                    <span class="info-label">上传速度</span>
                    <span class="info-value" id="netUpload">0 KB/s</span>
                </div>
                <div class="info-item">
                    <span class="info-label">下载速度</span>
                    <span class="info-value" id="netDownload">0 KB/s</span>
                </div>
                <div class="info-item">
                    <span class="info-label">总上传</span>
                    <span class="info-value" id="netTotalUpload">0 MB</span>
                </div>
                <div class="info-item">
                    <span class="info-label">总下载</span>
                    <span class="info-value" id="netTotalDownload">0 MB</span>
                </div>
            </div>
            
            <!-- IO信息卡片 -->
            <div class="card">
                <h2><span class="icon">🔄</span>IO信息</h2>
                <div class="info-item">
                    <span class="info-label">读取速度</span>
                    <span class="info-value" id="ioRead">0 KB/s</span>
                </div>
                <div class="info-item">
                    <span class="info-label">写入速度</span>
                    <span class="info-value" id="ioWrite">0 KB/s</span>
                </div>
                <div class="info-item">
                    <span class="info-label">总读取</span>
                    <span class="info-value" id="ioTotalRead">0 MB</span>
                </div>
                <div class="info-item">
                    <span class="info-label">总写入</span>
                    <span class="info-value" id="ioTotalWrite">0 MB</span>
                </div>
            </div>
            
            <!-- 系统信息卡片 -->
            <div class="card">
                <h2><span class="icon">🖥️</span>系统信息</h2>
                <div class="info-item">
                    <span class="info-label">运行时间</span>
                    <span class="info-value" id="sysUptime">0天 0小时 0分钟</span>
                </div>
                <div class="info-item">
                    <span class="info-label">操作系统</span>
                    <span class="info-value" id="sysSystem">Unknown</span>
                </div>
                <div class="info-item">
                    <span class="info-label">内核版本</span>
                    <span class="info-value" id="sysRelease">Unknown</span>
                </div>
                <div class="info-item">
                    <span class="info-label">系统架构</span>
                    <span class="info-value" id="sysMachine">Unknown</span>
                </div>
                <div class="info-item">
                    <span class="info-label">更新时间</span>
                    <span class="info-value" id="currentTimestamp">--</span>
                </div>
            </div>
            
        </div>
    </div>

    <script>
        // JavaScript代码将通过API获取系统信息并更新UI
        async function fetchSystemInfo() {
            try {
                const response = await fetch('/api/system');
                const data = await response.json();

                // 更新CPU信息
                document.getElementById('cpuPercent').textContent = data.cpu.percent + '%';
                document.getElementById('cpuTemp').textContent = data.cpu.temp + '°C';
                document.getElementById('cpuFreq').textContent = data.cpu.freq + ' MHz';
                document.getElementById('cpuCount').textContent = data.cpu.count;
                document.getElementById('cpuModel').textContent = data.cpu.model;
                
                // 更新进度条
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
                
                // 更新内存进度条
                const memoryProgress = document.getElementById('memoryProgress');
                memoryProgress.style.width = data.memory.percent + '%';
                memoryProgress.className = 'progress-fill ' + getProgressClass(data.memory.percent);

                // 更新磁盘信息
                document.getElementById('diskPercent').textContent = data.disk.percent + '%';
                document.getElementById('diskUsed').textContent = data.disk.used + ' GB';
                document.getElementById('diskFree').textContent = data.disk.free + ' GB';
                document.getElementById('diskTotal').textContent = data.disk.total + ' GB';
                
                // 更新磁盘进度条
                const diskProgress = document.getElementById('diskProgress');
                diskProgress.style.width = data.disk.percent + '%';
                diskProgress.className = 'progress-fill ' + getProgressClass(data.disk.percent);

                // 更新网络信息
                document.getElementById('netUpload').textContent = data.network.upload_speed + ' KB/s';
                document.getElementById('netDownload').textContent = data.network.download_speed + ' KB/s';
                document.getElementById('netTotalUpload').textContent = data.network.bytes_sent + ' MB';
                document.getElementById('netTotalDownload').textContent = data.network.bytes_recv + ' MB';

                // 更新IO信息
                document.getElementById('ioRead').textContent = data.io.read_speed + ' KB/s';
                document.getElementById('ioWrite').textContent = data.io.write_speed + ' KB/s';
                document.getElementById('ioTotalRead').textContent = data.io.read_bytes + ' MB';
                document.getElementById('ioTotalWrite').textContent = data.io.write_bytes + ' MB';

                // 更新系统信息
                document.getElementById('sysUptime').textContent = formatUptime(data.uptime);
                document.getElementById('sysSystem').textContent = data.system.system;
                document.getElementById('sysRelease').textContent = data.system.release;
                document.getElementById('sysMachine').textContent = data.system.machine;
                document.getElementById('currentTimestamp').textContent = data.timestamp;
                
                // 更新风扇信息（如果存在）
                if (data.fan_control) {
                    document.getElementById('fanStatus').textContent = data.fan_control.is_running ? '运行中' : '已停止';
                    document.getElementById('fanMode').textContent = data.fan_control.mode === 'auto' ? '自动' : '手动';
                    
                    // 格式化剩余时间
                    const remainingSecs = data.fan_control.current_cycle_remaining || 0;
                    document.getElementById('fanCycleRemaining').textContent = formatSeconds(remainingSecs);
                    
                    document.getElementById('fanRunningDuration').textContent = formatSeconds(data.fan_control.running_duration || 0);
                    document.getElementById('fanStopDuration').textContent = formatSeconds(data.fan_control.stop_duration || 0);
                }
            } catch (error) {
                console.error('获取系统信息失败:', error);
            }
        }
        
        // 格式化秒数为时分秒
        function formatSeconds(seconds) {
            if (seconds <= 0) return '0秒';
            
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            
            let result = '';
            if (h > 0) result += h + '小时 ';
            if (m > 0) result += m + '分钟 ';
            if (s > 0 || result === '') result += s + '秒';
            
            return result.trim();
        }
        
        // 根据百分比返回进度条样式类
        function getProgressClass(percent) {
            if (percent < 60) return '';
            if (percent < 80) return 'warning';
            return 'danger';
        }

        // 格式化运行时间
        function formatUptime(seconds) {
            const days = Math.floor(seconds / (24 * 3600));
            const hours = Math.floor((seconds % (24 * 3600)) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${days}天 ${hours}小时 ${minutes}分钟`;
        }

        // 定期获取系统信息
        setInterval(fetchSystemInfo, 1000);  // 每1秒更新一次
        fetchSystemInfo();  // 页面加载时立即获取一次
        
        async function setFanMode(mode) {
            try {
                const response = await fetch('/api/fan/mode', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ mode: mode })
                });
                
                if (response.ok) {
                    console.log(`风扇模式已设置为: ${mode}`);
                    fetchSystemInfo(); // 立即更新显示
                } else {
                    console.error('设置风扇模式失败:', await response.text());
                }
            } catch (error) {
                console.error('设置风扇模式时发生错误:', error);
            }
        }
        
        async function setFanStatus(status) {
            try {
                const response = await fetch('/api/fan/status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ status: status })
                });
                
                if (response.ok) {
                    console.log(`风扇状态已设置为: ${status}`);
                    fetchSystemInfo(); // 立即更新显示
                } else {
                    console.error('设置风扇状态失败:', await response.text());
                }
            } catch (error) {
                console.error('设置风扇状态时发生错误:', error);
            }
        }
    </script>
</body>
</html>
"""

# 路由定义
@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

# 文件管理器页面路由
@app.route('/filemanager')
def filemanager_page():
    with open("file_manager.html", "r", encoding="utf-8") as f:
        return f.read()

# API端点
@app.route('/api/system', methods=['GET'])
def api_system():
    """系统信息API - 更新以包含风扇控制信息"""
    try:
        # 构造包含风扇控制信息的响应
        response_data = system_info.copy()
        response_data["fan_control"] = {
            "enabled": fan_control["enabled"],
            "status": fan_control["status"],
            "mode": fan_control["mode"],
            "speed": fan_control["speed"],
            "target_temp": fan_control["target_temp"],
            "running_duration": fan_control["running_duration"],
            "stop_duration": fan_control["stop_duration"],
            "current_cycle_remaining": fan_control["current_cycle_remaining"],
            "is_running": fan_control["is_running"],
            "next_switch_time": fan_control["next_switch_time"]
        }
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"获取系统信息时发生错误: {e}")
        return jsonify({"success": False, "message": f"获取系统信息时发生错误: {str(e)}"}), 500

# 文件管理API

@app.route('/api/files/list', methods=['GET'])

def api_files_list():

    """列出目录内容"""

    try:

        path = request.args.get('path', '')

        # 确保路径是字符串类型

        if not isinstance(path, str):

            return jsonify({"success": False, "message": "路径参数类型错误"}), 400

        

        result = file_manager.list_directory(path)

        return jsonify(result)

    except Exception as e:

        logger.error(f"列出目录时发生错误: {e}")

        return jsonify({"success": False, "message": f"列出目录时发生错误: {str(e)}"}), 500



@app.route('/api/files/info', methods=['GET'])

def api_files_info():

    """获取文件信息"""

    try:

        path = request.args.get('path', '')

        if not path:

            return jsonify({"success": False, "message": "路径不能为空"}), 400

        if not isinstance(path, str):

            return jsonify({"success": False, "message": "路径参数类型错误"}), 400

        

        result = file_manager.get_file_info(path)

        return jsonify(result)

    except Exception as e:

        logger.error(f"获取文件信息时发生错误: {e}")

        return jsonify({"success": False, "message": f"获取文件信息时发生错误: {str(e)}"}), 500



@app.route('/api/files/upload', methods=['POST'])

def api_files_upload():

    """上传文件"""

    try:

        # 获取路径参数

        path = request.form.get('path', '')

        if not path:

            return jsonify({"success": False, "message": "目标路径不能为空"}), 400

        

        if 'file' not in request.files:

            return jsonify({"success": False, "message": "没有文件被上传"}), 400

        

        file = request.files['file']

        if file.filename == '':

            return jsonify({"success": False, "message": "文件名为空"}), 400

        

        # 验证路径安全性

        safe_path = file_manager._safe_path(path)

        if not safe_path or not safe_path.exists():

            return jsonify({"success": False, "message": "目标路径不存在或不安全"}), 400

        

        try:

            filename = file.filename

            # 验证文件名

            if '..' in filename or filename.startswith('/'):

                return jsonify({"success": False, "message": "文件名包含非法字符"}), 400

            

            file_path = safe_path / filename

            

            # 检查文件是否已存在

            if file_path.exists():

                return jsonify({"success": False, "message": "文件已存在"}), 409

            

            # 检查文件大小

            file.seek(0, 2)  # 移动到文件末尾

            file_size = file.tell()

            file.seek(0)  # 移动回文件开头

            

            if file_size > file_manager.max_file_size:

                return jsonify({

                    "success": False, 

                    "message": f"文件过大 ({file_manager.format_size(file_size)})，超过限制 ({file_manager.format_size(file_manager.max_file_size)})"

                }), 413

            

            # 保存文件

            file.save(str(file_path))

            return jsonify({

                "success": True, 

                "message": "文件上传成功",

                "path": str(file_path.relative_to(file_manager.base_path)),

                "size": file_manager.format_size(file_size)

            })

        except Exception as e:

            logger.error(f"上传文件失败: {e}")

            return jsonify({"success": False, "message": f"上传失败: {str(e)}"}), 500

    except Exception as e:

        logger.error(f"上传文件时发生错误: {e}")

        return jsonify({"success": False, "message": f"上传文件时发生错误: {str(e)}"}), 500



@app.route('/api/files/download', methods=['GET'])

def api_files_download():

    """下载文件"""

    try:

        path = request.args.get('path', '')

        if not path:

            return jsonify({"success": False, "message": "路径不能为空"}), 400

        if not isinstance(path, str):

            return jsonify({"success": False, "message": "路径参数类型错误"}), 400

        

        safe_path = file_manager._safe_path(path)

        if not safe_path or not safe_path.exists():

            return jsonify({"success": False, "message": "文件不存在"}), 404

        

        if safe_path.is_dir():

            return jsonify({"success": False, "message": "不能下载目录"}), 400

        

        from flask import send_file

        import os

        

        # 检查文件权限

        if not os.access(str(safe_path), os.R_OK):

            return jsonify({"success": False, "message": "无权限访问文件"}), 403

        

        # Flask 3.1.2 使用 download_name 参数

        return send_file(str(safe_path), as_attachment=True, download_name=os.path.basename(str(safe_path)))

    except PermissionError:

        return jsonify({"success": False, "message": "无权限下载文件"}), 403

    except Exception as e:

        logger.error(f"下载文件时发生错误: {e}")

        return jsonify({"success": False, "message": f"下载文件时发生错误: {str(e)}"}), 500



# 创建目录API端点

@app.route('/api/files/create_dir', methods=['POST'])

def api_files_create_dir():

    """创建目录"""

    try:

        data = request.get_json()

        if not data:

            return jsonify({"success": False, "message": "请求体为空"}), 400

        

        path = data.get('path', '')

        name = data.get('name', '')

        

        if not path:

            return jsonify({"success": False, "message": "父路径不能为空"}), 400

        if not name:

            return jsonify({"success": False, "message": "目录名不能为空"}), 400

        if not isinstance(path, str) or not isinstance(name, str):

            return jsonify({"success": False, "message": "路径和名称必须为字符串"}), 400

        

        # 验证目录名

        if name in ['.', '..'] or '/' in name or '\\' in name:

            return jsonify({"success": False, "message": "目录名包含非法字符"}), 400

        

        result = file_manager.create_directory(path, name)

        return jsonify(result)

    except Exception as e:

        logger.error(f"创建目录时发生错误: {e}")

        return jsonify({"success": False, "message": f"创建目录时发生错误: {str(e)}"}), 500



# 删除文件API端点

@app.route('/api/files/delete', methods=['POST'])

def api_files_delete():

    """删除文件或目录"""

    try:

        data = request.get_json()

        if not data:

            return jsonify({"success": False, "message": "请求体为空"}), 400

        

        path = data.get('path', '')

        if not path:

            return jsonify({"success": False, "message": "路径不能为空"}), 400

        if not isinstance(path, str):

            return jsonify({"success": False, "message": "路径参数类型错误"}), 400

        

        result = file_manager.delete_item(path)

        return jsonify(result)

    except Exception as e:

        logger.error(f"删除文件时发生错误: {e}")

        return jsonify({"success": False, "message": f"删除文件时发生错误: {str(e)}"}), 500



# 重命名API端点

@app.route('/api/files/rename', methods=['POST'])

def api_files_rename():

    """重命名文件或目录"""

    try:

        data = request.get_json()

        if not data:

            return jsonify({"success": False, "message": "请求体为空"}), 400

        

        path = data.get('path', '')

        new_name = data.get('new_name', '')

        

        if not path or not new_name:

            return jsonify({"success": False, "message": "路径和新名称不能为空"}), 400

        if not isinstance(path, str) or not isinstance(new_name, str):

            return jsonify({"success": False, "message": "路径和名称必须为字符串"}), 400

        

        # 验证新名称

        if new_name in ['.', '..'] or '/' in new_name or '\\' in new_name:

            return jsonify({"success": False, "message": "新名称包含非法字符"}), 400

        

        result = file_manager.rename_item(path, new_name)

        return jsonify(result)

    except Exception as e:

        logger.error(f"重命名时发生错误: {e}")

        return jsonify({"success": False, "message": f"重命名时发生错误: {str(e)}"}), 500



# 目录统计API端点

@app.route('/api/files/stats', methods=['GET'])

def api_files_stats():

    """获取目录统计信息"""

    try:

        path = request.args.get('path', '')

        if not isinstance(path, str):

            return jsonify({"success": False, "message": "路径参数类型错误"}), 400

        

        result = file_manager.get_directory_stats(path)

        return jsonify(result)

    except Exception as e:

        logger.error(f"获取统计信息时发生错误: {e}")

        return jsonify({"success": False, "message": f"获取统计信息时发生错误: {str(e)}"}), 500



# 读取文件内容API端点

@app.route('/api/files/read', methods=['GET'])

def api_files_read():

    """读取文件内容"""

    try:

        path = request.args.get('path', '')

        if not path:

            return jsonify({"success": False, "message": "路径不能为空"}), 400

        if not isinstance(path, str):

            return jsonify({"success": False, "message": "路径参数类型错误"}), 400

        

        # 可选的大小限制参数

        max_size_str = request.args.get('max_size')

        max_size = None

        if max_size_str:

            try:

                max_size = int(max_size_str)

            except ValueError:

                return jsonify({"success": False, "message": "max_size参数必须为整数"}), 400

        

        result = file_manager.read_file_content(path, max_size)

        return jsonify(result)

    except Exception as e:

        logger.error(f"读取文件内容时发生错误: {e}")

        return jsonify({"success": False, "message": f"读取文件内容时发生错误: {str(e)}"}), 500



# 写入文件内容API端点

@app.route('/api/files/write', methods=['POST'])

def api_files_write():

    """写入文件内容"""

    try:

        data = request.get_json()

        if not data:

            return jsonify({"success": False, "message": "请求体为空"}), 400

        

        path = data.get('path', '')

        content = data.get('content', '')

        overwrite = data.get('overwrite', True)

        

        if not path:

            return jsonify({"success": False, "message": "路径不能为空"}), 400

        if not isinstance(path, str):

            return jsonify({"success": False, "message": "路径参数类型错误"}), 400

        if not isinstance(content, str):

            return jsonify({"success": False, "message": "内容必须为字符串"}), 400

        

        result = file_manager.write_file_content(path, content, overwrite)

        return jsonify(result)

    except Exception as e:

        logger.error(f"写入文件内容时发生错误: {e}")

        return jsonify({"success": False, "message": f"写入文件内容时发生错误: {str(e)}"}), 500


# 风扇控制API端点
@app.route('/api/fan/mode', methods=['POST'])
def api_fan_mode():
    """设置风扇运行模式"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求体为空"}), 400
        
        mode = data.get('mode')
        if mode not in ['auto', 'manual']:
            return jsonify({"success": False, "message": "无效的模式，仅支持 'auto' 或 'manual'"}), 400
        
        # 更新风扇模式
        fan_control['mode'] = mode
        fan_control['last_control_time'] = time.time()
        
        # 在自动模式下，根据当前温度重新设置状态
        if mode == 'auto':
            cpu_temp = get_cpu_temperature()
            if cpu_temp >= fan_control['target_temp']:
                fan_control['is_running'] = True
                fan_control['status'] = 'on'
                fan_control['next_switch_time'] = None
            else:
                # 对于自动模式的循环，设置下次切换时间
                current_time = time.time()
                if fan_control['is_running']:
                    fan_control['next_switch_time'] = current_time + fan_control['running_duration']
                else:
                    fan_control['next_switch_time'] = current_time + fan_control['stop_duration']
        
        return jsonify({
            "success": True, 
            "message": f"风扇模式已设置为 {mode}",
            "fan_control": {
                "mode": fan_control['mode'],
                "status": fan_control['status'],
                "is_running": fan_control['is_running']
            }
        })
    except Exception as e:
        logger.error(f"设置风扇模式时发生错误: {e}")
        return jsonify({"success": False, "message": f"设置风扇模式时发生错误: {str(e)}"}), 500


@app.route('/api/fan/status', methods=['POST'])
def api_fan_status_control():
    """设置风扇运行状态"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求体为空"}), 400
        
        status = data.get('status')
        if status not in ['on', 'off']:
            return jsonify({"success": False, "message": "无效的状态，仅支持 'on' 或 'off'"}), 400
        
        # 更新风扇状态
        fan_control['status'] = status
        fan_control['is_running'] = (status == 'on')
        fan_control['last_control_time'] = time.time()
        
        # 如果是手动模式，直接设置状态
        if fan_control['mode'] == 'manual':
            fan_control['is_running'] = (status == 'on')
        
        return jsonify({
            "success": True, 
            "message": f"风扇状态已设置为 {status}",
            "fan_control": {
                "status": fan_control['status'],
                "is_running": fan_control['is_running'],
                "mode": fan_control['mode']
            }
        })
    except Exception as e:
        logger.error(f"设置风扇状态时发生错误: {e}")
        return jsonify({"success": False, "message": f"设置风扇状态时发生错误: {str(e)}"}), 500


@app.route('/api/fan/control_event', methods=['POST'])
def api_fan_control_event():
    """接收外部风扇控制事件（如来自温度管控程序）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求体为空"}), 400
        
        action = data.get('action')
        temperature = data.get('temperature')
        
        if action not in ['start', 'stop']:
            return jsonify({"success": False, "message": "无效的动作，仅支持 'start' 或 'stop'"}), 400
        
        # 记录外部控制事件
        current_time = time.time()
        logger.info(f"外部风扇控制事件: {action}, 温度: {temperature}°C, 时间: {time.ctime(current_time)}")
        
        # 更新内部状态以匹配外部控制
        fan_control['is_running'] = (action == 'start')
        fan_control['status'] = 'on' if action == 'start' else 'off'
        fan_control['last_control_time'] = current_time
        
        return jsonify({
            "success": True,
            "message": f"外部风扇控制事件 {action} 已记录",
            "fan_control": {
                "status": fan_control['status'],
                "is_running": fan_control['is_running'],
                "mode": fan_control['mode']
            }
        })
    except Exception as e:
        logger.error(f"处理外部风扇控制事件时发生错误: {e}")
        return jsonify({"success": False, "message": f"处理外部风扇控制事件时发生错误: {str(e)}"}), 500





# 风扇控制API端点
@app.route("/api/fan/status", methods=["GET"])
def api_fan_status_get():
    """获取风扇状态（只读监控）"""
    try:
        return jsonify({
            "success": True, 
            "fan_control": {
                "enabled": fan_control["enabled"],
                "status": fan_control["status"],
                "running_mode": fan_control["running_mode"],
                "running_minutes": fan_control["running_minutes"],
                "remaining_running_minutes": fan_control["remaining_running_minutes"],
                "stopped_minutes": fan_control["stopped_minutes"],
                "remaining_stopped_minutes": fan_control["remaining_stopped_minutes"],
                "total_cycle_minutes": fan_control["total_cycle_minutes"],
                "cycle_position": fan_control["cycle_position"],
                "is_running": fan_control["is_running"],
                "last_status_change": datetime.fromtimestamp(fan_control["last_status_change"]).strftime("%Y-%m-%d %H:%M:%S"),
                "current_status_start": datetime.fromtimestamp(fan_control["current_status_start"]).strftime("%Y-%m-%d %H:%M:%S")
            }
        })
    except Exception as e:
        logger.error(f"获取风扇状态时发生错误: {e}")
        return jsonify({"success": False, "message": f"获取风扇状态时发生错误: {str(e)}"}), 500

# 以下是关键的全局错误处理程序，这是修复文件管理模块问题的核心
# 全局错误处理程序，确保所有错误都返回JSON格式
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "message": "API端点不存在"}), 404
    return render_template_string(HTML_TEMPLATE), 404

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "message": "服务器内部错误"}), 500
    return render_template_string(HTML_TEMPLATE), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # 记录异常详情用于调试
    logger.error(f"未处理的异常: {e}", exc_info=True)
    
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "message": f"发生异常: {str(e)}"}), 500
    return render_template_string(HTML_TEMPLATE), 500







# 添加一个中间件来确保API响应始终是JSON格式
@app.after_request
def after_request(response):
    # 如果请求路径以/api/开头，确保Content-Type是JSON
    if request.path.startswith('/api/'):
        # 如果响应不是JSON格式，记录警告
        if not response.content_type.startswith('application/json'):
            logger.warning(f"API请求返回了非JSON格式: {request.path}, Content-Type: {response.content_type}")
            # 注意：这里不修改响应，因为可能已经发送了数据
    return response

# 启动应用
if __name__ == '__main__':
    # 启动后台更新线程
    update_thread = threading.Thread(target=background_update, daemon=True)
    update_thread.start()
    
    # 初始化一次系统信息
    update_system_info()
    
    # 启动Flask应用，使用9001端口（避免冲突）
    app.run(host='0.0.0.0', port=9001, debug=False, threaded=True)