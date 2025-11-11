from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.core.text import LabelBase
import os
import json
import hashlib
import socket
import datetime
from plyer import notification
# import pygame

running_path = os.path.dirname(os.path.abspath(__file__))
print(running_path)

weekday = datetime.datetime.now().weekday()

html_path = "https://www.github.com/pyTeachConnect/TeachConnect/releases"


def debug_log(message):
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def log_error(message):
    debug_log(f"记录错误: {message}")
    log_file = os.path.join(LOG_PATH, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
    log_entry = f"[{datetime.datetime.now()}] ERROR: {message}\n"
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(log_entry)


# 添加升级提醒通知
if weekday == 6:
    notification.notify(
        title="升级提醒",
        message=f"请将 TeachConnect 客户端更新到最新版本！GitHub仓库：{html_path}",
        timeout=5  # 通知显示的时长
    )

# 初始化 pygame 的混音器
#try:
#    pygame.mixer.init()
#except Exception as e:
#    log_error(f"初始化混音器失败: {e}")
#    notification.notify(
#        title="发生错误（非致命错误）",
#        message=f"播放音频时发生错误: {e}，尝试连接音频设备以解决错误",
#        timeout=5
#    )

# 播放提示音
#def play_notification_sound():
#    try:
#        sound = pygame.mixer.Sound(f'{running_path}\\sound\\sound.mp3')
#        sound.play()
#    except Exception as e:
#        log_error(f"播放音频时发生错误: {e}")

# 设置调试模式，True为启用调试，False为禁用
DEBUG_MODE = True

# 设置存储路径
APP_DATA_PATH = os.path.join(os.getenv("APPDATA"), "TConect")
USER_DATA_PATH = os.path.join(APP_DATA_PATH, "User")
LOG_PATH = os.path.join(APP_DATA_PATH, "log")
CACHE_PATH = os.path.join(APP_DATA_PATH, "cache")
IP_STORAGE_FILE = os.path.join(CACHE_PATH, "IPs.json")
NAME_STORAGE_FILE = os.path.join(CACHE_PATH, "Names.json")
USER_CREDENTIALS_FILE = os.path.join(USER_DATA_PATH, "UserInfo.json")

# 确保目录存在
for path in [USER_DATA_PATH, LOG_PATH, CACHE_PATH]:
    os.makedirs(path, exist_ok=True)


def load_recent_data(filepath):
    debug_log(f"加载文件: {filepath}")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            debug_log(f"加载成功: {data}")
            return data
    debug_log("文件不存在，返回空字典")
    return {}


def save_recent_data(filepath, data):
    debug_log(f"保存数据到 {filepath}，数据: {data}")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def log_message(ip, name, message):
    log_file = os.path.join(LOG_PATH, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
    log_entry = f"[{datetime.datetime.now()}] IP: {ip}, Name: {name}, Message: {message}\n"
    debug_log(f"记录日志: {log_entry}")
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(log_entry)

# 注册支持中文的字体

LabelBase.register(name='Roboto',fn_regular='./font/MiSans-Heavy.ttf')

class LoginScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.username_input = TextInput(hint_text="用户名", multiline=False)
        self.password_input = TextInput(hint_text="密码", multiline=False, password=True)
        self.login_button = Button(text="登录", on_press=self.check_credentials)
        self.register_button = Button(text="注册", on_press=self.register_user)

        self.add_widget(self.username_input)
        self.add_widget(self.password_input)
        self.add_widget(self.login_button)
        self.add_widget(self.register_button)

        # 检查是否已有用户数据
        self.check_if_registered()

    def check_if_registered(self):
        """检查是否已有用户数据"""
        if os.path.exists(USER_CREDENTIALS_FILE):
            users = load_recent_data(USER_CREDENTIALS_FILE)
            if users:  # 如果存在已注册的用户
                self.register_button.text = "已注册"  # 显示“已注册”文字

    def check_credentials(self, instance):
        users = load_recent_data(USER_CREDENTIALS_FILE)
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()

        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        if username in users and users[username] == password_hash:
            app = App.get_running_app()
            app.root.clear_widgets()
            app.root.add_widget(MessagingScreen(username))
        else:
            self.show_popup("错误", "用户名或密码错误！")
            self.username_input.text = ""
            self.password_input.text = ""

    def register_user(self, instance):
        users = load_recent_data(USER_CREDENTIALS_FILE)
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()

        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        if not username or not password:
            self.show_popup("错误", "用户名和密码不能为空！")
            return

        if username in users:
            self.show_popup("错误", "用户名已存在！")
        else:
            users[username] = password_hash
            save_recent_data(USER_CREDENTIALS_FILE, users)
            self.register_button.text = "已注册"  # 更新按钮文字
            self.show_popup("成功", "注册成功！")

    def show_popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message, font_name="Roboto"),
            size_hint=(None, None),
            size=(400, 200),
        )
        popup.open()

