"""Плашка «Активация Linux»: цветной Tux и градиентный заголовок.

Окно без рамки, всегда сверху, клики проходят сквозь него.
Запуск:  python activation_linux.py [--seconds N]
Выход:   Esc (пока окно в фокусе) или Ctrl+C в консоли.
"""

import ctypes
import math
import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from ctypes import wintypes

KEY = "#010203"
SHADOW = "#0d1524"
SUBTITLE_COLOR = "#a9b4c8"
GLINT_COLOR = "#ffe9a8"
PAD = 18

BODY_TOP = "#8ff0ff"
BODY_BOTTOM = "#8b7bff"
EYE = "#ffffff"
BEAK = "#ffb03a"
FEET = "#ff8a3d"

TITLE = "Активация Linux"
SUBTITLE = "Перейдите в раздел «Параметры», чтобы активировать Linux."

TITLE_STOPS = ["#8ff0ff", "#a78bfa", "#f472b6", "#fcd34d", "#8ff0ff"]
BAR_STOPS = ["#8ff0ff", "#a78bfa", "#f472b6"]

TUX = [
    [("        .--.", "body")],
    [
        ("       |", "body"),
        ("o", "eye"),
        ("_", "body"),
        ("o", "eye"),
        (" |", "body"),
    ],
    [("       |", "body"), (":_/", "beak"), (" |", "body")],
    [("      //   \\ \\", "body")],
    [("     (|     | )", "body")],
    [("    /'\\_   _/`\\", "body")],
    [("    \\___)=(___/", "feet")],
]

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080


class Colors:
    def __init__(self, value):
        self.value = value.lstrip("#")

    @classmethod
    def from_rgb(cls, rgb):
        return "#%02x%02x%02x" % tuple(int(round(c)) for c in rgb)

    def channels(self):
        return [int(self.value[i:i + 2], 16) for i in (0, 2, 4)]


def lerp(first, second, t):
    a = Colors(first).channels()
    b = Colors(second).channels()
    return Colors.from_rgb(a[i] + (b[i] - a[i]) * t for i in range(3))


def gradient(stops, t):
    t %= 1.0
    position = t * (len(stops) - 1)
    index = int(position)
    if index >= len(stops) - 1:
        return stops[-1]
    return lerp(stops[index], stops[index + 1], position - index)


def pick_font_family(root, preferred, fallback):
    available = set(tkfont.families(root))
    for name in preferred:
        if name in available:
            return name
    return fallback


def wrap_text(text, font, max_width):
    lines = []
    current = ""
    for word in text.split():
        trial = (current + " " + word).strip()
        if not current or font.measure(trial) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def enable_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def set_click_through(root):
    user32 = ctypes.windll.user32
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = wintypes.LONG
    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
    user32.SetWindowLongW.restype = wintypes.LONG

    hwnd = user32.GetParent(root.winfo_id()) or root.winfo_id()
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)


def draw_tux(canvas, font, char_width, line_height, left, top):
    for shadow in (True, False):
        offset = 1 if shadow else 0
        for row_index, row in enumerate(TUX):
            color = gradient([BODY_TOP, BODY_BOTTOM], row_index / max(1, len(TUX) - 1))
            x = left + offset
            y = top + row_index * line_height + offset
            for text, role in row:
                if shadow:
                    fill = SHADOW
                else:
                    fill = {
                        "body": color,
                        "eye": EYE,
                        "beak": BEAK,
                        "feet": FEET,
                    }[role]
                canvas.create_text(x, y, text=text, font=font, fill=fill, anchor="nw")
                x += len(text) * char_width


def draw_title(canvas, font, text, left, top):
    items = []
    x = left
    for char in text:
        canvas.create_text(x + 1, top + 1, text=char, font=font, fill=SHADOW, anchor="nw")
        item = canvas.create_text(x, top, text=char, font=font, fill=TITLE_STOPS[0], anchor="nw")
        items.append(item)
        x += font.measure(char)
    return items


def draw_subtitle(canvas, font, lines, line_height, left, top):
    for index, line in enumerate(lines):
        y = top + index * line_height
        canvas.create_text(left + 1, y + 1, text=line, font=font, fill=SHADOW, anchor="nw")
        canvas.create_text(left, y, text=line, font=font, fill=SUBTITLE_COLOR, anchor="nw")


