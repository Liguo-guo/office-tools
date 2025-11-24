#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
番茄计时器 - 桌面应用
支持定制化壁纸功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import threading
import os
import sys
import json
from PIL import Image, ImageTk
import ctypes
from ctypes import wintypes
import winsound
from win10toast import ToastNotifier

# Windows API 用于设置壁纸
SPI_SETDESKWALLPAPER = 0x0014
SPI_GETDESKWALLPAPER = 0x0073
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDWININICHANGE = 0x02
MAX_PATH = 260

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("番茄计时器")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        
        # 计时器状态
        self.is_running = False
        self.is_paused = False
        self.current_time = 25 * 60  # 默认25分钟（秒）
        self.mode = "work"  # work, short_break, long_break
        self.pomodoro_count = 0  # 完成的番茄数
        
        # 时间设置（秒）
        self.work_time = 25 * 60
        self.short_break_time = 5 * 60
        self.long_break_time = 15 * 60
        
        # 壁纸设置
        self.wallpaper_path = None
        self.original_wallpaper = None
        
        # 铃声设置
        self.ringtone_path = None
        
        self.config_file = "pomodoro_config.json"
        
        # 加载配置
        self.load_config()
        
        # 保存原始壁纸
        self.save_original_wallpaper()
        
        # 系统托盘
        self.setup_tray()
        
        # 通知器
        self.toast = ToastNotifier()
        
        # 创建UI
        self.create_ui()
        
        # 更新显示
        self.update_display()
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🍅 番茄计时器", font=("Arial", 24, "bold"))
        title_label.pack(pady=10)
        
        # 模式显示
        self.mode_label = ttk.Label(main_frame, text="工作模式", font=("Arial", 16))
        self.mode_label.pack(pady=5)
        
        # 时间显示
        self.time_label = ttk.Label(main_frame, text="25:00", font=("Arial", 48, "bold"))
        self.time_label.pack(pady=20)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, length=300, mode='determinate')
        self.progress_bar.pack(pady=10)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        # 控制按钮
        self.start_button = ttk.Button(button_frame, text="开始", command=self.start_timer, width=10)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = ttk.Button(button_frame, text="暂停", command=self.pause_timer, 
                                       width=10, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = ttk.Button(button_frame, text="重置", command=self.reset_timer, width=10)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        # 模式选择框架
        mode_frame = ttk.LabelFrame(main_frame, text="模式选择", padding="10")
        mode_frame.pack(pady=10, fill=tk.X)
        
        mode_button_frame = ttk.Frame(mode_frame)
        mode_button_frame.pack()
        
        ttk.Button(mode_button_frame, text="工作 (25分钟)", 
                  command=lambda: self.set_mode("work")).pack(side=tk.LEFT, padx=5)
        ttk.Button(mode_button_frame, text="短休息 (5分钟)", 
                  command=lambda: self.set_mode("short_break")).pack(side=tk.LEFT, padx=5)
        ttk.Button(mode_button_frame, text="长休息 (15分钟)", 
                  command=lambda: self.set_mode("long_break")).pack(side=tk.LEFT, padx=5)
        
        # 统计信息
        stats_frame = ttk.LabelFrame(main_frame, text="统计", padding="10")
        stats_frame.pack(pady=10, fill=tk.X)
        
        self.stats_label = ttk.Label(stats_frame, text="今日完成: 0 个番茄", font=("Arial", 12))
        self.stats_label.pack()
        
        # 壁纸设置框架
        wallpaper_frame = ttk.LabelFrame(main_frame, text="壁纸设置", padding="10")
        wallpaper_frame.pack(pady=10, fill=tk.X)
        
        wallpaper_button_frame = ttk.Frame(wallpaper_frame)
        wallpaper_button_frame.pack()
        
        ttk.Button(wallpaper_button_frame, text="选择壁纸", 
                  command=self.select_wallpaper).pack(side=tk.LEFT, padx=5)
        ttk.Button(wallpaper_button_frame, text="应用壁纸", 
                  command=self.apply_wallpaper).pack(side=tk.LEFT, padx=5)
        ttk.Button(wallpaper_button_frame, text="恢复默认", 
                  command=self.restore_wallpaper).pack(side=tk.LEFT, padx=5)
        
        self.wallpaper_label = ttk.Label(wallpaper_frame, text="未选择壁纸", 
                                         font=("Arial", 9), foreground="gray")
        self.wallpaper_label.pack(pady=5)
        
        # 铃声设置框架
        ringtone_frame = ttk.LabelFrame(main_frame, text="铃声设置", padding="10")
        ringtone_frame.pack(pady=10, fill=tk.X)
        
        ringtone_button_frame = ttk.Frame(ringtone_frame)
        ringtone_button_frame.pack()
        
        ttk.Button(ringtone_button_frame, text="选择铃声", 
                  command=self.select_ringtone).pack(side=tk.LEFT, padx=5)
        ttk.Button(ringtone_button_frame, text="测试铃声", 
                  command=self.test_ringtone).pack(side=tk.LEFT, padx=5)
        ttk.Button(ringtone_button_frame, text="使用系统提示音", 
                  command=self.use_system_sound).pack(side=tk.LEFT, padx=5)
        
        self.ringtone_label = ttk.Label(ringtone_frame, text="使用系统提示音", 
                                        font=("Arial", 9), foreground="gray")
        self.ringtone_label.pack(pady=5)
        
    def update_display(self):
        """更新显示"""
        minutes = self.current_time // 60
        seconds = self.current_time % 60
        self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        
        # 更新进度条
        if self.mode == "work":
            max_time = self.work_time
            mode_text = "工作模式"
        elif self.mode == "short_break":
            max_time = self.short_break_time
            mode_text = "短休息"
        else:
            max_time = self.long_break_time
            mode_text = "长休息"
        
        progress = ((max_time - self.current_time) / max_time) * 100
        self.progress_var.set(progress)
        self.mode_label.config(text=mode_text)
        
        # 更新统计
        self.stats_label.config(text=f"今日完成: {self.pomodoro_count} 个番茄")
        
    def start_timer(self):
        """开始计时"""
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.DISABLED)
            self.timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
            self.timer_thread.start()
    
    def pause_timer(self):
        """暂停计时"""
        if self.is_running:
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.pause_button.config(text="继续")
            else:
                self.pause_button.config(text="暂停")
    
    def reset_timer(self):
        """重置计时"""
        self.is_running = False
        self.is_paused = False
        self.set_mode(self.mode)  # 重新设置当前模式的时间
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="暂停")
        self.reset_button.config(state=tk.NORMAL)
    
    def set_mode(self, mode):
        """设置模式"""
        if not self.is_running:
            self.mode = mode
            if mode == "work":
                self.current_time = self.work_time
            elif mode == "short_break":
                self.current_time = self.short_break_time
            else:
                self.current_time = self.long_break_time
            self.update_display()
    
    def timer_loop(self):
        """计时器循环"""
        while self.is_running and self.current_time > 0:
            if not self.is_paused:
                time.sleep(1)
                self.current_time -= 1
                self.root.after(0, self.update_display)
                
                # 最后10秒提示音
                if self.current_time == 10:
                    self.play_sound("warning")
        
        # 时间到
        if self.current_time == 0:
            self.root.after(0, self.timer_finished)
    
    def timer_finished(self):
        """计时结束"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="暂停")
        self.reset_button.config(state=tk.NORMAL)
        
        # 播放提示音
        self.play_sound("finish")
        
        # 显示通知
        if self.mode == "work":
            self.pomodoro_count += 1
            message = f"工作完成！\n已完成 {self.pomodoro_count} 个番茄\n休息一下吧！"
            # 自动切换到短休息
            if self.pomodoro_count % 4 == 0:
                self.set_mode("long_break")
            else:
                self.set_mode("short_break")
        else:
            message = "休息结束！\n准备开始工作吧！"
            self.set_mode("work")
        
        # 显示消息框和通知
        messagebox.showinfo("时间到！", message)
        self.show_notification("番茄计时器", message)
        
        # 如果设置了壁纸，在休息时应用
        if self.mode in ["short_break", "long_break"] and self.wallpaper_path:
            self.apply_wallpaper()
        elif self.mode == "work" and self.wallpaper_path:
            self.restore_wallpaper()
        
        # 保存配置
        self.save_config()
        self.update_display()
    
    def select_wallpaper(self):
        """选择壁纸文件"""
        file_path = filedialog.askopenfilename(
            title="选择壁纸图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.wallpaper_path = file_path
            filename = os.path.basename(file_path)
            self.wallpaper_label.config(text=f"已选择: {filename}", foreground="green")
            self.save_config()
    
    def apply_wallpaper(self):
        """应用壁纸"""
        if not self.wallpaper_path:
            messagebox.showwarning("警告", "请先选择壁纸图片！")
            return
        
        if not os.path.exists(self.wallpaper_path):
            messagebox.showerror("错误", "壁纸文件不存在！")
            return
        
        try:
            # 使用Windows API设置壁纸
            user32 = ctypes.windll.user32
            result = user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER,
                0,
                self.wallpaper_path,
                SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
            )
            
            if result:
                messagebox.showinfo("成功", "壁纸已应用！")
                self.save_config()
            else:
                messagebox.showerror("错误", "壁纸应用失败！")
        except Exception as e:
            messagebox.showerror("错误", f"应用壁纸时出错：{str(e)}")
    
    def save_original_wallpaper(self):
        """保存原始壁纸路径"""
        try:
            user32 = ctypes.windll.user32
            wallpaper = ctypes.create_unicode_buffer(MAX_PATH)
            user32.SystemParametersInfoW(
                SPI_GETDESKWALLPAPER,
                MAX_PATH,
                wallpaper,
                0
            )
            self.original_wallpaper = wallpaper.value
        except Exception as e:
            print(f"保存原始壁纸失败：{str(e)}")
    
    def restore_wallpaper(self):
        """恢复原始壁纸"""
        if not self.original_wallpaper:
            messagebox.showwarning("警告", "未找到原始壁纸路径！")
            return
        
        try:
            user32 = ctypes.windll.user32
            result = user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER,
                0,
                self.original_wallpaper,
                SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
            )
            
            if result:
                messagebox.showinfo("成功", "壁纸已恢复！")
            else:
                messagebox.showerror("错误", "壁纸恢复失败！")
        except Exception as e:
            messagebox.showerror("错误", f"恢复壁纸时出错：{str(e)}")
    
    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.wallpaper_path = config.get('wallpaper_path')
                    self.ringtone_path = config.get('ringtone_path')
                    self.pomodoro_count = config.get('pomodoro_count', 0)
                    # 更新铃声标签
                    if self.ringtone_path:
                        filename = os.path.basename(self.ringtone_path)
                        self.ringtone_label.config(text=f"已选择: {filename}", foreground="green")
            except Exception as e:
                print(f"加载配置失败：{str(e)}")
    
    def save_config(self):
        """保存配置"""
        try:
            config = {
                'wallpaper_path': self.wallpaper_path,
                'ringtone_path': self.ringtone_path,
                'pomodoro_count': self.pomodoro_count
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败：{str(e)}")
    
    def setup_tray(self):
        """设置系统托盘（简化版，使用最小化到任务栏）"""
        pass  # Tkinter原生不支持系统托盘，可以使用pystray库，这里简化处理
    
    def show_notification(self, title, message):
        """显示桌面通知"""
        try:
            self.toast.show_toast(
                title,
                message,
                duration=5,
                threaded=True
            )
        except Exception as e:
            print(f"通知显示失败：{str(e)}")
    
    def select_ringtone(self):
        """选择铃声文件"""
        file_path = filedialog.askopenfilename(
            title="选择铃声文件",
            filetypes=[
                ("音频文件", "*.wav *.mp3"),
                ("WAV文件", "*.wav"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.ringtone_path = file_path
            filename = os.path.basename(file_path)
            self.ringtone_label.config(text=f"已选择: {filename}", foreground="green")
            self.save_config()
    
    def test_ringtone(self):
        """测试铃声"""
        self.play_sound("finish")
    
    def use_system_sound(self):
        """使用系统提示音"""
        self.ringtone_path = None
        self.ringtone_label.config(text="使用系统提示音", foreground="gray")
        self.save_config()
        # 播放测试音
        winsound.Beep(800, 300)
    
    def play_sound(self, sound_type="finish"):
        """播放声音
        sound_type: 'finish' 计时结束, 'warning' 警告提示
        """
        if self.ringtone_path and os.path.exists(self.ringtone_path):
            try:
                # 播放自定义铃声文件
                if sound_type == "finish":
                    # 计时结束时播放3次
                    for _ in range(3):
                        winsound.PlaySound(self.ringtone_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                        time.sleep(0.5)
                else:
                    # 警告提示播放1次
                    winsound.PlaySound(self.ringtone_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                print(f"播放铃声失败：{str(e)}，使用系统提示音")
                self._play_system_sound(sound_type)
        else:
            # 使用系统提示音
            self._play_system_sound(sound_type)
    
    def _play_system_sound(self, sound_type="finish"):
        """播放系统提示音"""
        if sound_type == "finish":
            # 计时结束：播放3次提示音
            for _ in range(3):
                winsound.Beep(800, 300)
                time.sleep(0.2)
        else:
            # 警告提示：播放1次提示音
            winsound.Beep(1000, 200)
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.is_running:
            if messagebox.askokcancel("退出", "计时器正在运行，确定要退出吗？"):
                self.is_running = False
                self.save_config()
                self.root.destroy()
        else:
            self.save_config()
            self.root.destroy()

def main():
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()

if __name__ == "__main__":
    main()

