#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派温度控制风扇项目
功能：当CPU温度高于40度时持续运行风扇，低于40度时运行5分钟停止5分钟循环
作者：BI9BJV
日期：2025年12月
"""

import time
import os
import RPi.GPIO as GPIO
import requests

# 禁用GPIO警告
GPIO.setwarnings(False)

# 配置参数
FAN_PIN = 14  # GPIO BCM码14
HIGH_TEMP = 40.0  # 高温阈值（度）
TEMP_CHECK_INTERVAL = 1  # 温度检查间隔（秒）
TEMP_PATH = '/sys/class/thermal/thermal_zone0/temp'  # 温度传感器路径
CYCLE_DURATION = 300  # 循环周期（秒），5分钟=300秒

# 全局变量
fan_status = False  # 风扇状态 False=关闭, True=开启
last_switch_time = time.time()  # 上次切换时间
is_in_cooling_period = False  # 是否处于降温模式

def get_cpu_temperature():
    """
    获取CPU温度
    返回温度值（摄氏度）
    """
    try:
        with open(TEMP_PATH, 'r') as f:
            temp_raw = f.read().strip()
            temp_celsius = float(temp_raw) / 1000.0
            return temp_celsius
    except FileNotFoundError:
        print(f"错误：找不到温度传感器文件 {TEMP_PATH}")
        return None
    except Exception as e:
        print(f"读取温度时发生错误: {e}")
        return None

def setup_gpio():
    """
    初始化GPIO
    """
    global fan_status
    try:
        # 设置GPIO模式为BCM
        GPIO.setmode(GPIO.BCM)
        # 设置风扇引脚为输出模式
        GPIO.setup(FAN_PIN, GPIO.OUT)
        # 初始状态关闭风扇
        GPIO.output(FAN_PIN, GPIO.LOW)
        fan_status = False
        print(f"GPIO初始化成功，风扇引脚: BCM {FAN_PIN}")
        return True
    except Exception as e:
        print(f"GPIO初始化失败: {e}")
        return False

def control_fan(turn_on):
    """
    控制风扇开关
    :param turn_on: True为开启风扇，False为关闭风扇
    """
    global fan_status
    if turn_on and not fan_status:
        # 开启风扇
        GPIO.output(FAN_PIN, GPIO.HIGH)
        fan_status = True
        current_temp = get_cpu_temperature()
        print(f"风扇已开启 - 当前温度: {current_temp:.2f}°C")
        
        # 向CPUWeb同步风扇开启事件
        try:
            response = requests.post(
                'http://localhost:9001/api/fan/control_event',
                json={'action': 'start', 'temperature': current_temp},
                timeout=5
            )
            if response.status_code == 200:
                print(f"风扇开启事件已同步到CPUWeb - 温度: {current_temp:.2f}°C")
            else:
                print(f"同步风扇开启事件到CPUWeb失败: {response.status_code}")
        except Exception as e:
            print(f"同步风扇开启事件到CPUWeb时出错: {e}")
    elif not turn_on and fan_status:
        # 关闭风扇
        GPIO.output(FAN_PIN, GPIO.LOW)
        fan_status = False
        current_temp = get_cpu_temperature()
        print(f"风扇已关闭 - 当前温度: {current_temp:.2f}°C")
        
        # 向CPUWeb同步风扇关闭事件
        try:
            response = requests.post(
                'http://localhost:9001/api/fan/control_event',
                json={'action': 'stop', 'temperature': current_temp},
                timeout=5
            )
            if response.status_code == 200:
                print(f"风扇关闭事件已同步到CPUWeb - 温度: {current_temp:.2f}°C")
            else:
                print(f"同步风扇关闭事件到CPUWeb失败: {response.status_code}")
        except Exception as e:
            print(f"同步风扇关闭事件到CPUWeb时出错: {e}")

def cleanup():
    """
    清理GPIO资源
    """
    try:
        GPIO.cleanup()
        print("GPIO资源已清理")
    except Exception as e:
        print(f"清理GPIO资源时出错: {e}")

def main():
    """
    主函数
    """
    global fan_status, last_switch_time, is_in_cooling_period
    
    print("树莓派温度控制风扇系统启动")
    print(f"高温阈值: {HIGH_TEMP}°C")
    print(f"温度检查间隔: {TEMP_CHECK_INTERVAL}秒")
    print(f"风扇控制引脚: BCM {FAN_PIN}")
    print(f"循环周期: {CYCLE_DURATION}秒 (运行5分钟，停止5分钟)")
    print("-" * 50)
    
    # 初始化GPIO
    if not setup_gpio():
        print("初始化失败，程序退出")
        return
    
    try:
        while True:
            # 获取当前CPU温度
            current_temp = get_cpu_temperature()
            
            if current_temp is not None:
                print(f"当前CPU温度: {current_temp:.2f}°C, 风扇状态: {'开启' if fan_status else '关闭'}, 模式: {'持续运行' if current_temp >= HIGH_TEMP else '循环模式'}")
                
                # 根据温度控制风扇
                if current_temp >= HIGH_TEMP:
                    # 高于40度时持续运行风扇
                    if not fan_status:
                        control_fan(True)
                        is_in_cooling_period = False  # 重置循环模式状态
                else:
                    # 低于40度时执行循环模式：运行5分钟，停止5分钟
                    current_time = time.time()
                    elapsed_time = current_time - last_switch_time
                    
                    if is_in_cooling_period:
                        # 在降温模式下：运行5分钟，然后切换到休息模式
                        if elapsed_time >= CYCLE_DURATION:  # 5分钟运行时间
                            print("降温模式：运行5分钟结束，切换到停止模式")
                            control_fan(False)
                            last_switch_time = current_time
                            is_in_cooling_period = False
                    else:
                        # 在休息模式下：停止5分钟，然后切换到运行模式
                        if elapsed_time >= CYCLE_DURATION:  # 5分钟停止时间
                            print("休息模式：停止5分钟结束，切换到运行模式")
                            control_fan(True)
                            last_switch_time = current_time
                            is_in_cooling_period = True
                            
            else:
                print("无法读取温度，跳过此次检查")
            
            # 等待下一次检查
            time.sleep(TEMP_CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n收到中断信号，正在关闭...")
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
