#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端JavaScript可能遇到的JSON解析错误
"""
import requests
import json

def test_json_parsing_simulation():
    """模拟前端JavaScript的JSON解析行为"""
    base_url = "http://127.0.0.1:9001"
    
    print("模拟前端JavaScript的JSON解析行为...")
    
    # 测试各种API端点，模拟JavaScript fetch().then(response => response.json())
    test_endpoints = [
        '/api/system',
        '/api/files/list',
        '/api/files/info',
        '/api/files/read',
        '/api/files/write',
        '/api/files/upload',
        '/api/files/download?path=test',
        '/api/files/create_dir',
        '/api/files/delete',
        '/api/files/rename',
        '/api/files/stats',
    ]
    
    for endpoint in test_endpoints:
        try:
            # 构造完整URL，对于POST请求使用GET来测试错误情况
            if 'write' in endpoint or 'upload' in endpoint or 'create_dir' in endpoint or 'delete' in endpoint or 'rename' in endpoint:
                # 对于POST端点，发送GET会收到错误响应
                url = base_url + endpoint
            elif endpoint == '/api/files/info' or endpoint == '/api/files/read' or endpoint == '/api/files/download?path=test':
                # 这些端点需要参数，不提供参数会收到错误响应
                url = base_url + endpoint
            else:
                url = base_url + endpoint
            
            print(f"测试端点: {url}")
            
            response = requests.get(url)
            
            # 模拟JavaScript中的 response.json() 调用
            try:
                data = response.json()
                print(f"  ✓ 成功解析JSON: {type(data)}")
                if isinstance(data, dict) and 'success' in data:
                    print(f"    success字段: {data['success']}")
            except json.JSONDecodeError as e:
                print(f"  ✗ JSON解析失败: {e}")
                print(f"    响应内容预览: {response.text[:200]}...")
                if response.text.strip().startswith('<!'):
                    print(f"    错误: 响应是HTML而不是JSON!")
                    
        except Exception as e:
            print(f"  ✗ 请求失败: {e}")
        
        print()

if __name__ == "__main__":
    test_json_parsing_simulation()