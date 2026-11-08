from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle, Ellipse, Line, RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window
import random

COLS = 20
ROWS = 20
BASE_STEP_TIME = 0.10

C_PRIMARY   = (0.22, 0.72, 0.35, 1)
C_SECONDARY = (0.25, 0.52, 0.88, 1)
C_WARNING   = (0.95, 0.65, 0.15, 1)
C_DANGER    = (0.85, 0.32, 0.32, 1)
C_NEUTRAL   = (0.38, 0.40, 0.45, 1)
C_ACTIVE    = (0.22, 0.72, 0.35, 1)
C_PURPLE    = (0.60, 0.40, 0.85, 1)


class SnakeGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.paused = False
        self.speed_multiplier = 1.0
        self.cell_size = 40
        self.app = None
        self.game_over = True
        self.start_touch = None

        Clock.schedule_interval(self.update, 1.0 / 60.0)
        self.bind(size=self.on_size)
        self.reset_game()

    def reset_game(self):
        self.game_over = False
        self.score = 0
        self.time_acc = 0.0
        self.snake = [(10, 10), (9, 10), (8, 10)]
        self.prev_snake = list(self.snake)
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.start_touch = None
        self.spawn_food()
        self.draw_game()

    def on_size(self, *args):
        self.cell_size = min(Window.width / COLS,
                             (Window.height - 200) / ROWS)
        if self.cell_size <= 0:
            self.cell_size = 10
        self.draw_game()

    def spawn_food(self):
        while True:
            new_food = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if new_food not in self.snake:
                self.food = new_food
                break

    def update(self, dt):
        if self.app:
            self.app.count_frame()
        if self.game_over or self.paused:
            return

        self.time_acc += dt
        step_time = BASE_STEP_TIME / self.speed_multiplier

        while self.time_acc >= step_time and not self.game_over:
            self.time_acc -= step_time
            self.step()

        if not self.game_over:
            self.draw_game()

    def step(self):
        self.prev_snake = list(self.snake)

        if (self.next_direction[0] != -self.direction[0] or
                self.next_direction[1] != -self.direction[1]):
            self.direction = self.next_direction

        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])

        if (new_head[0] < 0 or new_head[0] >= COLS or
                new_head[1] < 0 or new_head[1] >= ROWS):
            self.end_game()
            return

        if new_head in self.snake:
            self.end_game()
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 1
            self.spawn_food()
            if self.app:
                self.app.play_sound()
        else:
            self.snake.pop()

    def end_game(self):
        self.game_over = True
        if self.app:
            self.app.show_game_over()

    def _palette(self):
        if self.app:
            return self.app.get_colors()
        return {
            'snake_head': (0.40, 1.0, 0.45, 1),
            'snake_body': (0.15, 0.65, 0.25, 1),
            'food': (0.95, 0.30, 0.30, 1),
        }

    def draw_game(self):
        self.canvas.clear()
        grid_w = COLS * self.cell_size
        grid_h = ROWS * self.cell_size
        offset_x = (Window.width - grid_w) / 2
        offset_y = (Window.height - grid_h) / 2

        step_time = BASE_STEP_TIME / self.speed_multiplier
        if step_time <= 0:
            progress = 1.0
        else:
            progress = min(self.time_acc / step_time, 1.0)

        pal = self._palette()

        with self.canvas:
            # Фон поля
            Color(0.06, 0.08, 0.10, 1)
            Rectangle(pos=(offset_x, offset_y), size=(grid_w, grid_h))

            # Тонкая сетка
            Color(0.10, 0.13, 0.16, 1)
            for i in range(1, COLS):
                x = offset_x + i * self.cell_size
                Line(points=[x, offset_y, x, offset_y + grid_h], width=0.6)
            for j in range(1, ROWS):
                y = offset_y + j * self.cell_size
                Line(points=[offset_x, y, offset_x + grid_w, y], width=0.6)

            # Еда с бликом
            fx = offset_x + (self.food[0] + 0.5) * self.cell_size
            fy = offset_y + (self.food[1] + 0.5) * self.cell_size
            r = self.cell_size * 0.42
            Color(*pal['food'])
            Ellipse(pos=(fx - r, fy - r), size=(r * 2, r * 2))
            Color(1, 1, 1, 0.5)
            hr = r * 0.35
            Ellipse(pos=(fx - r * 0.35 - hr, fy + r * 0.15 - hr),
                    size=(hr * 2, hr * 2))

            # Тело змейки — линия с круглыми стыками
            points = []
            for i, seg in enumerate(self.snake):
                if i < len(self.prev_snake):
                    from_seg = self.prev_snake[i]
                else:
                    from_seg = self.prev_snake[-1]
                x = from_seg[0] + (seg[0] - from_seg[0]) * progress
                y = from_seg[1] + (seg[1] - from_seg[1]) * progress
                points.extend([
                    offset_x + (x + 0.5) * self.cell_size,
                    offset_y + (y + 0.5) * self.cell_size
                ])

            if len(points) >= 4:
                Color(*pal['snake_body'])
                Line(points=points, width=self.cell_size * 0.85,
                     joint='round', cap='round')

            # Голова
            if len(points) >= 2:
                hx, hy = points[0], points[1]
                hr = self.cell_size * 0.5
                Color(*pal['snake_head'])
                Ellipse(pos=(hx - hr, hy - hr), size=(hr * 2, hr * 2))

                # Глаза
                dx, dy = self.direction
                px, py = -dy, dx
                eye_off = hr * 0.42
                eye_side = hr * 0.35
                er = hr * 0.28

                for side in (1, -1):
                    ex = hx + dx * eye_off + px * eye_side * side
                    ey = hy + dy * eye_off + py * eye_side * side
                    Color(1, 1, 1)
                    Ellipse(pos=(ex - er, ey - er), size=(er * 2, er * 2))
                    Color(0.05, 0.05, 0.05)
                    pr = er * 0.55
                    Ellipse(pos=(ex - pr + dx * pr * 0.4,
                                 ey - pr + dy * pr * 0.4),
                            size=(pr * 2, pr * 2))

    def _apply_swipe(self, dx, dy):
        if abs(dx) < 22 and abs(dy) < 22:
            return False
        if abs(dx) > abs(dy):
            new_dir = (1, 0) if dx > 0 else (-1, 0)
        else:
            new_dir = (0, 1) if dy > 0 else (0, -1)
        return self._try_turn(new_dir)

    def _try_turn(self, new_dir):
        if new_dir == self.direction or new_dir == self.next_direction:
            return False
        if (new_dir[0] == -self.direction[0] and
                new_dir[1] == -self.direction[1]):
            return False
        if (new_dir[0] == -self.next_direction[0] and
                new_dir[1] == -self.next_direction[1]):
            return False
        self.next_direction = new_dir
        step_time = BASE_STEP_TIME / self.speed_multiplier
        if self.time_acc >= step_time * 0.55:
            self.time_acc = step_time
        return True

    def on_touch_down(self, touch):
        if self.game_over or self.paused:
            return False
        self.start_touch = touch.pos
        return True

    def on_touch_move(self, touch):
        if self.game_over or self.paused or self.start_touch is None:
            return False
        dx = touch.x - self.start_touch[0]
        dy = touch.y - self.start_touch[1]
        if self._apply_swipe(dx, dy):
            self.start_touch = touch.pos
        return True

    def on_touch_up(self, touch):
        if self.game_over or self.paused or self.start_touch is None:
            return False
        dx = touch.x - self.start_touch[0]
        dy = touch.y - self.start_touch[1]
        self._apply_swipe(dx, dy)
        self.start_touch = None
        return True


