#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的文件管理功能流程
"""
import requests
import json
import time
import tempfile
import os

def test_full_filemanager_workflow():
    """测试完整的文件管理器工作流程"""
    base_url = "http://127.0.0.1:9001"
    
    print("开始测试完整的文件管理器工作流程...")
    
    # 1. 测试浏览根目录
    print("\n1. 测试浏览根目录:")
    try:
        response = requests.get(f"{base_url}/api/files/list")
        response.raise_for_status()
        data = response.json()
        print(f"   ✓ 成功获取根目录内容，返回 {data.get('total_items', 0)} 个项目")
        if data['success']:
            print(f"   ✓ 当前路径: {data.get('current_path', '')}")
        else:
            print(f"   ⚠ 信息: {data.get('message', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
    
    # 2. 测试创建目录
    print("\n2. 测试创建目录:")
    try:
        import uuid
        dir_name = f"test_dir_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        response = requests.post(f"{base_url}/api/files/create_dir", 
                                json={"path": "", "name": dir_name})
        response.raise_for_status()
        data = response.json()
        if data['success']:
            print(f"   ✓ 目录创建成功: {dir_name}")
            created_dir_path = data['path']
        else:
            print(f"   ⚠ 目录创建失败: {data.get('message', 'Unknown')}")
            # 即使失败也继续测试
            created_dir_path = f"test/{dir_name}"
    except Exception as e:
        print(f"   ✗ 创建目录失败: {e}")
        created_dir_path = f"test/test_dir_{int(time.time())}"
    
    # 3. 测试在新目录中创建文件
    print("\n3. 测试在新目录中写入文件:")
    try:
        file_path = f"{created_dir_path}/test_file.txt"
        content = f"这是一个测试文件\n创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n随机内容: {uuid.uuid4()}"
        response = requests.post(f"{base_url}/api/files/write", 
                                json={"path": file_path, "content": content})
        response.raise_for_status()
        data = response.json()
        if data['success']:
            print(f"   ✓ 文件写入成功: {file_path}")
        else:
            print(f"   ⚠ 文件写入失败: {data.get('message', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ 文件写入失败: {e}")
    
    # 4. 测试读取文件内容
    print("\n4. 测试读取文件内容:")
    try:
        response = requests.get(f"{base_url}/api/files/read?path={created_dir_path}/test_file.txt")
        response.raise_for_status()
        data = response.json()
        if data['success']:
            print(f"   ✓ 成功读取文件内容，大小: {data.get('size', 'Unknown')}")
            print(f"   ✓ 内容行数: {data.get('lines', 0)}")
        else:
            print(f"   ⚠ 读取文件失败: {data.get('message', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ 读取文件失败: {e}")
    
    # 5. 测试获取文件信息
    print("\n5. 测试获取文件信息:")
    try:
        response = requests.get(f"{base_url}/api/files/info?path={created_dir_path}/test_file.txt")
        response.raise_for_status()
        data = response.json()
        if data['success']:
            print(f"   ✓ 成功获取文件信息: {data.get('name', 'Unknown')}")
        else:
            print(f"   ⚠ 获取文件信息失败: {data.get('message', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ 获取文件信息失败: {e}")
    
    # 6. 测试获取目录统计信息
    print("\n6. 测试获取目录统计信息:")
    try:
        response = requests.get(f"{base_url}/api/files/stats?path={created_dir_path}")
        response.raise_for_status()
        data = response.json()
        if data['success']:
            print(f"   ✓ 成功获取目录统计: {data.get('file_count', 0)} 个文件, {data.get('directory_count', 0)} 个目录")
        else:
            print(f"   ⚠ 获取统计信息失败: {data.get('message', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ 获取统计信息失败: {e}")
    
    # 7. 测试重命名文件
    print("\n7. 测试重命名文件:")
    try:
        response = requests.post(f"{base_url}/api/files/rename", 
                                json={"path": f"{created_dir_path}/test_file.txt", 
                                      "new_name": "renamed_test_file.txt"})
        response.raise_for_status()
        data = response.json()
        if data['success']:
            print(f"   ✓ 文件重命名成功")
        else:
            print(f"   ⚠ 文件重命名失败: {data.get('message', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ 文件重命名失败: {e}")
    
    # 8. 清理: 删除测试目录
    print("\n8. 清理测试文件:")
    try:
        response = requests.post(f"{base_url}/api/files/delete", 
                                json={"path": created_dir_path})
        response.raise_for_status()
        data = response.json()
        if data['success']:
            print(f"   ✓ 测试目录清理成功: {created_dir_path}")
        else:
            print(f"   ⚠ 清理失败: {data.get('message', 'Unknown')}")
    except Exception as e:
        print(f"   ✗ 清理失败: {e}")
    
    print("\n文件管理器工作流程测试完成!")

if __name__ == "__main__":
    test_full_filemanager_workflow()