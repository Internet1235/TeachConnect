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

# 修复：优先使用 APPDATA，若为 None 则回退到 running_path（避免 Android 上的 None 导致 os.path.join 抛错）
base_appdata = os.getenv("APPDATA") or running_path
APP_DATA_PATH = os.path.join(base_appdata, "TConect")
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

# 注册支持中文的字体（使用运行目录下的字体文件，注册前检查文件是否存在）
try:
    font_path = os.path.join(running_path, "font", "MiSans-Heavy.ttf")
    if os.path.exists(font_path):
        LabelBase.register(name='Roboto', fn_regular=font_path)
    else:
        debug_log(f"字体文件未找到: {font_path}，将使用默认字体")
except Exception as e:
    debug_log(f"注册字体失败: {e}")

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
        self.name_spinner = Spinner(text="选择名称", values=[], size_hint=(1, None))  # 快捷选择
        self.name_input = TextInput(hint_text="或手动输入名称", multiline=False, size_hint=(1, None))  # 手动输入
        # 选择 spinner 时把完整名称填入手动输入框
        self.name_spinner.bind(text=self.on_name_selected)
        # 回车确认手动输入
        self.name_input.bind(on_text_validate=self.on_name_confirm)

        # IP 输入框：支持快捷选择和手动输入
        self.label_ip = Label(text="服务器 IP:", halign="left", size_hint=(1, None), height=30)  # 靠左对齐
        self.ip_spinner = Spinner(text="选择 IP", values=[], size_hint=(1, None))  # 快捷选择，显示为 "备注 - IP"
        self.ip_input = TextInput(hint_text="或手动输入 IP（可写入备注 - IP）", multiline=False, size_hint=(1, None))  # 手动输入
        # 选择 spinner 时把完整 "备注 - IP" 填入手动输入框
        self.ip_spinner.bind(text=self.on_ip_selected)
        # 回车确认手动输入
        self.ip_input.bind(on_text_validate=self.on_ip_confirm)

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

        # 设置默认值
        self.set_default_inputs()

        # 保存当前选中的带备注 IP（格式 "备注 - IP"），用于发送后恢复
        self.selected_ip = None

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
            # ip_spinner 的文本为 "备注 - IP"，直接填入 ip_input 保留备注格式（用户可编辑）
            self.ip_input.text = self.ip_spinner.text

    def on_name_selected(self, spinner, text):
        """当选择名称时，将值填入手动输入框"""
        self.name_input.text = text

    def on_ip_selected(self, spinner, text):
        """当选择 IP 时，将值填入手动输入框"""
        # Spinner 显示为 "备注 - IP"，直接填入编辑框，保留备注与 IP
        self.ip_input.text = text

    def on_name_confirm(self, instance):
        """处理名称输入框的确认事件"""
        text = self.name_input.text.strip()
        if text and text not in self.recent_names:
            self.recent_names[text] = True
            save_recent_data(NAME_STORAGE_FILE, self.recent_names)
            self.update_inputs()

    def on_ip_confirm(self, instance):
        """处理 IP 输入框的确认事件"""
        text = self.ip_input.text.strip()
        if text and text not in self.recent_ips:
            # 尝试分离备注和 IP（优先 "备注 - IP"）
            try:
                note, ip = text.split(" - ", 1)
                note = note.strip(); ip = ip.strip()
                self.recent_ips[ip] = note
            except ValueError:
                # 允许用户只输入 "备注-IP"（无空格）或只输入 IP；若含单短横线自动修正
                try:
                    note, ip = text.split("-", 1)
                    note = note.strip(); ip = ip.strip()
                    self.recent_ips[ip] = note
                    # 自动把编辑框标准化为 "备注 - IP"
                    self.ip_input.text = f"{note} - {ip}"
                except ValueError as e:
                    log_error(e)
                    try:
                        note, ip = text.split(" - ", 1)
                    except ValueError :
                        self.show_popup("错误", "IP 格式无效！")
                        return
            save_recent_data(IP_STORAGE_FILE, self.recent_ips)
            self.update_inputs()

    def send_message(self, instance):
        # 获取名称和 IP，优先使用手动输入的值
        name = self.name_input.text.strip() or (self.name_spinner.text.strip() if hasattr(self, 'name_spinner') else "")
        ip_with_note = self.ip_input.text.strip() or (self.ip_spinner.text.strip() if hasattr(self, 'ip_spinner') else "")
        message = self.message_input.text.strip()

        # 检查必要字段是否填写
        if not name or not ip_with_note or not message:
            self.show_popup("错误", "所有字段均为必填项！")
            return

        # 从 "备注 - IP" 格式中分离出备注和 IP
        try:
            note, ip = ip_with_note.split(" - ", 1)
        except ValueError as e:
                log_error(e)
                try:
            # 若用户输入为 "备注-IP"（无空格），尝试自动修正为 "备注 - IP"
                    note, ip = ip_with_note.split("-", 1)
                    self.ip_input.text = ip_with_note
                except ValueError:
                    self.show_popup("错误", "IP 格式无效！")
                    return

        # 保存当前选中的带备注字符串，后续恢复时使用
        self.selected_ip = ip_with_note

        # 保存最近使用的名称
        if name not in self.recent_names:
            self.recent_names[name] = True
            save_recent_data(NAME_STORAGE_FILE, self.recent_names)

        # 保存最近使用的 IP
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

        # 重新加载 IP 并保持之前选中的 IP
        self.recent_ips = load_recent_data(IP_STORAGE_FILE)
        self.update_inputs()

        # 恢复之前选中的 IP（直接写回文本框）
        if self.selected_ip:
            # ip_input 是 TextInput，直接恢复带备注的字符串
            self.ip_input.text = self.selected_ip

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