def draw_bar(canvas, left, top, width, segment=4):
    count = max(1, int(width // segment))
    step = width / count
    for index in range(count):
        x1 = left + index * step
        x2 = left + (index + 1) * step
        canvas.create_rectangle(x1, top + 1, x2, top + 4, fill=SHADOW, outline="")
        color = gradient(BAR_STOPS, index / max(1, count - 1))
        canvas.create_rectangle(x1, top, x2, top + 3, fill=color, outline="")


def draw_glints(canvas, positions):
    glints = []
    for x, y, phase in positions:
        item = canvas.create_oval(
            x - 1.5, y - 1.5, x + 1.5, y + 1.5,
            fill=GLINT_COLOR, outline="",
        )
        glints.append((item, x, y, phase))
    return glints


def build(root):
    canvas = tk.Canvas(root, bg=KEY, highlightthickness=0, bd=0)

    tux_family = pick_font_family(root, ["Cascadia Mono", "Consolas", "Courier New"], "Courier New")
    title_family = pick_font_family(root, ["Bahnschrift SemiBold", "Segoe UI Semibold"], "Segoe UI")
    sub_family = pick_font_family(root, ["Segoe UI"], "Segoe UI")

    tux_font = tkfont.Font(root=root, family=tux_family, size=10)
    title_weight = "bold" if title_family == "Segoe UI" else "normal"
    title_font = tkfont.Font(root=root, family=title_family, size=14, weight=title_weight)
    sub_font = tkfont.Font(root=root, family=sub_family, size=9)

    char_width = tux_font.measure("M")
    line_height = tux_font.metrics("linespace")
    tux_width = max(sum(len(part) for part, _ in row) for row in TUX) * char_width
    tux_height = len(TUX) * line_height

    title_width = sum(title_font.measure(char) for char in TITLE)
    title_height = title_font.metrics("linespace")

    sub_width_limit = max(230, min(330, title_width + 40))
    sub_lines = wrap_text(SUBTITLE, sub_font, sub_width_limit)
    sub_width = max(sub_font.measure(line) for line in sub_lines)
    sub_height = sub_font.metrics("linespace")

    text_left = PAD + tux_width + 22
    text_width = max(title_width, sub_width)

    subtitle_offset = title_height + 6
    bar_offset = subtitle_offset + len(sub_lines) * sub_height + 10
    text_height = bar_offset + 3

    content_height = max(tux_height, text_height)
    width = text_left + text_width + PAD
    height = content_height + PAD * 2
    canvas.configure(width=width, height=height)

    tux_left = PAD
    tux_top = PAD + (content_height - tux_height) // 2
    draw_tux(canvas, tux_font, char_width, line_height, tux_left, tux_top)

    text_top = PAD + (content_height - text_height) // 2
    title_items = draw_title(canvas, title_font, TITLE, text_left, text_top)

    subtitle_top = text_top + subtitle_offset
    draw_subtitle(canvas, sub_font, sub_lines, sub_height, text_left, subtitle_top)

    draw_bar(canvas, text_left, text_top + bar_offset, text_width)

    glints = draw_glints(canvas, [
        (tux_left + 3, tux_top + 2, 0.0),
        (tux_left + tux_width + 9, tux_top + 16, 1.9),
        (tux_left + 2, tux_top + tux_height - 6, 3.4),
    ])

    canvas.pack()
    return canvas, title_items, glints


def animate(root, canvas, title_items, glints):
    start = time.time()
    count = max(1, len(TITLE))

    def tick():
        elapsed = time.time() - start
        phase = elapsed * 0.10
        for index, item in enumerate(title_items):
            canvas.itemconfigure(item, fill=gradient(TITLE_STOPS, index / count + phase))
        for item, x, y, offset in glints:
            radius = 1.4 + 1.1 * abs(math.sin(elapsed * 1.1 + offset))
            canvas.coords(item, x - radius, y - radius, x + radius, y + radius)
        root.after(80, tick)

    tick()


def main():
    enable_dpi_awareness()

    root = tk.Tk()
    root.title("Активация Linux")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-transparentcolor", KEY)
    root.configure(bg=KEY)

    canvas, title_items, glints = build(root)

    width = int(float(canvas["width"]))
    height = int(float(canvas["height"]))
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+{screen_width - width - 36}+{screen_height - height - 78}")

    root.after(90, lambda: set_click_through(root))
    root.after(150, root.focus_force)
    root.bind("<Escape>", lambda _event: root.destroy())
    root.bind_all("<Escape>", lambda _event: root.destroy())

    if "--seconds" in sys.argv:
        try:
            seconds = float(sys.argv[sys.argv.index("--seconds") + 1])
            root.after(int(seconds * 1000), root.destroy)
        except (IndexError, ValueError):
            pass

    animate(root, canvas, title_items, glints)
    root.mainloop()


if __name__ == "__main__":
    main()
