import json
import os
import datetime
import socket
import hashlib
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.audio import SoundLoader
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from jnius import autoclass
from android.permissions import request_permissions, Permission


# 获取应用目录
if hasattr(App, 'get_running_app'):
    running_path = App.get_running_app().user_data_dir
else:
    running_path = os.path.dirname(os.path.abspath(__file__))

# 初始化调试模式
DEBUG_MODE = True

# 设置存储路径
APP_DATA_PATH = running_path
USER_DATA_PATH = os.path.join(APP_DATA_PATH, "User")
LOG_PATH = os.path.join(APP_DATA_PATH, "log")
CACHE_PATH = os.path.join(APP_DATA_PATH, "cache")

# 确保目录存在
for path in [USER_DATA_PATH, LOG_PATH, CACHE_PATH]:
    os.makedirs(path, exist_ok=True)

# 使用Kivy的JsonStore替代文件操作
ip_store = JsonStore(os.path.join(CACHE_PATH, 'IPs.json'))
name_store = JsonStore(os.path.join(CACHE_PATH, 'Names.json'))
user_store = JsonStore(os.path.join(USER_DATA_PATH, 'UserInfo.json'))

def debug_log(message):
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def log_error(message):
    debug_log(f"记录错误: {message}")
    log_file = os.path.join(LOG_PATH, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
    log_entry = f"[{datetime.datetime.now()}] ERROR: {message}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(log_entry)
    except:
        pass

def log_message(ip, name, message):
    log_file = os.path.join(LOG_PATH, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
    log_entry = f"[{datetime.datetime.now()}] IP: {ip}, Name: {name}, Message: {message}\n"
    debug_log(f"记录日志: {log_entry}")
    try:
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(log_entry)
    except:
        pass

def play_notification_sound():
    try:
        sound = SoundLoader.load(f'{running_path}/sound/sound.mp3')
        if sound:
            sound.play()
    except Exception as e:
        log_error(f"播放音频时发生错误: {e}")

class LoginScreen(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        # 标题
        title = Label(
            text='TeachConnect 登录',
            size_hint=(1, 0.2),
            font_size='24sp',
            bold=True
        )
        self.add_widget(title)
        
        # 表单容器
        form_layout = GridLayout(cols=2, spacing=10, size_hint=(1, 0.4))
        
        form_layout.add_widget(Label(text='用户名:', size_hint=(0.3, 1)))
        self.username_input = TextInput(
            multiline=False,
            size_hint=(0.7, 1),
            hint_text='输入用户名'
        )
        form_layout.add_widget(self.username_input)
        
        form_layout.add_widget(Label(text='密码:', size_hint=(0.3, 1)))
        self.password_input = TextInput(
            password=True,
            multiline=False,
            size_hint=(0.7, 1),
            hint_text='输入密码'
        )
        form_layout.add_widget(self.password_input)
        
        self.add_widget(form_layout)
        
        # 按钮容器
        button_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.2))
        
        self.login_button = Button(
            text='登录',
            size_hint=(0.5, 1),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.login_button.bind(on_press=self.check_credentials)
        
        self.register_button = Button(
            text='注册',
            size_hint=(0.5, 1),
            background_color=(0.3, 0.8, 0.3, 1)
        )
        self.register_button.bind(on_press=self.register_user)
        
        button_layout.add_widget(self.login_button)
        button_layout.add_widget(self.register_button)
        
        self.add_widget(button_layout)
        
        self.check_if_registered()

    def check_if_registered(self):
        """检查是否已有用户数据"""
        try:
            if user_store.exists('users'):
                self.register_button.text = '已注册'
        except:
            pass

    def check_credentials(self, instance):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        
        if not username or not password:
            self.show_popup('错误', '用户名和密码不能为空！')
            return
            
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        
        try:
            if user_store.exists('users'):
                users = user_store.get('users')
                if username in users and users[username] == password_hash:
                    self.app.current_user = username
                    self.app.show_messaging_screen()
                    return
                    
            self.show_popup('错误', '用户名或密码错误！')
            self.username_input.text = ''
            self.password_input.text = ''
        except Exception as e:
            self.show_popup('错误', f'登录时发生错误: {str(e)}')

    def register_user(self, instance):
        if self.register_button.text == '已注册':
            self.show_confirm_popup(
                '警告', 
                '已经注册过账户，确认继续注册？',
                self.do_register
            )
        else:
            self.do_register()

    def do_register(self):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()

        if not username or not password:
            self.show_popup('错误', '用户名和密码不能为空！')
            return

        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        try:
            if user_store.exists('users'):
                users = user_store.get('users')
            else:
                users = {}
                
            if username in users:
                self.show_popup('错误', '用户名已存在！')
            else:
                users[username] = password_hash
                user_store.put('users', **users)
                self.show_popup('成功', '注册成功！')
                self.register_button.text = '已注册'
        except Exception as e:
            self.show_popup('错误', f'注册时发生错误: {str(e)}')

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message))
        btn = Button(text='确定', size_hint=(1, 0.3))
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    def show_confirm_popup(self, title, message, callback):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message))
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.4))
        btn_yes = Button(text='是')
        btn_no = Button(text='否')
        
        def on_yes(instance):
            popup.dismiss()
            callback()
            
        def on_no(instance):
            popup.dismiss()
            import sys
            sys.exit()
            
        btn_yes.bind(on_press=on_yes)
        btn_no.bind(on_press=on_no)
        
        btn_layout.add_widget(btn_yes)
        btn_layout.add_widget(btn_no)
        
        content.add_widget(btn_layout)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        popup.open()

