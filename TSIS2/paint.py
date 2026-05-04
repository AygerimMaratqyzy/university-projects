import pygame
import sys
import os
from datetime import datetime

from tools import (
    PencilTool, LineTool, RectTool, CircleTool,
    EraserTool, FillTool, TextTool,
)

#constants
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

#pygame init
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


#icon loading
def load_icon(path, size=(22, 22)):
    """
    Load a PNG icon, scale it to `size`, and return the Surface.
    If the file is missing, return None so the button falls back to text.

    pygame.image.load()  — reads the PNG from disk.
    convert_alpha()      — converts to display format with per-pixel alpha,
                           which is needed for transparent PNGs to render
                           correctly over coloured button backgrounds.
    pygame.transform.smoothscale() — resizes with anti-aliasing to the
                           requested (width, height) tuple.
    """
    if not os.path.isfile(path):
        return None
    raw = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(raw, size)


# Load the two icon PNGs from the assets folder.
# Icons are 50×50 px originals → scaled down to 22×22 for the toolbar.
ICON_SIZE = (22, 22)
icons = {
    "pencil": load_icon(os.path.join("assets", "pencil.png"), ICON_SIZE),
    "eraser": load_icon(os.path.join("assets", "eraser.png"), ICON_SIZE),
}


#button
class Button:
    """
    A rectangular toolbar button that can display:
      • text only  (icon=None)
      • icon + text side by side  (icon is a pygame.Surface)

    Parameters
    ----------
    x, y, w, h : int   — position and size in the toolbar
    label       : str  — text shown on / next to the button
    icon        : Surface | None — optional PNG icon Surface
    color       : tuple — default background colour
    """

    def __init__(self, x, y, w, h, label, icon=None, color=GRAY):
        self.rect   = pygame.Rect(x, y, w, h)
        self.label  = label
        self.icon   = icon       # pygame.Surface or None
        self.color  = color
        self.active = False      # True when this tool is selected

    def draw(self, surface):
        # Choose background: light-blue if active, else normal gray
        bg = LIGHT_BLUE if self.active else self.color
        pygame.draw.rect(surface, bg,        self.rect, border_radius=5)
        pygame.draw.rect(surface, DARK_GRAY, self.rect, 1, border_radius=5)

        if self.icon is not None:
            # Icon + text layout
            # Icon sits on the left with a small margin; text follows it.
            icon_x = self.rect.x + 5
            icon_y = self.rect.y + (self.rect.h - self.icon.get_height()) // 2
            surface.blit(self.icon, (icon_x, icon_y))          # draw icon

            text    = font.render(self.label, True, BLACK)
            text_x  = icon_x + self.icon.get_width() + 5       # right of icon
            text_y  = self.rect.y + (self.rect.h - text.get_height()) // 2
            surface.blit(text, (text_x, text_y))               # draw label
        else:
            #Text-only layout (centered) 
            text   = font.render(self.label, True, BLACK)
            text_x = self.rect.x + (self.rect.w - text.get_width())  // 2
            text_y = self.rect.y + (self.rect.h - text.get_height()) // 2
            surface.blit(text, (text_x, text_y))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


#build toolbar buttons
#
# Tool names match the keys in the TOOLS dict below.
# For "pencil" and "eraser" we pass the loaded icon Surface;
# all other buttons receive icon=None and show text only.
#
TOOL_NAMES = ["pencil", "line", "rect", "circle", "eraser", "fill", "text"]

BTN_X = 8        # left margin inside toolbar
BTN_W = 124      # button width
BTN_H = 32       # button height
BTN_GAP = 6      # vertical gap between buttons

def _make_tool_buttons():
    buttons = []
    labels = {
        "pencil": "Pencil",
        "line":   "Line",
        "rect":   "Rect",
        "circle": "Circle",
        "eraser": "Eraser",
        "fill":   "Fill",
        "text":   "Text",
    }
    for i, name in enumerate(TOOL_NAMES):
        y    = 10 + i * (BTN_H + BTN_GAP)
        icon = icons.get(name)          # None for tools without a PNG
        buttons.append(Button(BTN_X, y, BTN_W, BTN_H, labels[name], icon=icon))
    return buttons

tool_buttons = _make_tool_buttons()