class SnakeApp(App):
    def build(self):
        Window.fullscreen = 'auto'
        self.root_layout = FloatLayout()

        self.sound_enabled = True
        self.show_fps = False
        self.colorblind_mode = False
        self.fps_counter = 0
        self.fps_value = 0
        self.current_speed = 1.0

        self.build_game_screen()
        self.build_menu_screen()
        self.build_settings_screen()
        self.build_pause_screen()
        self.build_death_screen()

        self.refresh_settings_ui()

        Clock.schedule_interval(self.update_fps, 1.0)
        Clock.schedule_interval(self.update_ui, 0.1)

        self.root_layout.add_widget(self.menu_screen)
        return self.root_layout

    def get_colors(self):
        if self.colorblind_mode:
            return {
                'snake_head': (0.45, 0.75, 1.0, 1),
                'snake_body': (0.20, 0.42, 0.85, 1),
                'food': (1.0, 0.72, 0.15, 1),
            }
        return {
            'snake_head': (0.40, 1.0, 0.45, 1),
            'snake_body': (0.15, 0.65, 0.25, 1),
            'food': (0.95, 0.30, 0.30, 1),
        }

    def build_game_screen(self):
        self.game_screen = FloatLayout()
        self.game = SnakeGame(size_hint=(1, 1))
        self.game.app = self
        self.game_screen.add_widget(self.game)

        top_bar = BoxLayout(
            size_hint=(1, None), height=70,
            pos_hint={'top': 1.0},
            padding=(10, 8), spacing=8
        )

        left_box = BoxLayout(size_hint=(0.28, 1))
        self.fps_label = Label(
            text="FPS: 0", font_size='20sp', bold=True,
            halign='left', valign='middle',
            color=(0.3, 1.0, 0.3, 1), opacity=0
        )
        self.fps_label.bind(size=self._sync_fps_text_size)
        left_box.add_widget(self.fps_label)

        self.score_label = Label(
            text="Счет: 0", font_size='30sp', bold=True,
            halign='center', valign='middle'
        )
        self.score_label.bind(size=self._sync_score_text_size)

        right_box = BoxLayout(size_hint=(0.28, 1))
        right_box.add_widget(Widget(size_hint=(1, 1)))
        self.pause_btn = RoundedButton(
            text="II", font_size='22sp', bold=True,
            size_hint=(None, 1), width=65,
            bg_color=C_WARNING
        )
        self.pause_btn.bind(on_press=self.open_pause)
        right_box.add_widget(self.pause_btn)

        top_bar.add_widget(left_box)
        top_bar.add_widget(self.score_label)
        top_bar.add_widget(right_box)

        self.game_screen.add_widget(top_bar)

        speed_layout = BoxLayout(
            size_hint=(0.9, None), height=70,
            pos_hint={'center_x': 0.5, 'y': 0.02}, spacing=10
        )
        self.speed_buttons = []
        for text, val in [("0.5x", 0.5), ("1.0x", 1.0), ("2.0x", 2.0), ("3.0x", 3.0)]:
            btn = RoundedButton(text=text, font_size='18sp', bold=True,
                                bg_color=C_NEUTRAL)
            btn.bind(on_press=lambda inst, v=val: self.change_speed(v))
            speed_layout.add_widget(btn)
            self.speed_buttons.append((btn, val))
        self.game_screen.add_widget(speed_layout)

    def _sync_fps_text_size(self, instance, size):
        instance.text_size = size

    def _sync_score_text_size(self, instance, size):
        instance.text_size = size

    def build_menu_screen(self):
        self.menu_screen = FloatLayout()
        with self.menu_screen.canvas:
            Color(0.06, 0.09, 0.13)
            self._menu_bg = Rectangle(pos=(0, 0), size=Window.size)
            Color(0.09, 0.13, 0.19)
            self._menu_bg2 = Rectangle(pos=(0, 0), size=Window.size)
        Window.bind(size=self._update_menu_bg)

        title = Label(
            text="ЗМЕЙКА", font_size='64sp', bold=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.78},
            color=(0.35, 1.0, 0.45, 1)
        )
        self.menu_screen.add_widget(title)

        subtitle = Label(
            text="классическая аркада", font_size='16sp',
            pos_hint={'center_x': 0.5, 'center_y': 0.70},
            color=(0.6, 0.65, 0.7, 1)
        )
        self.menu_screen.add_widget(subtitle)

        btn_play = RoundedButton(
            text="ИГРАТЬ", font_size='26sp', bold=True,
            size_hint=(None, None), size=(300, 80),
            pos_hint={'center_x': 0.5, 'center_y': 0.48},
            bg_color=C_PRIMARY, radius=18
        )
        btn_play.bind(on_press=self.start_game)
        self.menu_screen.add_widget(btn_play)

        btn_settings = RoundedButton(
            text="НАСТРОЙКИ", font_size='26sp', bold=True,
            size_hint=(None, None), size=(300, 80),
            pos_hint={'center_x': 0.5, 'center_y': 0.32},
            bg_color=C_SECONDARY, radius=18
        )
        btn_settings.bind(on_press=self.open_settings)
        self.menu_screen.add_widget(btn_settings)

    def _update_menu_bg(self, *args):
        self._menu_bg.size = Window.size
        self._menu_bg2.pos = (0, Window.height * 0.65)
        self._menu_bg2.size = (Window.width, Window.height * 0.35)
        
    def _make_setting_row(self, icon_type, text, on_press, y_pos, btn_attr):
        row = BoxLayout(
            size_hint=(None, None), size=(340, 68),
            pos_hint={'center_x': 0.5, 'center_y': y_pos},
            spacing=10
        )
        icon = IconWidget(icon_type=icon_type,
                          size_hint=(None, 1), width=68)
        btn = RoundedButton(text=text, font_size='18sp', bold=True,
                            bg_color=C_NEUTRAL, radius=14)
        btn.bind(on_press=on_press)
        setattr(self, btn_attr, btn)
        row.add_widget(icon)
        row.add_widget(btn)
        return row

    def build_settings_screen(self):
        self.settings_screen = FloatLayout()
        with self.settings_screen.canvas:
            Color(0.06, 0.09, 0.13)
            Rectangle(pos=(0, 0), size=Window.size)

        lbl = Label(text="НАСТРОЙКИ", font_size='36sp', bold=True,
                    pos_hint={'center_x': 0.5, 'center_y': 0.90})
        self.settings_screen.add_widget(lbl)

        self.settings_screen.add_widget(
            self._make_setting_row("sound", "ЗВУК: ВКЛ",
                                   self.toggle_sound, 0.74,
                                   "btn_sound_settings"))

        self.settings_screen.add_widget(
            self._make_setting_row("fps", "FPS: ВЫКЛ",
                                   self.toggle_fps, 0.62,
                                   "btn_fps"))

        self.settings_screen.add_widget(
            self._make_setting_row("eye", "ДАЛЬТОНИК: ВЫКЛ",
                                   self.toggle_colorblind, 0.50,
                                   "btn_colorblind_settings"))

        speed_hint = Label(
            text="Скорость", font_size='18sp',
            pos_hint={'center_x': 0.5, 'center_y': 0.40},
            color=(0.7, 0.75, 0.8, 1)
        )
        self.settings_screen.add_widget(speed_hint)

        speed_layout = BoxLayout(
            size_hint=(0.9, None), height=62,
            pos_hint={'center_x': 0.5, 'center_y': 0.32}, spacing=8
        )
        self.settings_speed_buttons = []
        for text, val in [("0.5x", 0.5), ("1.0x", 1.0), ("2.0x", 2.0), ("3.0x", 3.0)]:
            btn = RoundedButton(text=text, font_size='17sp', bold=True,
                                bg_color=C_NEUTRAL, radius=12)
            btn.bind(on_press=lambda inst, v=val: self.change_speed(v))
            speed_layout.add_widget(btn)
            self.settings_speed_buttons.append((btn, val))
        self.settings_screen.add_widget(speed_layout)

        btn_back = RoundedButton(
            text="НАЗАД", font_size='22sp', bold=True,
            size_hint=(None, None), size=(300, 62),
            pos_hint={'center_x': 0.5, 'center_y': 0.14},
            bg_color=C_DANGER, radius=16
        )
        btn_back.bind(on_press=self.back_to_menu)
        self.settings_screen.add_widget(btn_back)

    def build_pause_screen(self):
        self.pause_screen = FloatLayout()
        with self.pause_screen.canvas:
            Color(0.06, 0.09, 0.13)
            Rectangle(pos=(0, 0), size=Window.size)

        lbl_pause = Label(text="ПАУЗА", font_size='40sp', bold=True,
                          pos_hint={'center_x': 0.5, 'center_y': 0.92})
        self.pause_screen.add_widget(lbl_pause)

        btn_resume = RoundedButton(
            text="ПРОДОЛЖИТЬ", font_size='22sp', bold=True,
            size_hint=(None, None), size=(300, 62),
            pos_hint={'center_x': 0.5, 'center_y': 0.80},
            bg_color=C_PRIMARY, radius=16
        )
        btn_resume.bind(on_press=self.close_pause)
        self.pause_screen.add_widget(btn_resume)

        self.pause_screen.add_widget(
            self._make_setting_row("sound", "ЗВУК: ВКЛ",
                                   self.toggle_sound, 0.68,
                                   "btn_sound"))

        self.pause_screen.add_widget(
            self._make_setting_row("fps", "FPS: ВЫКЛ",
                                   self.toggle_fps, 0.57,
                                   "btn_fps_pause"))

        self.pause_screen.add_widget(
            self._make_setting_row("eye", "ДАЛЬТОНИК: ВЫКЛ",
                                   self.toggle_colorblind, 0.46,
                                   "btn_colorblind_pause"))

        speed_layout = BoxLayout(
            size_hint=(0.9, None), height=58,
            pos_hint={'center_x': 0.5, 'center_y': 0.35}, spacing=8
        )
        self.pause_speed_buttons = []
        for text, val in [("0.5x", 0.5), ("1.0x", 1.0), ("2.0x", 2.0), ("3.0x", 3.0)]:
            btn = RoundedButton(text=text, font_size='17sp', bold=True,
                                bg_color=C_NEUTRAL, radius=12)
            btn.bind(on_press=lambda inst, v=val: self.change_speed(v))
            speed_layout.add_widget(btn)
            self.pause_speed_buttons.append((btn, val))
        self.pause_screen.add_widget(speed_layout)

        btn_menu = RoundedButton(
            text="МЕНЮ", font_size='22sp', bold=True,
            size_hint=(None, None), size=(300, 62),
            pos_hint={'center_x': 0.5, 'center_y': 0.20},
            bg_color=C_DANGER, radius=16
        )
        btn_menu.bind(on_press=self.to_menu)
        self.pause_screen.add_widget(btn_menu)

    def build_death_screen(self):
        self.death_screen = FloatLayout()
        self._draw_death_art()
        Window.bind(size=lambda *a: self._draw_death_art())

        self.death_label = Label(
            text="", font_size='44sp', bold=True, color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.83}
        )
        self.death_screen.add_widget(self.death_label)

        sub = Label(
            text="Игра окончена", font_size='18sp',
            color=(0.65, 0.7, 0.75, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.32}
        )
        self.death_screen.add_widget(sub)

        btn_restart = RoundedButton(
            text="ЗАНОВО", font_size='22sp', bold=True,
            size_hint=(None, None), size=(300, 62),
            pos_hint={'center_x': 0.5, 'center_y': 0.20},
            bg_color=C_PRIMARY, radius=16
        )
        btn_restart.bind(on_press=self.restart_game)
        self.death_screen.add_widget(btn_restart)

        btn_menu_death = RoundedButton(
            text="МЕНЮ", font_size='22sp', bold=True,
            size_hint=(None, None), size=(300, 62),
            pos_hint={'center_x': 0.5, 'center_y': 0.08},
            bg_color=C__DANGER, radius=16
        )
        btn_menu_death.bind(on_press=self.to_menu)
        self.death_screen.add_widget(btn_menu_death)

    def _draw_death_art(self):
        w = Window.width
        h = Window.height
        cx = w / 2
        cy = h * 0.62
        head_w = min(w * 0.55, h * 0.28)
        head_h = head_w * 0.55

        with self.death_screen.canvas.before:
            Color(0.06, 0.09, 0.13)
            Rectangle(pos=(0, 0), size=Window.size)

        with self.death_screen.canvas:
            Color(0.06, 0.09, 0.13)
            Rectangle(pos=(0, 0), size=Window.size)

            Color(0.20, 0.65, 0.30)
            Ellipse(pos=(cx - head_w/2, cy - head_h/2),
                    size=(head_w, head_h))

            Color(1, 1, 1)
            eye_size = head_w * 0.22
            eye_y = cy + head_h * 0.12
            left_eye_x  = cx - head_w * 0.22
            right_eye_x = cx + head_w * 0.22
            Ellipse(pos=(left_eye_x - eye_size/2, eye_y - eye_size/2),
                    size=(eye_size, eye_size))
            Ellipse(pos=(right_eye_x - eye_size/2, eye_y - eye_size/2),
                    size=(eye_size, eye_size))

            Color(0.1, 0.1, 0.1)
            xs = eye_size * 0.65
            for ex in (left_eye_x, right_eye_x):
                Line(points=[ex - xs/2, eye_y - xs/2,
                             ex + xs/2, eye_y + xs/2], width=3)
                Line(points=[ex - xs/2, eye_y + xs/2,
                             ex + xs/2, eye_y - xs/2], width=3)

            Color(0.9, 0.2, 0.25)
            ty = cy - head_h/2
            tlen = h * 0.05
            Line(points=[cx, ty, cx, ty - tlen], width=4)
            Line(points=[cx, ty - tlen,
                         cx - w*0.018, ty - tlen - h*0.018], width=4)
            Line(points=[cx, ty - tlen,
                         cx + w*0.018, ty - tlen - h*0.018], width=4)

    def start_game(self, instance):
        self.game.reset_game()
        self.game.paused = False
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.game_screen)

    def open_settings(self, instance):
        self.refresh_settings_ui()
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.settings_screen)

    def back_to_menu(self, instance):
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.menu_screen)

    def to_menu(self, instance):
        self.game.paused = False
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.menu_screen)

    def open_pause(self, instance):
        self.game.paused = True
        self.refresh_settings_ui()
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.pause_screen)

    def close_pause(self, instance):
        self.game.paused = False
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.game_screen)

    def change_speed(self, value):
        self.current_speed = value
        self.game.speed_multiplier = value
        self.update_speed_buttons()

    def update_speed_buttons(self):
        for buttons in (self.speed_buttons,
                        self.settings_speed_buttons,
                        self.pause_speed_buttons):
            for btn, val in buttons:
                btn.set_color(C_ACTIVE if val == self.current_speed else C_NEUTRAL)

    def refresh_settings_ui(self):
        sound_text = "ЗВУК: ВКЛ" if self.sound_enabled else "ЗВУК: ВЫКЛ"
        fps_text = "FPS: ВКЛ" if self.show_fps else "FPS: ВЫКЛ"
        cb_text = "ДАЛЬТОНИК: ВКЛ" if self.colorblind_mode else "ДАЛЬТОНИК: ВЫКЛ"

        self.btn_sound.text = sound_text
        self.btn_sound_settings.text = sound_text
        self.btn_fps.text = fps_text
        self.btn_fps_pause.text = fps_text
        self.btn_colorblind_settings.text = cb_text
        self.btn_colorblind_pause.text = cb_text

        self.btn_fps.set_color(C_PRIMARY if self.show_fps else C_NEUTRAL)
        self.btn_fps_pause.set_color(C_PRIMARY if self.show_fps else C_NEUTRAL)
        self.btn_colorblind_settings.set_color(
            C_PURPLE if self.colorblind_mode else C_NEUTRAL)
        self.btn_colorblind_pause.set_color(
            C_PURPLE if self.colorblind_mode else C_NEUTRAL)

        self.update_speed_buttons()

    def toggle_sound(self, instance):
        self.sound_enabled = not self.sound_enabled
        self.refresh_settings_ui()

    def toggle_fps(self, instance):
        self.show_fps = not self.show_fps
        self.fps_label.opacity = 1 if self.show_fps else 0
        self.fps_counter = 0
        self.refresh_settings_ui()

    def toggle_colorblind(self, instance):
        self.colorblind_mode = not self.colorblind_mode
        self.refresh_settings_ui()
        self.game.draw_game()

    def count_frame(self):
        if self.show_fps:
            self.fps_counter += 1

    def update_fps(self, dt):
        if self.show_fps:
            self.fps_value = self.fps_counter
            self.fps_counter = 0
            self.fps_label.text = f"FPS: {self.fps_value}"

    def play_sound(self):
        if self.sound_enabled:
            try:
                from jnius import autoclass
                ToneGenerator = autoclass('android.media.ToneGenerator')
                tone = ToneGenerator(
                    autoclass('android.media.AudioManager').STREAM_MUSIC, 100)
                tone.startTone(ToneGenerator.TONE_PROP_BEEP, 50)
            except Exception:
                pass

    def update_ui(self, dt):
        self.score_label.text = f"Счет: {self.game.score}"

    def show_game_over(self):
        self.death_label.text = f"Счет: {self.game.score}"
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.death_screen)

    def restart_game(self, instance):
        self.game.reset_game()
        self.game.paused = False
        self.root_layout.clear_widgets()
        self.root_layout.add_widget(self.game_screen)