class MessagingScreen(BoxLayout):
    def __init__(self, username, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.username = username

        # 名称输入框：支持快捷选择和手动输入
        self.label_name = Label(text="名称:", halign="left", size_hint=(1, None), height=30)  # 靠左对齐
        self.name_spinner = Spinner(text="选择名称", values=[], size_hint=(1, 0.2))  # 快捷选择
        self.name_input = TextInput(hint_text="或手动输入名称", multiline=False)  # 手动输入

        # IP 输入框：支持快捷选择和手动输入
        self.label_ip = Label(text="服务器 IP:", halign="left", size_hint=(1, None), height=30)  # 靠左对齐
        self.ip_spinner = Spinner(text="选择 IP", values=[], size_hint=(1, 0.2))  # 快捷选择
        self.ip_input = TextInput(hint_text="或手动输入 IP", multiline=False)  # 手动输入

        # 消息输入框
        self.label_message = Label(text="消息:", halign="left", size_hint=(1, None), height=30)  # 靠左对齐
        self.message_input = TextInput(hint_text="输入消息", multiline=False)

        # 发送按钮
        self.send_button = Button(text="发送", on_press=self.send_message, font_name="Roboto")

        # 添加到布局
        self.add_widget(self.label_name)
        self.add_widget(self.name_spinner)
        self.add_widget(self.name_input)
        self.add_widget(self.label_ip)
        self.add_widget(self.ip_spinner)
        self.add_widget(self.ip_input)
        self.add_widget(self.label_message)
        self.add_widget(self.message_input)
        self.add_widget(self.send_button)

        # 加载最近使用的 IP 和名称
        self.recent_ips = load_recent_data(IP_STORAGE_FILE)
        self.recent_names = load_recent_data(NAME_STORAGE_FILE)

        # 更新输入框的值
        self.update_inputs()

        # 绑定 Spinner 的值变化事件
        self.name_spinner.bind(text=self.on_name_selected)
        self.ip_spinner.bind(text=self.on_ip_selected)

        # 设置默认值
        self.set_default_inputs()

    def update_inputs(self):
        """更新名称和IP输入框的值"""
        self.name_spinner.values = list(self.recent_names.keys())
        self.ip_spinner.values = [f"{note} - {ip}" for ip, note in self.recent_ips.items()]

    def set_default_inputs(self):
        """设置默认选择数据库列表的第一个内容"""
        if self.name_spinner.values:
            self.name_spinner.text = self.name_spinner.values[0]
            self.name_input.text = self.name_spinner.text
        if self.ip_spinner.values:
            self.ip_spinner.text = self.ip_spinner.values[0]
            try:
                note, ip = self.ip_spinner.text.split(" - ", 1)
                self.ip_input.text = ip
            except ValueError:
                self.ip_input.text = self.ip_spinner.text

    def on_name_selected(self, spinner, text):
        """当选择名称时，将值填入手动输入框"""
        self.name_input.text = text

    def on_ip_selected(self, spinner, text):
        """当选择 IP 时，将值填入手动输入框"""
        try:
            note, ip = text.split(" - ", 1)
            self.ip_input.text = ip
        except ValueError:
            self.ip_input.text = text  # 如果没有备注，直接使用 IP

    def send_message(self, instance):
        # 获取名称和 IP，优先使用手动输入的值
        name = self.name_input.text.strip() or self.name_spinner.text.strip()
        ip_with_note = self.ip_input.text.strip() or self.ip_spinner.text.strip()
        message = self.message_input.text.strip()

        # 检查必要字段是否填写
        if not name or not ip_with_note or not message:
            self.show_popup("错误", "所有字段均为必填项！")
            return

        # 从 "备注 - IP" 格式中分离出备注和 IP
        try:
            note, ip = ip_with_note.split(" - ", 1)
        except ValueError:
            ip = ip_with_note  # 如果没有备注，直接使用 IP
            note = "备注"

        # 保存最近使用的名称
        if name not in self.recent_names:
            self.recent_names[name] = True
            save_recent_data(NAME_STORAGE_FILE, self.recent_names)

        # 保存最近使用的 IP
        if ip not in self.recent_ips:
            self.recent_ips[ip] = note
            save_recent_data(IP_STORAGE_FILE, self.recent_ips)

        # 更新输入框的值
        self.update_inputs()

        # 记录日志
        log_message(ip, name, message)

        # 发送数据
        data = json.dumps({"name": name, "message": message})
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, 11224))
                s.sendall(data.encode("utf-8"))
#                play_notification_sound()
                self.show_popup(
                    "发送成功",
                    "消息已成功发送\n由于纪律问题，目标计算机将在10秒后重新开启信息接收，"
                )
        except Exception as e:
            log_error(f"发送失败: {e}")
            self.show_popup("发送失败", f"发送失败：请检查网络连接或目标教室未启动程序\n错误信息: {e}")

    def show_popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message, font_name="Roboto", size_hint_y=None),
            size_hint=(None, None),
            size=(500, 150),  # 调整提示框大小以避免文字溢出
        )
        popup.open()
class TeachConnectApp(App):
    def build(self):
        return LoginScreen()


if __name__ == "__main__":
    TeachConnectApp().run()