# Clear button — text only, red tint
_clear_y = 10 + len(TOOL_NAMES) * (BTN_H + BTN_GAP) + 4
btn_clear = Button(BTN_X, _clear_y, BTN_W, BTN_H, "Clear", color=(255, 200, 200))

#tool instances
TOOLS = {
    "pencil": PencilTool(),
    "line":   LineTool(),
    "rect":   RectTool(),
    "circle": CircleTool(),
    "eraser": EraserTool(),
    "fill":   FillTool(),
    "text":   TextTool(),
}
#pallette drawing helpers
_PAL_Y0     = 330   # top of colour section in toolbar
_SWATCH_SZ  = 20
_SWATCH_GAP = 3
_PAL_COLS   = 4
_PAL_SX     = BTN_X


def draw_palette(surface, selected_color):
    """Draw the colour swatches grid and return geometry for hit-testing."""
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
    """Return the palette colour under `pos`, or None."""
    for i, color in enumerate(PALETTE):
        col  = i % _PAL_COLS
        row  = i // _PAL_COLS
        x    = _PAL_SX + col * (_SWATCH_SZ + _SWATCH_GAP)
        y    = _PAL_Y0 + 16 + row * (_SWATCH_SZ + _SWATCH_GAP)
        if pygame.Rect(x, y, _SWATCH_SZ, _SWATCH_SZ).collidepoint(pos):
            return color
    return None


#brush-size buttons
_SIZE_Y0 = 460

_size_rects = [
    pygame.Rect(BTN_X + (lvl - 1) * 42, _SIZE_Y0 + 16, 36, 24)
    for lvl in (1, 2, 3)
]


def draw_size_buttons(surface, size_level):
    """Draw three small buttons labelled 1 / 2 / 3 for brush thickness."""
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
    """Return 1/2/3 if a size button was clicked, else None."""
    for lvl, rect in zip((1, 2, 3), _size_rects):
        if rect.collidepoint(pos):
            return lvl
    return None

#current-color preview
_PREVIEW_Y0 = 500


def draw_color_preview(surface, color):
    lbl = font.render("Current:", True, BLACK)
    surface.blit(lbl, (BTN_X, _PREVIEW_Y0))
    pygame.draw.rect(surface, color,
                     (BTN_X, _PREVIEW_Y0 + 16, BTN_W, 22), border_radius=4)
    pygame.draw.rect(surface, DARK_GRAY,
                     (BTN_X, _PREVIEW_Y0 + 16, BTN_W, 22), 1, border_radius=4)


#keyboard-shortcut hints
def draw_hints(surface):
    hints = [
        "P Pencil  L Line",
        "R Rect    C Circle",
        "E Eraser  F Fill",
        "T Text",
        "1/2/3 Brush size",
        "Ctrl+S  Save PNG",
    ]
    y = SCREEN_HEIGHT - 14 * len(hints) - 4
    for h in hints:
        t = font_small.render(h, True, DARK_GRAY)
        surface.blit(t, (BTN_X, y))
        y += 14


#save canvas
def save_canvas():
    """
    Save the current canvas Surface as a PNG file.

    pygame.image.save(surface, filename) writes the pixels of `surface`
    directly to disk.  The datetime timestamp in the filename ensures each
    save creates a unique file (no overwriting).
    """
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"canvas_{ts}.png"
    pygame.image.save(canvas, filename)
    return filename