class MessagingScreen(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        # 标题
        title = Label(
            text='消息发送',
            size_hint=(1, 0.1),
            font_size='20sp',
            bold=True
        )
        self.add_widget(title)
        
        # 表单容器
        form_layout = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, 0.6))
        
        # 名称输入
        name_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.2))
        name_layout.add_widget(Label(text='名称:', size_hint=(0.3, 1)))
        self.name_input = Spinner(
            text='',
            size_hint=(0.7, 1),
            values=self.load_names()
        )
        name_layout.add_widget(self.name_input)
        form_layout.add_widget(name_layout)
        
        # IP输入
        ip_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.2))
        ip_layout.add_widget(Label(text='服务器 IP:', size_hint=(0.3, 1)))
        self.ip_input = Spinner(
            text='',
            size_hint=(0.7, 1),
            values=self.load_ips()
        )
        ip_layout.add_widget(self.ip_input)
        form_layout.add_widget(ip_layout)
        
        # 消息输入
        msg_layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.4))
        msg_layout.add_widget(Label(text='消息:', size_hint=(1, 0.2)))
        self.message_input = TextInput(
            multiline=True,
            size_hint=(1, 0.8),
            hint_text='输入要发送的消息'
        )
        msg_layout.add_widget(self.message_input)
        form_layout.add_widget(msg_layout)
        
        self.add_widget(form_layout)
        
        # 发送按钮
        self.send_button = Button(
            text='发送',
            size_hint=(1, 0.1),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.send_button.bind(on_press=self.send_message)
        self.add_widget(self.send_button)
        
        self.selected_ip = None

    def load_names(self):
        try:
            if name_store.exists('names'):
                names_data = name_store.get('names')
                return list(names_data.keys())
        except:
            pass
        return []

    def load_ips(self):
        ips = []
        try:
            if ip_store.exists('ips'):
                ips_data = ip_store.get('ips')
                for ip, note in ips_data.items():
                    ips.append(f"{note} - {ip}")
        except:
            pass
        return ips

    def send_message(self, instance):
        name = self.name_input.text.strip()
        ip_with_note = self.ip_input.text.strip()
        message = self.message_input.text.strip()

        # 检查必要字段是否填写
        if not name or not ip_with_note or not message:
            self.show_popup('错误', '请填写所有字段！')
            return

        # 从 "备注 - IP" 格式中分离出备注和 IP
        try:
            if " - " in ip_with_note:
                note, ip = ip_with_note.split(" - ", 1)
            else:
                note, ip = ip_with_note.split("-", 1)
        except ValueError:
            self.show_popup('错误', 'IP 格式无效！请使用"备注 - IP"格式')
            return

        # 保存当前选中的 IP
        self.selected_ip = ip_with_note

        # 保存最近使用的名称
        try:
            if name_store.exists('names'):
                names_data = name_store.get('names')
            else:
                names_data = {}
                
            if name not in names_data:
                names_data[name] = True
                name_store.put('names', **names_data)
                # 更新下拉列表
                self.name_input.values = self.load_names()
        except Exception as e:
            log_error(f"保存名称时错误: {e}")

        # 更新备注，并保存
        try:
            if ip_store.exists('ips'):
                ips_data = ip_store.get('ips')
            else:
                ips_data = {}
                
            ips_data[ip] = note  # 更新 IP 的备注
            ip_store.put('ips', **ips_data)
            # 更新下拉列表
            self.ip_input.values = self.load_ips()
        except Exception as e:
            log_error(f"保存IP时错误: {e}")

        # 记录日志
        log_message(ip, name, message)

        # 发送数据
        data = json.dumps({"name": name, "message": message})
        try:
            # 在Android上需要在后台线程执行网络操作
            def do_send():
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(10)  # 10秒超时
                        s.connect((ip, 11224))
                        s.sendall(data.encode("utf-8"))
                        
                        # 在主线程中播放声音和显示成功消息
                        Clock.schedule_once(lambda dt: self.send_success())
                except Exception as e:
                    # 在主线程中显示错误
                    Clock.schedule_once(lambda dt: self.send_error(str(e)))
            
            import threading
            thread = threading.Thread(target=do_send)
            thread.daemon = True
            thread.start()
            
            self.send_button.text = '发送中...'
            self.send_button.disabled = True
            
        except Exception as e:
            self.send_error(str(e))

    def send_success(self):
        play_notification_sound()
        self.show_popup('发送成功', '消息已成功发送\n由于纪律问题，目标计算机将在10秒后重新开启信息接收')
        self.send_button.text = '发送'
        self.send_button.disabled = False
        self.message_input.text = ''

    def send_error(self, error_msg):
        log_error(f"发送失败: {error_msg}")
        self.show_popup('发送失败', f'发送失败：请检查网络连接或目标教室未启动程序\n错误信息: {error_msg}')
        self.send_button.text = '发送'
        self.send_button.disabled = False

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=message))
        btn = Button(text='确定', size_hint=(1, 0.3))
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

class TeachConnectApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user = None
        
        # 检查升级提醒
        weekday = datetime.datetime.now().weekday()
        if weekday == 6:  # 周日
            self.show_upgrade_notification()

    def show_upgrade_notification(self):
        html_path = "https://www.github.com/pyTeachConnect/TeachConnect/releases"
        # 在Android上使用Toast显示通知
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Toast = autoclass('android.widget.Toast')
            String = autoclass('java.lang.String')
            
            context = PythonActivity.mActivity
            message = String(f"请将TeachConnect更新到最新版本！{html_path}")
            toast = Toast.makeText(context, message, Toast.LENGTH_LONG)
            toast.show()
        except:
            # 备用方案：使用弹出窗口
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            content.add_widget(Label(text=f"请将TeachConnect更新到最新版本！\n{html_path}"))
            btn = Button(text='确定', size_hint=(1, 0.3))
            popup = Popup(title='升级提醒', content=content, size_hint=(0.8, 0.4))
            btn.bind(on_press=popup.dismiss)
            content.add_widget(btn)
            popup.open()

    def build(self):
        self.login_screen = LoginScreen(self)
        return self.login_screen

    def show_messaging_screen(self):
        self.root.clear_widgets()
        self.messaging_screen = MessagingScreen(self)
        self.root.add_widget(self.messaging_screen)

if __name__ == '__main__':
    TeachConnectApp().run()
