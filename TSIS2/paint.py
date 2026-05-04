import pygame
import sys
import os
from datetime import datetime

from tools import (
    PencilTool, LineTool, RectTool, CircleTool,
    EraserTool, FillTool, TextTool,
    SquareTool, RightTriangleTool, EquilateralTriangleTool, RhombusTool,
)

# ── constants ─────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 920
SCREEN_HEIGHT = 640
TOOLBAR_WIDTH = 140          # Width of left toolbar panel
CANVAS_X      = TOOLBAR_WIDTH
FPS           = 60

# UI colours
WHITE      = (255, 255, 255)
BLACK      = (  0,   0,   0)
GRAY       = (210, 210, 215)
DARK_GRAY  = ( 80,  80,  85)
LIGHT_BLUE = (160, 210, 240)   # active-tool highlight
PANEL_BG   = (235, 235, 240)   # toolbar background
DIVIDER    = (170, 170, 175)

# Drawing colour palette
PALETTE = [
    (  0,   0,   0),   # Black
    (255, 255, 255),   # White
    (220,  50,  50),   # Red
    ( 50, 180,  50),   # Green
    ( 50,  80, 220),   # Blue
    (240, 220,  30),   # Yellow
    (240, 140,  20),   # Orange
    (150,  40, 200),   # Purple
    ( 30, 200, 200),   # Cyan
    (240, 100, 160),   # Pink
    (120,  70,  20),   # Brown
    (140, 140, 140),   # Gray
]

# Brush size presets  key → pixel radius
BRUSH_SIZES = {1: 1, 2: 3, 3: 6}

# ── pygame init ───────────────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Paint")
clock  = pygame.time.Clock()

font       = pygame.font.SysFont("Verdana", 10, bold=True)
font_small = pygame.font.SysFont("Verdana", 9)

# Drawing surface — toolbar never bleeds onto it
canvas  = pygame.Surface((SCREEN_WIDTH - TOOLBAR_WIDTH, SCREEN_HEIGHT))
canvas.fill(WHITE)