class RoundedButton(Button):
    """Кнопка со скруглёнными углами и мягкой тенью."""

    def __init__(self, bg_color=C_NEUTRAL, radius=14, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.bind(pos=self._redraw, size=self._redraw)

    def set_color(self, color):
        self.bg_color = color
        self._redraw()

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Тень
            Color(0, 0, 0, 0.25)
            RoundedRectangle(
                pos=(self.x + 2, self.y - 3),
                size=self.size,
                radius=[self.radius]
            )
            # Основной фон
            Color(*self.bg_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.radius]
            )


class IconWidget(Widget):
    """Иконки для строк настроек."""

    def __init__(self, icon_type="sound", **kwargs):
        super().__init__(**kwargs)
        self.icon_type = icon_type
        self.bind(size=self.redraw, pos=self.redraw)
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        w, h = self.size
        x, y = self.pos

        with self.canvas:
            if self.icon_type == "sound":
                Color(0.95, 0.65, 0.15, 1)
                Rectangle(pos=(x + w*0.20, y + h*0.35),
                          size=(w*0.22, h*0.30))
                Line(points=[
                    x + w*0.42, y + h*0.35,
                    x + w*0.65, y + h*0.20,
                    x + w*0.65, y + h*0.80,
                    x + w*0.42, y + h*0.65
                ], width=2)
                Line(points=[
                    x + w*0.72, y + h*0.38,
                    x + w*0.80, y + h*0.50,
                    x + w*0.72, y + h*0.62
                ], width=2)
                Line(points=[
                    x + w*0.80, y + h*0.30,
                    x + w*0.92, y + h*0.50,
                    x + w*0.80, y + h*0.70
                ], width=2)

            elif self.icon_type == "fps":
                Color(0.35, 1.0, 0.35, 1)
                base_y = y + h*0.25
                bw = w * 0.13
                gap = w * 0.06
                heights = [0.30, 0.55, 0.75, 0.50]
                start_x = x + w*0.15
                for i, hh in enumerate(heights):
                    Rectangle(pos=(start_x + i*(bw+gap), base_y),
                              size=(bw, h*hh))
                Color(0.7, 0.7, 0.75, 1)
                Line(points=[x + w*0.10, base_y, x + w*0.90, base_y],
                     width=1.5)

            elif self.icon_type == "eye":
                Color(0.60, 0.40, 0.85, 1)
                # Контур глаза
                Line(points=[
                    x + w*0.10, y + h*0.50,
                    x + w*0.30, y + h*0.30,
                    x + w*0.50, y + h*0.25,
                    x + w*0.70, y + h*0.30,
                    x + w*0.90, y + h*0.50,
                    x + w*0.70, y + h*0.70,
                    x + w*0.50, y + h*0.75,
                    x + w*0.30, y + h*0.70,
                    x + w*0.10, y + h*0.50,
                ], width=2.2, close=True)
                # Зрачок
                Ellipse(pos=(x + w*0.38, y + h*0.38),
                        size=(w*0.24, h*0.24))

            else:
                Color(0.6, 0.6, 0.7, 1)
                Ellipse(pos=(x + w*0.25, y + h*0.25),
                        size=(w*0.5, h*0.5))


if __name__ == '__main__':
    SnakeApp().run()
