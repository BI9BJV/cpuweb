#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
脚本用于还原app.py中的风扇控制功能
"""

def restore_fan_control():
    # 读取原文件
    with open('/home/bi9bjv/python/cpuweb/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修改全局变量定义，将fan_control相关参数恢复
    old_fan_var = """fan_control = {
    'enabled': True,  # 风扇监控是否启用
    'status': 'off',  # 'off', 'on' - 当前风扇状态
    'running_mode': 'continuous',  # 'continuous', 'cycling' - 运行模式
    'last_status_change': time.time(),  # 上次状态改变时间
    'current_status_start': time.time(),  # 当前状态开始时间
    'running_minutes': 0,  # 风扇已运行分钟数
    'remaining_running_minutes': 0,  # 风扇剩余运行分钟数
    'stopped_minutes': 0,  # 风扇已停止分钟数
    'remaining_stopped_minutes': 0,  # 风扇剩余停止分钟数
    'total_cycle_minutes': 10,  # 总循环时长（分钟）- 5分钟运行+5分钟停止
    'cycle_position': 0,  # 当前在循环中的位置（分钟）
    'is_running': False  # 风扇当前是否运行
}"""
    
    new_fan_var = """fan_control = {
    'enabled': True,  # 风扇控制是否启用
    'status': 'off',  # 'off', 'on', 'auto'
    'mode': 'auto',   # 'manual', 'auto'
    'speed': 50,      # 风扇转速 (0-100)
    'target_temp': 60,  # 自动模式下的目标温度
    'last_control_time': time.time(),  # 上次控制时间
    'next_switch_time': None,  # 下次开关时间
    'running_duration': 300,  # 连续运行时间（秒）5分钟
    'stop_duration': 120,     # 停止时间（秒）2分钟
    'current_state_start': time.time(),  # 当前状态开始时间
    'current_cycle_remaining': 0,  # 当前周期剩余时间
    'is_running': False  # 风扇当前是否运行
}"""
    
    content = content.replace(old_fan_var, new_fan_var)
    
    # 2. 添加控制API端点
    api_endpoints_insert = '''
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


'''
    
    # 找到api_files_write函数结束位置并插入API端点
    # 使用正则表达式或简单的字符串匹配
    api_files_write_end = 'return jsonify({"success": False, "message": f"写入文件内容时发生错误: {str(e)}"}), 500'
    if api_files_write_end in content:
        content = content.replace(api_files_write_end, api_files_write_end + "\n\n" + api_endpoints_insert)
    
    # 3. 修改api_system函数，确保fan_control信息被包含
    if "data.fan_monitor" in content:
        content = content.replace("data.fan_monitor", "data.fan_control")
    
    # 4. 修改update_fan_status函数 - 先查找当前函数定义
    if '"更新风扇状态监控"' in content:
        old_function = '''def update_fan_status():
    """更新风扇状态监控"""
    global fan_control

    current_time = time.time()

    # 获取当前CPU温度
    cpu_temp = get_cpu_temperature()

    # 计算已运行分钟数和剩余分钟数
    elapsed_time = current_time - fan_control['current_status_start']
    elapsed_minutes = int(elapsed_time / 60)

    # 更新监控数据
    if fan_control['is_running']:
        fan_control['running_minutes'] = elapsed_minutes
        fan_control['stopped_minutes'] = 0
        fan_control['remaining_running_minutes'] = max(0, fan_control['total_cycle_minutes'] - elapsed_minutes)
        fan_control['remaining_stopped_minutes'] = 0
    else:
        fan_control['stopped_minutes'] = elapsed_minutes
        fan_control['running_minutes'] = 0
        fan_control['remaining_stopped_minutes'] = max(0, fan_control['total_cycle_minutes'] - elapsed_minutes)
        fan_control['remaining_running_minutes'] = 0

    # 更新周期位置
    total_cycle_seconds = fan_control['total_cycle_minutes'] * 60
    cycle_position = int((current_time - fan_control['last_status_change']) % total_cycle_seconds)
    fan_control['cycle_position'] = int(cycle_position / 60)
'''
        new_function = '''def update_fan_status():
    """更新风扇状态"""
    global fan_control
    
    current_time = time.time()
    
    # 获取当前CPU温度
    cpu_temp = get_cpu_temperature()
    
    # 更新当前周期剩余时间
    if fan_control['next_switch_time']:
        remaining_time = max(0, fan_control['next_switch_time'] - current_time)
        fan_control['current_cycle_remaining'] = int(remaining_time)
    else:
        fan_control['current_cycle_remaining'] = 0
    
    # 根据模式控制风扇
    if fan_control['mode'] == 'auto':
        # 自动模式：根据温度和循环控制
        if cpu_temp >= fan_control['target_temp']:
            # 温度高于目标值时持续运行
            fan_control['status'] = 'on'
            fan_control['is_running'] = True
            fan_control['next_switch_time'] = None  # 清除切换时间
        else:
            # 温度低于目标值时循环运行
            if fan_control['next_switch_time'] is None:
                # 初始化循环：如果风扇当前运行，设置停止时间；如果停止，设置运行时间
                if fan_control['is_running']:
                    fan_control['next_switch_time'] = current_time + fan_control['running_duration']
                else:
                    fan_control['next_switch_time'] = current_time + fan_control['stop_duration']
            
            # 检查是否需要切换状态
            if current_time >= fan_control['next_switch_time']:
                # 切换风扇状态
                fan_control['is_running'] = not fan_control['is_running']
                if fan_control['is_running']:
                    # 风扇开启：下次切换时间为开启持续时间后
                    fan_control['next_switch_time'] = current_time + fan_control['running_duration']
                    fan_control['status'] = 'on'
                else:
                    # 风扇关闭：下次切换时间为关闭持续时间后
                    fan_control['next_switch_time'] = current_time + fan_control['stop_duration']
                    fan_control['status'] = 'off'
    elif fan_control['mode'] == 'manual':
        # 手动模式：按照设定状态运行
        fan_control['is_running'] = (fan_control['status'] == 'on')
        
        # 在手动模式下，如果设置了运行状态，但next_switch_time存在（之前在自动模式下设置的）
        # 则清除next_switch_time以避免自动切换
        if fan_control['status'] == 'on':
            fan_control['is_running'] = True
            fan_control['next_switch_time'] = None
        elif fan_control['status'] == 'off':
            fan_control['is_running'] = False
            fan_control['next_switch_time'] = None'''
        content = content.replace(old_function, new_function)
    
    # 5. 修改HTML界面部分，从监控改为控制
    content = content.replace('风扇监控', '风扇控制')
    content = content.replace('<!-- 风扇监控卡片 -->', '<!-- 风扇控制卡片 -->')
    
    # 替换HTML中的内容
    old_html_content = """<div class="info-item">
                    <span class="info-label">运行状态</span>
                    <span class="info-value" id="fanStatus">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">运行模式</span>
                    <span class="info-value" id="fanMode">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">运行分钟数</span>
                    <span class="info-value" id="fanRunningMinutes">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">剩余运行分钟数</span>
                    <span class="info-value" id="fanRemainingRunningMinutes">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">停止分钟数</span>
                    <span class="info-value" id="fanStoppedMinutes">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">剩余停止分钟数</span>
                    <span class="info-value" id="fanRemainingStoppedMinutes">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">总周期分钟数</span>
                    <span class="info-value" id="fanTotalCycleMinutes">--</span>
                </div>
                <div class="info-item">
                    <span class="info-label">周期位置</span>
                    <span class="info-value" id="fanCyclePosition">--</span>
                </div>"""
    
    new_html_content = """<div class="info-item">
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
                </div>"""
    
    content = content.replace(old_html_content, new_html_content)
    
    # 6. 修改api_fan_status函数名，避免与新的控制API冲突
    content = content.replace(
        'def api_fan_status():',
        'def api_fan_status_get():'
    )
    
    # 7. 添加JavaScript控制函数（在fetchSystemInfo函数之后）
    js_control_functions = '''
        // 风扇控制函数
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
                    console.error(`设置风扇模式失败: ${response.status}`);
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
                    console.error(`设置风扇状态失败: ${response.status}`);
                }
            } catch (error) {
                console.error('设置风扇状态时发生错误:', error);
            }
        }
    '''
    
    # 检查JavaScript函数是否已经存在，如果不存在则添加
    if 'setFanMode' not in content and 'setFanStatus' not in content:
        # 在fetchSystemInfo函数结束后（在fetchSystemInfo()调用之前）添加控制函数
        fetch_system_end = "fetchSystemInfo();  // 页面加载时立即获取一次"
        if fetch_system_end in content:
            content = content.replace(fetch_system_end, js_control_functions + "\n        " + fetch_system_end)
    
    # 写回文件
    with open('/home/bi9bjv/python/cpuweb/app.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    restore_fan_control()
    print("风扇控制功能已还原完成")