# Transparent overlay for shape ghost previews
preview = pygame.Surface((SCREEN_WIDTH - TOOLBAR_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)


# ── icon loading ──────────────────────────────────────────────────────────────
def load_icon(path, size=(22, 22)):
    """
    Load a PNG icon, scale it to `size`, and return the Surface.
    If the file is missing, return None so the button falls back to text.
    """
    if not os.path.isfile(path):
        return None
    raw = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(raw, size)


ICON_SIZE = (22, 22)
icons = {
    "pencil": load_icon(os.path.join("assets", "pencil.png"), ICON_SIZE),
    "eraser": load_icon(os.path.join("assets", "eraser.png"), ICON_SIZE),
}


# ── Button ────────────────────────────────────────────────────────────────────
class Button:
    """
    A rectangular toolbar button that can display:
      • text only  (icon=None)
      • icon + text side by side  (icon is a pygame.Surface)
    """

    def __init__(self, x, y, w, h, label, icon=None, color=GRAY):
        self.rect   = pygame.Rect(x, y, w, h)
        self.label  = label
        self.icon   = icon
        self.color  = color
        self.active = False

    def draw(self, surface):
        bg = LIGHT_BLUE if self.active else self.color
        pygame.draw.rect(surface, bg,        self.rect, border_radius=5)
        pygame.draw.rect(surface, DARK_GRAY, self.rect, 1, border_radius=5)

        if self.icon is not None:
            icon_x = self.rect.x + 5
            icon_y = self.rect.y + (self.rect.h - self.icon.get_height()) // 2
            surface.blit(self.icon, (icon_x, icon_y))
            text   = font.render(self.label, True, BLACK)
            text_x = icon_x + self.icon.get_width() + 5
            text_y = self.rect.y + (self.rect.h - text.get_height()) // 2
            surface.blit(text, (text_x, text_y))
        else:
            text   = font.render(self.label, True, BLACK)
            text_x = self.rect.x + (self.rect.w - text.get_width())  // 2
            text_y = self.rect.y + (self.rect.h - text.get_height()) // 2
            surface.blit(text, (text_x, text_y))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ── build toolbar buttons ─────────────────────────────────────────────────────
#
# Four new tools appended after the original seven.
# Keyboard shortcuts: Q=square, G=right-triangle, V=equilateral, H=rhombus
#
TOOL_NAMES = [
    "pencil", "line", "rect", "circle",
    "eraser", "fill", "text",
    "square", "rtriangle", "etriangle", "rhombus",
]

BTN_X   = 8
BTN_W   = 124
BTN_H   = 28    # slightly shorter to fit all 11 tools + clear button
BTN_GAP = 4

def _make_tool_buttons():
    labels = {
        "pencil":    "Pencil",
        "line":      "Line",
        "rect":      "Rect",
        "circle":    "Circle",
        "eraser":    "Eraser",
        "fill":      "Fill",
        "text":      "Text",
        "square":    "Square",
        "rtriangle": "Right Tri",
        "etriangle": "Equil Tri",
        "rhombus":   "Rhombus",
    }
    buttons = []
    for i, name in enumerate(TOOL_NAMES):
        y    = 10 + i * (BTN_H + BTN_GAP)
        icon = icons.get(name)
        buttons.append(Button(BTN_X, y, BTN_W, BTN_H, labels[name], icon=icon))
    return buttons

tool_buttons = _make_tool_buttons()

# Clear button — below all tool buttons
_clear_y = 10 + len(TOOL_NAMES) * (BTN_H + BTN_GAP) + 4
btn_clear = Button(BTN_X, _clear_y, BTN_W, BTN_H, "Clear", color=(255, 200, 200))

# ── tool instances ────────────────────────────────────────────────────────────
TOOLS = {
    "pencil":    PencilTool(),
    "line":      LineTool(),
    "rect":      RectTool(),
    "circle":    CircleTool(),
    "eraser":    EraserTool(),
    "fill":      FillTool(),
    "text":      TextTool(),
    "square":    SquareTool(),
    "rtriangle": RightTriangleTool(),
    "etriangle": EquilateralTriangleTool(),
    "rhombus":   RhombusTool(),
}

# ── palette drawing helpers ───────────────────────────────────────────────────
# Push palette lower to clear the taller tool list
_PAL_Y0     = 395
_SWATCH_SZ  = 20
_SWATCH_GAP = 3
_PAL_COLS   = 4
_PAL_SX     = BTN_X


def draw_palette(surface, selected_color):
    lbl = font.render("Colors:", True, BLACK)
    surface.blit(lbl, (BTN_X, _PAL_Y0))
    for i, color in enumerate(PALETTE):
        col  = i % _PAL_COLS
        row  = i // _PAL_COLS
        x    = _PAL_SX + col * (_SWATCH_SZ + _SWATCH_GAP)
        y    = _PAL_Y0 + 16 + row * (_SWATCH_SZ + _SWATCH_GAP)
        rect = pygame.Rect(x, y, _SWATCH_SZ, _SWATCH_SZ)
        pygame.draw.rect(surface, color, rect, border_radius=3)
        if color == selected_color:
            pygame.draw.rect(surface, WHITE, rect, 2, border_radius=3)
            pygame.draw.rect(surface, BLACK, rect, 1, border_radius=3)
        else:
            pygame.draw.rect(surface, DARK_GRAY, rect, 1, border_radius=3)


def get_swatch_click(pos):
    for i, color in enumerate(PALETTE):
        col  = i % _PAL_COLS
        row  = i // _PAL_COLS
        x    = _PAL_SX + col * (_SWATCH_SZ + _SWATCH_GAP)
        y    = _PAL_Y0 + 16 + row * (_SWATCH_SZ + _SWATCH_GAP)
        if pygame.Rect(x, y, _SWATCH_SZ, _SWATCH_SZ).collidepoint(pos):
            return color
    return None


# ── brush-size buttons ────────────────────────────────────────────────────────
_SIZE_Y0 = 525

_size_rects = [
    pygame.Rect(BTN_X + (lvl - 1) * 42, _SIZE_Y0 + 16, 36, 24)
    for lvl in (1, 2, 3)
]


def draw_size_buttons(surface, size_level):
    lbl = font.render("Size (1/2/3):", True, BLACK)
    surface.blit(lbl, (BTN_X, _SIZE_Y0))
    for lvl, rect in zip((1, 2, 3), _size_rects):
        bg = LIGHT_BLUE if lvl == size_level else GRAY
        pygame.draw.rect(surface, bg,        rect, border_radius=4)
        pygame.draw.rect(surface, DARK_GRAY, rect, 1, border_radius=4)
        t = font.render(str(lvl), True, BLACK)
        surface.blit(t, (rect.x + (rect.w - t.get_width()) // 2,
                         rect.y + (rect.h - t.get_height()) // 2))


def get_size_click(pos):
    for lvl, rect in zip((1, 2, 3), _size_rects):
        if rect.collidepoint(pos):
            return lvl
    return None


# ── current-color preview ─────────────────────────────────────────────────────
_PREVIEW_Y0 = 565


def draw_color_preview(surface, color):
    lbl = font.render("Current:", True, BLACK)
    surface.blit(lbl, (BTN_X, _PREVIEW_Y0))
    pygame.draw.rect(surface, color,
                     (BTN_X, _PREVIEW_Y0 + 16, BTN_W, 22), border_radius=4)
    pygame.draw.rect(surface, DARK_GRAY,
                     (BTN_X, _PREVIEW_Y0 + 16, BTN_W, 22), 1, border_radius=4)


# ── keyboard-shortcut hints ───────────────────────────────────────────────────
def draw_hints(surface):
    hints = [
        "P Pencil  L Line",
        "R Rect    C Circle",
        "E Eraser  F Fill",
        "T Text    Q Square",
        "G R.Tri   V E.Tri",
        "H Rhombus",
        "1/2/3 Brush size",
        "Ctrl+S  Save PNG",
    ]
    y = SCREEN_HEIGHT - 13 * len(hints) - 2
    for h in hints:
        t = font_small.render(h, True, DARK_GRAY)
        surface.blit(t, (BTN_X, y))
        y += 13


# ── save canvas ───────────────────────────────────────────────────────────────
def save_canvas():
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"canvas_{ts}.png"
    pygame.image.save(canvas, filename)
    return filename


# ── shape tools that use the preview ghost ────────────────────────────────────
PREVIEW_TOOLS = {"line", "rect", "circle", "square", "rtriangle", "etriangle", "rhombus"}


# ── main loop ─────────────────────────────────────────────────────────────────
def main():
    current_tool  = "pencil"
    current_color = BLACK
    size_level    = 2
    brush_size    = BRUSH_SIZES[size_level]

    drawing   = False
    start_pos = None
    last_pos  = None

    save_msg      = ""
    save_msg_time = 0

    tool_buttons[TOOL_NAMES.index(current_tool)].active = True

    text_tool = TOOLS["text"]

    running = True
    while running:
        mouse_pos    = pygame.mouse.get_pos()
        canvas_mouse = (mouse_pos[0] - CANVAS_X, mouse_pos[1])
        on_canvas    = mouse_pos[0] >= CANVAS_X

        # ── event handling ────────────────────────────────────────────────────
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            # keyboard
            if event.type == pygame.KEYDOWN:

                if current_tool == "text" and text_tool.active:
                    if text_tool.on_key(event, canvas, current_color):
                        continue

                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    fname    = save_canvas()
                    save_msg = f"Saved: {fname}"
                    save_msg_time = pygame.time.get_ticks()

                _key_to_tool = {
                    pygame.K_p: "pencil",
                    pygame.K_l: "line",
                    pygame.K_r: "rect",
                    pygame.K_c: "circle",
                    pygame.K_e: "eraser",
                    pygame.K_f: "fill",
                    pygame.K_t: "text",
                    pygame.K_q: "square",
                    pygame.K_g: "rtriangle",
                    pygame.K_v: "etriangle",
                    pygame.K_h: "rhombus",
                }
                if event.key in _key_to_tool:
                    current_tool = _key_to_tool[event.key]

                _key_to_size = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3}
                if event.key in _key_to_size:
                    size_level = _key_to_size[event.key]
                    brush_size = BRUSH_SIZES[size_level]

            # Mouse button down
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if not on_canvas:
                    for i, btn in enumerate(tool_buttons):
                        if btn.is_clicked(mouse_pos):
                            current_tool = TOOL_NAMES[i]

                    if btn_clear.is_clicked(mouse_pos):
                        canvas.fill(WHITE)

                    lvl = get_size_click(mouse_pos)
                    if lvl is not None:
                        size_level = lvl
                        brush_size = BRUSH_SIZES[size_level]

                    clicked_color = get_swatch_click(mouse_pos)
                    if clicked_color is not None:
                        current_color = clicked_color

                else:
                    if current_tool == "text":
                        text_tool.on_canvas_click(canvas_mouse, current_color)

                    elif current_tool == "fill":
                        TOOLS["fill"].on_mouse_down(
                            canvas, canvas_mouse, current_color, brush_size)

                    else:
                        drawing   = True
                        start_pos = canvas_mouse
                        last_pos  = canvas_mouse
                        TOOLS[current_tool].on_mouse_down(
                            canvas, canvas_mouse, current_color, brush_size)

            # Mouse button up
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing:
                    TOOLS[current_tool].on_mouse_up(
                        canvas, start_pos, canvas_mouse, current_color, brush_size)
                    preview.fill((0, 0, 0, 0))
                drawing   = False
                start_pos = None

            # Mouse motion
            if event.type == pygame.MOUSEMOTION and drawing and on_canvas:
                last_pos = TOOLS[current_tool].on_mouse_move(
                    canvas, preview, last_pos, canvas_mouse,
                    current_color, brush_size)
                if current_tool in PREVIEW_TOOLS:
                    TOOLS[current_tool].draw_preview(
                        preview, start_pos, canvas_mouse, current_color, brush_size)

        # ── sync active-button highlights ─────────────────────────────────────
        for i, btn in enumerate(tool_buttons):
            btn.active = (TOOL_NAMES[i] == current_tool)

        # ── render ────────────────────────────────────────────────────────────
        screen.fill(PANEL_BG)
        pygame.draw.rect(screen, DIVIDER, (TOOLBAR_WIDTH - 1, 0, 1, SCREEN_HEIGHT))

        screen.blit(canvas,  (CANVAS_X, 0))
        screen.blit(preview, (CANVAS_X, 0))

        for btn in tool_buttons:
            btn.draw(screen)
        btn_clear.draw(screen)

        draw_palette(screen, current_color)
        draw_size_buttons(screen, size_level)
        draw_color_preview(screen, current_color)
        draw_hints(screen)

        if current_tool == "text":
            text_tool.draw_overlay(screen, current_color, CANVAS_X)

        if on_canvas and not (current_tool == "text" and text_tool.active):
            TOOLS[current_tool].draw_cursor(screen, mouse_pos, current_color, brush_size)

        if save_msg and pygame.time.get_ticks() - save_msg_time < 3000:
            msg = font.render(save_msg, True, (0, 130, 0))
            screen.blit(msg, (CANVAS_X + 8, 4))

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()