#main loop
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

    #Set default active button
    tool_buttons[TOOL_NAMES.index(current_tool)].active = True

    text_tool = TOOLS["text"]   # handy alias

    running = True
    while running:
        mouse_pos    = pygame.mouse.get_pos()
        # Translate screen coordinates → canvas-local coordinates
        canvas_mouse = (mouse_pos[0] - CANVAS_X, mouse_pos[1])
        on_canvas    = mouse_pos[0] >= CANVAS_X

        #event handling
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            # keyboard
            if event.type == pygame.KEYDOWN:

                # Text tool captures all keys while typing
                if current_tool == "text" and text_tool.active:
                    if text_tool.on_key(event, canvas, current_color):
                        continue

                # Quit
                if event.key == pygame.K_ESCAPE:
                    running = False

                # Ctrl+S → save
                if event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    fname    = save_canvas()
                    save_msg = f"Saved: {fname}"
                    save_msg_time = pygame.time.get_ticks()

                # Tool shortcuts
                _key_to_tool = {
                    pygame.K_p: "pencil",
                    pygame.K_l: "line",
                    pygame.K_r: "rect",
                    pygame.K_c: "circle",
                    pygame.K_e: "eraser",
                    pygame.K_f: "fill",
                    pygame.K_t: "text",
                }
                if event.key in _key_to_tool:
                    current_tool = _key_to_tool[event.key]

                # Brush-size shortcuts 1 / 2 / 3
                _key_to_size = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3}
                if event.key in _key_to_size:
                    size_level = _key_to_size[event.key]
                    brush_size = BRUSH_SIZES[size_level]

            #Mouse button down
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if not on_canvas:
                    #Toolbar clicks

                    # Tool buttons
                    for i, btn in enumerate(tool_buttons):
                        if btn.is_clicked(mouse_pos):
                            current_tool = TOOL_NAMES[i]

                    # Clear button
                    if btn_clear.is_clicked(mouse_pos):
                        canvas.fill(WHITE)

                    # Size buttons
                    lvl = get_size_click(mouse_pos)
                    if lvl is not None:
                        size_level = lvl
                        brush_size = BRUSH_SIZES[size_level]

                    # Colour swatches
                    clicked_color = get_swatch_click(mouse_pos)
                    if clicked_color is not None:
                        current_color = clicked_color

                else:
                    #canvas clicks

                    if current_tool == "text":
                        text_tool.on_canvas_click(canvas_mouse, current_color)

                    elif current_tool == "fill":
                        # Fill acts immediately on click; no drag needed
                        TOOLS["fill"].on_mouse_down(
                            canvas, canvas_mouse, current_color, brush_size)

                    else:
                        drawing   = True
                        start_pos = canvas_mouse
                        last_pos  = canvas_mouse
                        TOOLS[current_tool].on_mouse_down(
                            canvas, canvas_mouse, current_color, brush_size)

            #Mouse button up
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing:
                    TOOLS[current_tool].on_mouse_up(
                        canvas, start_pos, canvas_mouse, current_color, brush_size)
                    preview.fill((0, 0, 0, 0))   # clear ghost
                drawing   = False
                start_pos = None

            #Mouse motion
            if event.type == pygame.MOUSEMOTION and drawing and on_canvas:
                last_pos = TOOLS[current_tool].on_mouse_move(
                    canvas, preview, last_pos, canvas_mouse,
                    current_color, brush_size)
                # Ghost preview for shape tools
                if current_tool in ("line", "rect", "circle"):
                    TOOLS[current_tool].draw_preview(
                        preview, start_pos, canvas_mouse, current_color, brush_size)

        #Sync active-button highlights with current tool
        for i, btn in enumerate(tool_buttons):
            btn.active = (TOOL_NAMES[i] == current_tool)

        #render
        # Toolbar background
        screen.fill(PANEL_BG)
        # Thin vertical divider between toolbar and canvas
        pygame.draw.rect(screen, DIVIDER, (TOOLBAR_WIDTH - 1, 0, 1, SCREEN_HEIGHT))

        # Canvas (drawing surface) + ghost preview on top
        screen.blit(canvas,  (CANVAS_X, 0))
        screen.blit(preview, (CANVAS_X, 0))

        # All toolbar widgets
        for btn in tool_buttons:
            btn.draw(screen)
        btn_clear.draw(screen)

        draw_palette(screen, current_color)
        draw_size_buttons(screen, size_level)
        draw_color_preview(screen, current_color)
        draw_hints(screen)

        # Text tool: live character preview + blinking cursor
        if current_tool == "text":
            text_tool.draw_overlay(screen, current_color, CANVAS_X)

        # Custom cursor on canvas
        if on_canvas and not (current_tool == "text" and text_tool.active):
            TOOLS[current_tool].draw_cursor(screen, mouse_pos, current_color, brush_size)

        # "Saved!" feedback banner (fades after 3 s)
        if save_msg and pygame.time.get_ticks() - save_msg_time < 3000:
            msg = font.render(save_msg, True, (0, 130, 0))
            screen.blit(msg, (CANVAS_X + 8, 4))

        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()