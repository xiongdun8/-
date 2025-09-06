"""
使用前须知：
该模块是基于kivy库开发的移动端图像化程序
你可能需要执行kivy库安装命令才能正常运行
字体文件为更纱黑体（等距简体字体），该字体可能需要商用许可
如需使用AI解析功能，请更改deepseek APIkey的值，约在代码行第661行处
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.config import Config
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase, DEFAULT_FONT
import webbrowser
import os
import time
import socket  # 新增加网络检查需要的模块
from datetime import datetime
import main  # 导入后端模块
import ai_main  # 导入AI调用模块

# 字体设置
try:
    font_path = os.path.join(os.path.dirname(__file__), 'sarasa-mono-sc-semibolditalic.ttf')
    if os.path.exists(font_path):
        LabelBase.register(DEFAULT_FONT, font_path)
        print(f"成功加载字体: {font_path}")
    else:
        print(f"警告: 未找到字体文件 {font_path}，将使用默认字体")
except Exception as e:
    print(f"字体加载错误: {e}")

# 配置窗口
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')


# 自定义带圆角的按钮 - 解决移动端点击触发异常问题
class RoundedButton(Button):
    def __init__(self, **kwargs):
        super(RoundedButton, self).__init__(** kwargs)
        self.background_normal = ''
        self.normal_color = (0.2, 0.6, 0.8, 1)  # 正常状态颜色
        self.pressed_color = (0.1, 0.4, 0.6, 1)  # 按下状态颜色
        self.background_color = self.normal_color  # 默认使用正常颜色
        self.color = (1, 1, 1, 1)
        self.font_size = dp(16)
        self.size_hint_y = None
        self.height = dp(50)
        self.bind(pos=self.update_rect, size=self.update_rect)
        self.touch_down_time = 0  # 触摸按下时间记录
        self.min_click_interval = 0.05  # 最小点击间隔(秒)
        self.is_pressed = False  # 按钮按压状态标记

    def update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # 使用当前背景颜色（根据按压状态变化）
            Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_down_time = time.time()
            self.is_pressed = True
            self.background_color = self.pressed_color  # 切换到按下颜色
            self.update_rect()  # 更新显示
            return True  # 消耗触摸事件，防止穿透
        return super(RoundedButton, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self.is_pressed:
            # 检查触摸时间间隔
            elapsed = time.time() - self.touch_down_time
            self.is_pressed = False
            self.background_color = self.normal_color  # 恢复正常颜色
            self.update_rect()  # 更新显示

            if elapsed >= self.min_click_interval:
                # 触发按钮事件
                self.dispatch('on_press')
                self.dispatch('on_release')
            return True  # 消耗触摸事件
        return super(RoundedButton, self).on_touch_up(touch)

# 自定义标题标签
class TitleLabel(Label):
    def __init__(self, **kwargs):
        self.bg_color = kwargs.pop('bg_color', (0, 0, 0, 0))
        super(TitleLabel, self).__init__(**kwargs)
        self.font_size = dp(20)
        self.color = (0, 0, 0, 1)  # 标题文字为黑色
        self.size_hint_y = None
        self.height = dp(60)
        self.halign = 'center'
        self.valign = 'middle'
        self.bind(width=self.update_text_size, pos=self.update_bg, size=self.update_bg)
        self.update_bg()

    def update_text_size(self, instance, value):
        self.text_size = (value * 0.9, None)

    def update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            Rectangle(pos=self.pos, size=self.size)


# 自定义内容标签
class ContentLabel(Label):
    def __init__(self, is_scrollable=False, **kwargs):
        self.bg_color = kwargs.pop('bg_color', (0, 0, 0, 0))
        super(ContentLabel, self).__init__(**kwargs)
        self.font_size = dp(14)
        self.color = (0, 0, 0, 1)
        self.valign = 'top'
        self.bind(pos=self.update_bg, size=self.update_bg)
        self.update_bg()

        if not is_scrollable:
            self.size_hint_x = 1
            self.halign = 'center'
            self.size_hint_y = None
            self.bind(width=self.update_text_size, text=self.update_height)
        else:
            self.size_hint = (None, None)
            self.halign = 'left'
            self.bind(text=self.update_texture, width=self.update_texture)

    def update_text_size(self, instance, value):
        self.text_size = (value * 0.9, None)
        self.texture_update()

    def update_height(self, instance, value):
        self.texture_update()
        self.height = self.texture_size[1] + dp(10)

    def update_texture(self, instance, value):
        self.texture_update()
        if hasattr(self, 'texture_size'):
            self.height = self.texture_size[1] + dp(10)
            if instance == self and hasattr(value, 'texture_size'):
                self.width = max(Window.width * 0.9, value.texture_size[0])

    def update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            Rectangle(pos=self.pos, size=self.size)


# 支持滚动的容器
class ScrollableContainer(BoxLayout):
    def __init__(self, **kwargs):
        super(ScrollableContainer, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.bind(minimum_width=self.setter('width'),
                  minimum_height=self.setter('height'))


# 带背景图的基础布局
class BackgroundLayout(RelativeLayout):
    def __init__(self, **kwargs):
        super(BackgroundLayout, self).__init__(**kwargs)
        self.bg_image = Image(
            source='beijin.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1)
        )
        self.add_widget(self.bg_image)
        Window.bind(size=self._adjust_background)
        self._adjust_background(None, Window.size)

    def _adjust_background(self, instance, size):
        self.bg_image.size = size
        self.bg_image.pos = (0, 0)


# 首页
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        layout = BackgroundLayout()

        content_layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint=(1, 1)
        )

        content_layout.add_widget(TitleLabel(text="六爻排盘工具"))
        content_layout.add_widget(ContentLabel(
            text="欢迎使用六爻排盘工具，请选择下方功能开始使用",
            size_hint_y=None,
            height=dp(80)
        ))
        content_layout.add_widget(Label(size_hint_y=1, color=(0, 0, 0, 0)))

        layout.add_widget(content_layout)

        nav_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            pos_hint={'bottom': 0}
        )

        divination_btn = RoundedButton(text="算卦")
        divination_btn.bind(on_press=self.go_to_divination)
        nav_layout.add_widget(divination_btn)

        query_btn = RoundedButton(text="查询", background_color=(0.3, 0.7, 0.5, 1))
        query_btn.bind(on_press=self.open_baidu)
        nav_layout.add_widget(query_btn)

        layout.add_widget(nav_layout)
        self.add_widget(layout)

    def go_to_divination(self, instance):
        self.manager.current = 'reason'

    def open_baidu(self, instance):
        webbrowser.open('http://zy.kvov.com/index.php')  #64卦详解网站，对应主页的查询按键，可自行修改


# 输入起卦原因的屏幕
class ReasonScreen(Screen):
    def __init__(self, **kwargs):
        super(ReasonScreen, self).__init__(**kwargs)
        layout = BackgroundLayout()

        content_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        content_layout.add_widget(TitleLabel(text="六爻排盘"))
        content_layout.add_widget(ContentLabel(text="请输入起卦原因："))

        self.reason_input = TextInput(
            hint_text="例如：问事业发展",
            size_hint_y=None,
            height=dp(100),
            font_size=dp(16),
            multiline=True,
            padding=[dp(10), dp(10)],
            input_type='text',
            background_color=(1, 1, 1, 0.9)
        )
        content_layout.add_widget(self.reason_input)

        next_btn = RoundedButton(text="继续")
        next_btn.bind(on_press=self.go_to_hexagram_input)
        content_layout.add_widget(next_btn)
        content_layout.add_widget(Label(size_hint_y=1, color=(0, 0, 0, 0)))

        layout.add_widget(content_layout)
        self.add_widget(layout)

        #Clock.schedule_once(lambda dt: setattr(self.reason_input, 'focus', True), 0.5)

    def go_to_hexagram_input(self, instance):
        reason = self.reason_input.text.strip() or "未说明原因"
        self.manager.reason = reason
        self.manager.current = 'hexagram_input'


# 输入卦象的屏幕
class HexagramInputScreen(Screen):
    def __init__(self, **kwargs):
        super(HexagramInputScreen, self).__init__(**kwargs)
        self.hexagram = []

        layout = BackgroundLayout()

        content_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        content_layout.add_widget(TitleLabel(text="输入卦象"))
        content_layout.add_widget(ContentLabel(
            text="请输入6爻（从初爻到上爻）（普通硬币面额面【正面】为阳）：\n1=少阴（两正一反），2=少阳（两反一正）\n3=纯阳（动爻），4=纯阴（动爻）"
        ))

        self.hexagram_display = ContentLabel(text="已选：[]", bg_color=(1, 1, 1, 0.7))
        content_layout.add_widget(self.hexagram_display)

        button_grid = GridLayout(cols=4, spacing=dp(10), size_hint_y=None)
        button_grid.bind(minimum_height=button_grid.setter('height'))
        for i in range(1, 5):
            btn = RoundedButton(text=str(i))
            btn.bind(on_press=lambda instance, value=i: self.add_hexagram_value(value))
            button_grid.add_widget(btn)
        content_layout.add_widget(button_grid)

        clear_btn = RoundedButton(text="清除", background_color=(0.8, 0.3, 0.3, 1))
        clear_btn.bind(on_press=self.clear_hexagram)
        content_layout.add_widget(clear_btn)

        self.next_btn = RoundedButton(text="下一步")
        self.next_btn.bind(on_press=self.go_to_time_selection)
        self.next_btn.disabled = True
        content_layout.add_widget(self.next_btn)
        content_layout.add_widget(Label(size_hint_y=1, color=(0, 0, 0, 0)))

        layout.add_widget(content_layout)
        self.add_widget(layout)

    def add_hexagram_value(self, value):
        if len(self.hexagram) < 6:
            self.hexagram.append(value)
            self.update_display()
            self.next_btn.disabled = len(self.hexagram) != 6

    def clear_hexagram(self, instance):
        self.hexagram = []
        self.update_display()
        self.next_btn.disabled = True

    def update_display(self):
        self.hexagram_display.text = f"已选：{self.hexagram}（{len(self.hexagram)}/6）"

    def go_to_time_selection(self, instance):
        self.manager.hexagram = self.hexagram
        self.manager.current = 'time_selection'


# 时间选择屏幕
class TimeSelectionScreen(Screen):
    def __init__(self, **kwargs):
        super(TimeSelectionScreen, self).__init__(**kwargs)

        layout = BackgroundLayout()

        content_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        content_layout.add_widget(TitleLabel(text="选择时间"))

        self.current_time = datetime.now()
        self.time_display = ContentLabel(
            text=f"当前时间：{self.current_time.year}年{self.current_time.month}月{self.current_time.day}日 {self.current_time.hour}:{self.current_time.minute:02d}",
            bg_color=(1, 1, 1, 0.7)
        )
        content_layout.add_widget(self.time_display)

        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        yes_btn = RoundedButton(text="使用当前时间", size_hint_x=1)
        yes_btn.bind(on_press=self.use_current_time)
        btn_layout.add_widget(yes_btn)

        no_btn = RoundedButton(text="手动输入", size_hint_x=1, background_color=(0.6, 0.6, 0.6, 1))
        no_btn.bind(on_press=self.go_to_manual_time)
        btn_layout.add_widget(no_btn)

        content_layout.add_widget(btn_layout)
        content_layout.add_widget(Label(size_hint_y=1, color=(0, 0, 0, 0)))

        layout.add_widget(content_layout)
        self.add_widget(layout)

    def on_enter(self, *args):
        self.current_time = datetime.now()
        self.time_display.text = f"当前时间：{self.current_time.year}年{self.current_time.month}月{self.current_time.day}日 {self.current_time.hour}:{self.current_time.minute:02d}"

    def use_current_time(self, instance):
        self.manager.time = self.current_time
        self.manager.current = 'result'

    def go_to_manual_time(self, instance):
        self.manager.current = 'manual_time'


# 手动输入时间屏幕
class ManualTimeScreen(Screen):
    def __init__(self, **kwargs):
        super(ManualTimeScreen, self).__init__(**kwargs)
        now = datetime.now()

        layout = BackgroundLayout()

        content_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        content_layout.add_widget(TitleLabel(text="手动输入时间"))

        self.year_input = TextInput(
            text=str(now.year),
            hint_text="年份",
            size_hint_y=None,
            height=dp(40),
            input_filter='int',
            input_type='number',
            background_color=(1, 1, 1, 0.9)
        )
        self.month_input = TextInput(
            text=str(now.month),
            hint_text="月份",
            size_hint_y=None,
            height=dp(40),
            input_filter='int',
            input_type='number',
            background_color=(1, 1, 1, 0.9)
        )
        self.day_input = TextInput(
            text=str(now.day),
            hint_text="日期",
            size_hint_y=None,
            height=dp(40),
            input_filter='int',
            input_type='number',
            background_color=(1, 1, 1, 0.9)
        )
        self.hour_input = TextInput(
            text=str(now.hour),
            hint_text="小时（0-23）",
            size_hint_y=None,
            height=dp(40),
            input_filter='int',
            input_type='number',
            background_color=(1, 1, 1, 0.9)
        )
        self.minute_input = TextInput(
            text=str(now.minute),
            hint_text="分钟（0-59）",
            size_hint_y=None,
            height=dp(40),
            input_filter='int',
            input_type='number',
            background_color=(1, 1, 1, 0.9)
        )

        for widget in [self.year_input, self.month_input, self.day_input, self.hour_input, self.minute_input]:
            content_layout.add_widget(widget)

        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        back_btn = RoundedButton(text="返回", size_hint_x=1, background_color=(0.6, 0.6, 0.6, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'time_selection'))
        btn_layout.add_widget(back_btn)

        confirm_btn = RoundedButton(text="确认", size_hint_x=1)
        confirm_btn.bind(on_press=self.confirm_time)
        btn_layout.add_widget(confirm_btn)

        content_layout.add_widget(btn_layout)
        self.error_label = ContentLabel(text="", color=(1, 0, 0, 1))
        content_layout.add_widget(self.error_label)

        layout.add_widget(content_layout)
        self.add_widget(layout)

        #Clock.schedule_once(lambda dt: setattr(self.year_input, 'focus', True), 0.5)

    def confirm_time(self, instance):
        try:
            year = int(self.year_input.text)
            month = int(self.month_input.text)
            day = int(self.day_input.text)
            hour = int(self.hour_input.text)
            minute = int(self.minute_input.text)

            if not (1 <= month <= 12):
                raise ValueError("月份必须在1-12之间")
            if not (1 <= day <= 31):
                raise ValueError("日期必须在1-31之间")
            if not (0 <= hour <= 23):
                raise ValueError("小时必须在0-23之间")
            if not (0 <= minute <= 59):
                raise ValueError("分钟必须在0-59之间")

            self.manager.time = datetime(year, month, day, hour, minute)
            self.manager.current = 'result'

        except ValueError as e:
            self.error_label.text = f"输入错误：{str(e)}"


# 结果显示屏幕
class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super(ResultScreen, self).__init__(**kwargs)

        layout = BackgroundLayout()

        content_layout = BoxLayout(orientation='vertical')
        content_layout.add_widget(TitleLabel(text="排盘结果"))

        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True)
        self.scroll_content = ScrollableContainer()
        self.result_label = ContentLabel(
            is_scrollable=True,
            text="正在计算结果...",
            bg_color=(1, 1, 1, 0.85)
        )
        self.scroll_content.add_widget(self.result_label)
        self.scroll_view.add_widget(self.scroll_content)
        content_layout.add_widget(self.scroll_view)

        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), padding=dp(10), size_hint_y=None,
                               height=dp(60))
        restart_btn = RoundedButton(text="重新起卦", size_hint_x=1, background_color=(0.6, 0.6, 0.6, 1))
        restart_btn.bind(on_press=self.restart)
        btn_layout.add_widget(restart_btn)

        self.ai_btn = RoundedButton(text="AI解析", size_hint_x=1)
        self.ai_btn.bind(on_press=self.go_to_ai_analysis)
        btn_layout.add_widget(self.ai_btn)

        content_layout.add_widget(btn_layout)
        layout.add_widget(content_layout)
        self.add_widget(layout)
        Window.bind(width=self.on_window_width_change)

    def on_window_width_change(self, instance, width):
        if hasattr(self.result_label, 'texture_size'):
            self.result_label.width = max(width * 0.9, self.result_label.texture_size[0])

    def on_enter(self, *args):
        Clock.schedule_once(self.calculate_result, 0.1)

    def calculate_result(self, dt):
        try:
            result_text = main.arrange_hexagram(
                self.manager.hexagram,
                self.manager.time,
                self.manager.reason
            )

            self.manager.full_result = main.ai_text
            self.result_label.text = result_text
            self.result_label.width = max(Window.width * 0.9, self.result_label.texture_size[0])
            print(f"排盘结果: {result_text}")
            print(f"AI分析文本: {self.manager.full_result}")

        except Exception as e:
            self.result_label.text = f"计算出错：{str(e)}"
            print(f"计算错误: {e}")

    def restart(self, instance):
        self.manager.hexagram = []
        self.manager.time = None
        self.manager.reason = ""
        self.manager.full_result = ""
        self.manager.current = 'home'

    def go_to_ai_analysis(self, instance):
        self.manager.current = 'ai_analysis'


# AI解析屏幕（优化移动端流式输出）
class AIAnalysisScreen(Screen):
    def __init__(self, **kwargs):
        super(AIAnalysisScreen, self).__init__(**kwargs)

        layout = BackgroundLayout()

        content_layout = BoxLayout(orientation='vertical')
        content_layout.add_widget(TitleLabel(text="AI解析"))

        # 状态标签
        self.status_label = ContentLabel(
            text="准备解析...",
            size_hint_y=None,
            height=dp(30)
        )
        content_layout.add_widget(self.status_label)

        # 滚动视图
        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True)
        self.scroll_content = ScrollableContainer()
        self.analysis_label = ContentLabel(
            is_scrollable=True,
            text="",
            bg_color=(1, 1, 1, 0.85)
        )
        self.scroll_content.add_widget(self.analysis_label)
        self.scroll_view.add_widget(self.scroll_content)
        content_layout.add_widget(self.scroll_view)

        # 按钮布局
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), padding=dp(10), size_hint_y=None,
                               height=dp(60))
        back_btn = RoundedButton(text="返回结果", size_hint_x=1, background_color=(0.6, 0.6, 0.6, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'result'))
        btn_layout.add_widget(back_btn)

        restart_btn = RoundedButton(text="重新起卦", size_hint_x=1)
        restart_btn.bind(on_press=self.restart)
        btn_layout.add_widget(restart_btn)

        content_layout.add_widget(btn_layout)
        layout.add_widget(content_layout)
        self.add_widget(layout)

        # 初始化变量
        self.full_analysis = ""
        self.is_analyzing = False
        self.chunk_count = 0  # 计数接收的流式块数量
        Window.bind(width=self.on_window_width_change)

    def on_window_width_change(self, instance, width):
        if hasattr(self.analysis_label, 'texture_size'):
            self.analysis_label.width = max(width * 0.9, self.analysis_label.texture_size[0])

    def on_enter(self, *args):
        """进入屏幕时初始化并开始分析"""
        self.reset_analysis()
        self.is_analyzing = True
        self.start_ai_analysis()

    def reset_analysis(self):
        """重置分析状态"""
        self.analysis_label.text = ""
        self.full_analysis = ""
        self.chunk_count = 0
        self.status_label.text = "准备解析..."

    def start_ai_analysis(self):
        """启动AI分析流程"""
        if not self.manager.full_result:
            self.status_label.text = "错误：没有可用的排盘结果"
            self.analysis_label.text = "没有可用的排盘结果进行解析"
            return

        # 显示初始信息
        self.full_analysis = "AI正在解析排盘结果，请稍候...\n\n"
        self.update_analysis_text()
        self.status_label.text = "正在调用AI接口..."

        # 在新线程中执行AI调用，避免阻塞UI
        from threading import Thread
        Thread(target=self.process_ai_stream, daemon=True).start()

    def process_ai_stream(self):
        """处理AI流式响应 - 优化移动端适配"""
        try:
            # 移动端网络连接检查
            def is_connected():
                try:
                    # 尝试连接百度，超时5秒
                    socket.create_connection(("www.baidu.com", 80), timeout=5)
                    return True
                except:
                    return False

            # 检查网络连接
            if not is_connected():
                self.update_status("网络连接失败，请检查网络")
                self.full_analysis += "\n\n错误：网络连接失败，请检查网络设置"
                Clock.schedule_once(lambda dt: self.update_analysis_text(), 0)
                return

            # 调用AI模块的流式接口（返回生成器）
            self.update_status("正在发送请求...")
            response_generator = ai_main.deepseek_chat(
                api_key="sk-********************************",  #填写你自己的deepseek APIkey（基于deepseek文档开发，其他AI接口可能不兼容）
                prompt=f"请对以下六爻排盘信息进行解析：\n{self.manager.full_result}",
                stream=True,
                max_tokens=1500,
                temperature=0.7,
                model="deepseek-chat"
            )

            # 迭代处理流式数据
            for chunk_data in response_generator:
                # 检查是否需要终止
                if not self.is_analyzing:
                    self.update_status("解析已终止")
                    return

                # 处理单个流式块
                self.chunk_count += 1
                self.update_status(f"接收第{self.chunk_count}个数据块")

                # 判断返回格式（是错误信息还是内容）
                if isinstance(chunk_data, dict) and "error" in chunk_data:
                    raise Exception(chunk_data["error"])

                # 将内容添加到分析文本
                chunk_str = str(chunk_data) if chunk_data else ""
                self.full_analysis += chunk_str

                # 移动端优化：减少UI更新频率，避免性能问题
                if self.chunk_count % 2 == 0 or "。" in chunk_str or "？" in chunk_str or "！" in chunk_str:
                    Clock.schedule_once(lambda dt: self.update_analysis_text(), 0)

                # 调整延迟时间适应移动端
                time.sleep(0.05)

            # 所有流式数据处理完毕
            self.full_analysis += "\n\n=== AI解析结束 ===\n\n"
            self.full_analysis += "=== 排盘信息 ===\n"
            self.full_analysis += self.manager.full_result
            Clock.schedule_once(lambda dt: self.update_analysis_text(), 0)
            self.update_status("解析完成")

        except Exception as e:
            error_msg = f"解析错误: {str(e)}"
            print(error_msg)
            self.full_analysis += f"\n\n{error_msg}"
            Clock.schedule_once(lambda dt: self.update_analysis_text(), 0)
            self.update_status("解析出错")

    @mainthread
    def update_analysis_text(self):
        """在主线程更新分析文本UI"""
        self.analysis_label.text = self.full_analysis
        self.analysis_label.width = max(Window.width * 0.92,
                                        self.analysis_label.texture_size[0]
                                        if hasattr(self.analysis_label, 'texture_size')
                                        else Window.width * 0.92)
        self.analysis_label.texture_update()  # 强制刷新文本纹理
        # 自动滚动到底部
        # self.scroll_view.scroll_y = 0
        print(f"UI更新: 已显示 {self.chunk_count} 个数据块")

    @mainthread
    def update_status(self, text):
        """在主线程更新状态标签"""
        self.status_label.text = text
        print(f"状态更新: {text}")

    def restart(self, instance):
        """重新起卦"""
        self.is_analyzing = False
        self.manager.hexagram = []
        self.manager.time = None
        self.manager.reason = ""
        self.manager.full_result = ""
        self.manager.current = 'home'

    def on_leave(self, *args):
        """离开屏幕时停止分析"""
        self.is_analyzing = False


# 主应用
class HexagramApp(App):
    def build(self):
        Window.clearcolor = (0.95, 0.95, 0.95, 1)
        sm = ScreenManager()

        sm.reason = ""
        sm.hexagram = []
        sm.time = None
        sm.full_result = ""

        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ReasonScreen(name='reason'))
        sm.add_widget(HexagramInputScreen(name='hexagram_input'))
        sm.add_widget(TimeSelectionScreen(name='time_selection'))
        sm.add_widget(ManualTimeScreen(name='manual_time'))
        sm.add_widget(ResultScreen(name='result'))
        sm.add_widget(AIAnalysisScreen(name='ai_analysis'))

        return sm


if __name__ == '__main__':
    HexagramApp().run()
