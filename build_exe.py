#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本 - 使用PyInstaller打包番茄计时器
"""

import os
import sys
import subprocess

def check_pyinstaller():
    """检查PyInstaller是否已安装"""
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller 安装成功")
            return True
        except subprocess.CalledProcessError:
            print("✗ PyInstaller 安装失败，请手动运行: pip install pyinstaller")
            return False

def clean_build_files():
    """清理旧的打包文件"""
    print("\n清理旧的打包文件...")
    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = ['*.spec']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            import shutil
            shutil.rmtree(dir_name)
            print(f"  已删除: {dir_name}/")
    
    import glob
    for spec_file in glob.glob('*.spec'):
        os.remove(spec_file)
        print(f"  已删除: {spec_file}")

def build_exe():
    """执行打包"""
    print("\n开始打包程序...")
    print("这可能需要几分钟时间，请耐心等待...\n")
    
    # PyInstaller命令
    cmd = [
        'pyinstaller',
        '--name=番茄计时器',
        '--onefile',  # 打包成单个exe文件
        '--windowed',  # 不显示控制台窗口
        '--clean',  # 清理临时文件
        '--noconfirm',  # 覆盖输出目录而不询问
        # 隐藏导入（确保所有依赖都被包含）
        '--hidden-import=win32timezone',
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32gui',
        '--collect-all=win10toast',  # 收集win10toast的所有数据文件
        # 主程序文件
        'pomodoro_timer.py'
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "="*50)
        print("✓ 打包成功！")
        print("="*50)
        print(f"\n可执行文件位置: {os.path.abspath('dist/番茄计时器.exe')}")
        print("\n你可以将 dist/番茄计时器.exe 复制到任何Windows电脑上使用")
        print("不需要安装Python环境！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 打包失败: {e}")
        return False
    except FileNotFoundError:
        print("\n✗ 找不到PyInstaller，请先安装: pip install pyinstaller")
        return False

def main():
    print("="*50)
    print("番茄计时器 - 打包程序")
    print("="*50)
    
    # 检查PyInstaller
    if not check_pyinstaller():
        input("\n按回车键退出...")
        return
    
    # 清理旧文件
    clean_build_files()
    
    # 执行打包
    if build_exe():
        print("\n打包完成！")
    else:
        print("\n打包失败，请检查错误信息。")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()

