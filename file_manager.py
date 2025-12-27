#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理模块
"""
import os
import shutil
import mimetypes
from datetime import datetime
from pathlib import Path

class FileManager:
    def __init__(self, base_path="/"):
        self.base_path = Path(base_path).resolve()
        
    def _safe_path(self, path):
        """确保路径在安全范围内"""
        try:
            full_path = self.base_path / path
            full_path = full_path.resolve()
            
            # 检查路径是否在基础路径内
            if str(full_path).startswith(str(self.base_path)):
                return full_path
            else:
                return None
        except:
            return None
    
    def list_directory(self, path=""):
        """列出目录内容"""
        safe_path = self._safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "路径不存在或无权访问"}
        
        if not safe_path.is_dir():
            return {"success": False, "message": "不是目录"}
        
        try:
            items = []
            for item in safe_path.iterdir():
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item.relative_to(self.base_path)),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "permissions": oct(stat.st_mode)[-3:]
                })
            
            # 按类型和名称排序（目录在前，然后按名称）
            items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            
            return {
                "success": True,
                "items": items,
                "current_path": str(safe_path.relative_to(self.base_path)),
                "parent_path": str(safe_path.parent.relative_to(self.base_path)) if safe_path.parent != self.base_path else None
            }
            
        except Exception as e:
            return {"success": False, "message": f"读取目录失败: {str(e)}"}
    
    def get_file_info(self, path):
        """获取文件信息"""
        safe_path = self._safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "文件不存在或无权访问"}
        
        try:
            stat = safe_path.stat()
            return {
                "success": True,
                "name": safe_path.name,
                "path": str(safe_path.relative_to(self.base_path)),
                "type": "directory" if safe_path.is_dir() else "file",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                "created": datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                "permissions": oct(stat.st_mode)[-3:],
                "mime_type": mimetypes.guess_type(str(safe_path))[0] if safe_path.is_file() else None
            }
        except Exception as e:
            return {"success": False, "message": f"获取文件信息失败: {str(e)}"}
    
    def create_directory(self, path, name):
        """创建目录"""
        safe_path = self._safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "路径不存在"}
        
        try:
            new_dir = safe_path / name
            if new_dir.exists():
                return {"success": False, "message": "目录已存在"}
            
            new_dir.mkdir()
            return {"success": True, "message": "目录创建成功"}
        except Exception as e:
            return {"success": False, "message": f"创建目录失败: {str(e)}"}
    
    def delete_item(self, path):
        """删除文件或目录"""
        safe_path = self._safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "文件或目录不存在"}
        
        try:
            if safe_path.is_dir():
                shutil.rmtree(safe_path)
            else:
                safe_path.unlink()
            return {"success": True, "message": "删除成功"}
        except Exception as e:
            return {"success": False, "message": f"删除失败: {str(e)}"}
    
    def rename_item(self, path, new_name):
        """重命名文件或目录"""
        safe_path = self._safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "文件或目录不存在"}
        
        try:
            new_path = safe_path.parent / new_name
            if new_path.exists():
                return {"success": False, "message": "目标名称已存在"}
            
            safe_path.rename(new_path)
            return {"success": True, "message": "重命名成功"}
        except Exception as e:
            return {"success": False, "message": f"重命名失败: {str(e)}"}
    
    def get_directory_stats(self, path=""):
        """获取目录统计信息"""
        safe_path = self._safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "路径不存在"}
        
        try:
            file_count = 0
            total_size = 0
            
            if safe_path.is_file():
                file_count = 1
                total_size = safe_path.stat().st_size
            else:
                for item in safe_path.rglob('*'):
                    if item.is_file():
                        file_count += 1
                        total_size += item.stat().st_size
            
            # 格式化大小
            def format_size(size):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if size < 1024.0:
                        return f"{size:.2f} {unit}"
                    size /= 1024.0
                return f"{size:.2f} PB"
            
            return {
                "success": True,
                "path": str(safe_path.relative_to(self.base_path)),
                "file_count": file_count,
                "size": format_size(total_size),
                "size_bytes": total_size
            }
            
        except Exception as e:
            return {"success": False, "message": f"获取统计信息失败: {str(e)}"}

# 创建文件管理器实例
file_manager = FileManager()