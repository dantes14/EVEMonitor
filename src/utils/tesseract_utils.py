#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tesseract OCR 工具函数
"""

import os
import sys
import subprocess
import requests
import shutil
import tempfile
import zipfile
from pathlib import Path
from loguru import logger

def check_tesseract():
    """
    检查Tesseract是否已安装，如果未安装则询问用户是否自动安装
    
    返回值:
        bool: Tesseract是否可用
    """
    # 检查Tesseract是否可用
    try:
        import pytesseract
        
        # Windows平台需要手动设置tesseract_cmd
        if sys.platform == 'win32':
            # 检查环境变量
            tesseract_env = os.environ.get("TESSERACT_PATH", "")
            if tesseract_env and os.path.exists(tesseract_env):
                pytesseract.pytesseract.tesseract_cmd = tesseract_env
                return True
                
            # 检查默认安装路径
            default_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                os.path.join(os.path.expanduser("~"), 'AppData', 'Local', 'Tesseract-OCR', 'tesseract.exe')
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    return True
                    
            # 未找到Tesseract，询问用户是否自动安装
            logger.warning("未找到Tesseract OCR，需要安装才能继续使用")
            return False
            
        # 其他平台直接尝试使用tesseract命令
        try:
            subprocess.run(['tesseract', '--version'], check=True, capture_output=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("未找到Tesseract OCR，需要安装才能继续使用")
            return False
            
    except ImportError:
        logger.error("缺少pytesseract库，请先安装: pip install pytesseract")
        return False

def install_tesseract_windows(version="5.0.1"):
    """
    在Windows上自动安装Tesseract OCR
    
    参数:
        version: 版本号
        
    返回值:
        bool: 安装是否成功
    """
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        # 安装目录
        install_dir = os.path.join(os.path.expanduser("~"), 'AppData', 'Local', 'Tesseract-OCR')
        
        # 下载Tesseract安装包
        url = f"https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v{version}.exe"
        logger.info(f"正在下载Tesseract OCR安装包: {url}")
        
        # 下载文件
        installer_path = os.path.join(temp_dir, f"tesseract-{version}-installer.exe")
        response = requests.get(url, stream=True)
        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 提示用户安装
        logger.info("请按照安装向导完成Tesseract OCR的安装")
        logger.info("推荐安装到默认路径: C:\\Program Files\\Tesseract-OCR")
        logger.info("安装完成后，请重启程序")
        
        # 运行安装程序
        subprocess.run([installer_path], check=True)
        
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return True
    except Exception as e:
        logger.error(f"自动安装Tesseract OCR失败: {e}")
        return False

def download_language_data(lang="chi_sim"):
    """
    下载Tesseract语言数据
    
    参数:
        lang: 语言代码
        
    返回值:
        bool: 下载是否成功
    """
    try:
        # Windows平台需要特殊处理
        if sys.platform == 'win32':
            import pytesseract
            
            # 获取Tesseract安装路径
            tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
            if not tesseract_cmd or not os.path.exists(tesseract_cmd):
                logger.error("未找到Tesseract路径，无法下载语言数据")
                return False
                
            # 获取tessdata目录
            tessdata_dir = os.path.join(os.path.dirname(tesseract_cmd), "tessdata")
            if not os.path.exists(tessdata_dir):
                os.makedirs(tessdata_dir, exist_ok=True)
                
            # 下载语言数据
            url = f"https://github.com/tesseract-ocr/tessdata/raw/main/{lang}.traineddata"
            logger.info(f"正在下载{lang}语言数据: {url}")
            
            # 下载文件
            traineddata_path = os.path.join(tessdata_dir, f"{lang}.traineddata")
            response = requests.get(url, stream=True)
            with open(traineddata_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"语言数据下载完成: {traineddata_path}")
            return True
            
        else:
            logger.info(f"请使用系统包管理器安装Tesseract {lang}语言数据")
            return False
            
    except Exception as e:
        logger.error(f"下载语言数据失败: {e}")
        return False

if __name__ == "__main__":
    # 测试代码
    if check_tesseract():
        print("Tesseract已安装")
    else:
        print("Tesseract未安装")
        if sys.platform == 'win32' and input("是否自动安装Tesseract? (y/n): ").lower() == 'y':
            install_tesseract_windows() 