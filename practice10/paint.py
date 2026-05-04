import pygame
import sys

pygame.init()

# ── Constants ──────────────────────────────────────────────
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
TOOLBAR_WIDTH = 120       # Width of the left toolbar panel
CANVAS_X      = TOOLBAR_WIDTH  # Canvas starts after toolbar
FPS           = 60

# ── Colors ─────────────────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (  0,   0,   0)
GRAY       = (200, 200, 200)
DARK_GRAY  = (100, 100, 100)
LIGHT_BLUE = (173, 216, 230)

# ── Color palette available to the user ───────────────────
PALETTE = [
    (  0,   0,   0),   # Black
    (255, 255, 255),   # White
    (255,   0,   0),   # Red
    (  0, 255,   0),   # Green
    (  0,   0, 255),   # Blue
    (255, 255,   0),   # Yellow
    (255, 165,   0),   # Orange
    (128,   0, 128),   # Purple
    (  0, 255, 255),   # Cyan
    (255, 105, 180),   # Pink
    (139,  69,  19),   # Brown
    (128, 128, 128),   # Gray
]

# ── Display ────────────────────────────────────────────────
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Paint")
clock  = pygame.time.Clock()

# ── Fonts ──────────────────────────────────────────────────
font       = pygame.font.SysFont("Verdana", 11, bold=True)
font_small = pygame.font.SysFont("Verdana", 9)

# ── Canvas surface (separate from screen) ─────────────────
# Drawing happens on this surface so toolbar stays clean
canvas = pygame.Surface((SCREEN_WIDTH - TOOLBAR_WIDTH, SCREEN_HEIGHT))
canvas.fill(WHITE)


# ── Button class ───────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, label, color=GRAY):
        self.rect  = pygame.Rect(x, y, w, h)
        self.label = label
        self.color = color        # Background color of button
        self.active = False       # Whether this tool is currently selected

    def draw(self, surface):
        # Highlight active tool with light blue background
        bg = LIGHT_BLUE if self.active else self.color
        pygame.draw.rect(surface, bg, self.rect, border_radius=4)
        pygame.draw.rect(surface, DARK_GRAY, self.rect, 2, border_radius=4)
        text = font.render(self.label, True, BLACK)
        # Center text inside button
        tx = self.rect.x + (self.rect.w - text.get_width())  // 2
        ty = self.rect.y + (self.rect.h - text.get_height()) // 2
        surface.blit(text, (tx, ty))

    def is_clicked(self, pos):
        """Returns True if the given mouse position is inside this button."""
        return self.rect.collidepoint(pos)


# ── Tool buttons (left toolbar) ────────────────────────────
btn_pencil = Button(10, 10,  100, 30, "Pencil")
btn_rect   = Button(10, 50,  100, 30, "Rectangle")
btn_circle = Button(10, 90,  100, 30, "Circle")
btn_eraser = Button(10, 130, 100, 30, "Eraser")
btn_clear  = Button(10, 180, 100, 30, "Clear", color=(255, 200, 200))

tool_buttons = [btn_pencil, btn_rect, btn_circle, btn_eraser]


# ── Color swatches ─────────────────────────────────────────
def draw_palette(surface, selected_color):
    """
    Draw a grid of color swatches in the toolbar.
    Highlights the currently selected color with a white border.
    """
    label = font.render("Colors:", True, BLACK)
    surface.blit(label, (10, 230))

    swatch_size = 22
    cols        = 4    # 4 swatches per row
    start_x     = 8
    start_y     = 250

    for i, color in enumerate(PALETTE):
        col = i % cols
        row = i // cols
        x   = start_x + col * (swatch_size + 3)
        y   = start_y + row * (swatch_size + 3)
        rect = pygame.Rect(x, y, swatch_size, swatch_size)

        pygame.draw.rect(surface, color, rect, border_radius=3)

        # Draw highlight border around selected color
        if color == selected_color:
            pygame.draw.rect(surface, WHITE, rect, 2, border_radius=3)
            pygame.draw.rect(surface, BLACK, rect, 1, border_radius=3)
        else:
            pygame.draw.rect(surface, DARK_GRAY, rect, 1, border_radius=3)

    return start_x, start_y, swatch_size, cols


def get_swatch_click(pos, start_x, start_y, swatch_size, cols):
    """
    Check if a mouse click landed on any color swatch.
    Returns the color if clicked, None otherwise.
    """
    for i, color in enumerate(PALETTE):
        col  = i % cols
        row  = i // cols
        x    = start_x + col * (swatch_size + 3)
        y    = start_y + row * (swatch_size + 3)
        rect = pygame.Rect(x, y, swatch_size, swatch_size)
        if rect.collidepoint(pos):
            return color
    return None


# ── Draw brush size indicator ──────────────────────────────
def draw_brush_size(surface, size):
    """Show current brush size and +/- buttons."""
    label = font.render(f"Size: {size}", True, BLACK)
    surface.blit(label, (10, 390))
    # Minus button
    pygame.draw.rect(surface, GRAY, (10,  415, 30, 25), border_radius=3)
    pygame.draw.rect(surface, DARK_GRAY, (10, 415, 30, 25), 1, border_radius=3)
    surface.blit(font.render("-", True, BLACK), (20, 420))
    # Plus button
    pygame.draw.rect(surface, GRAY, (50,  415, 30, 25), border_radius=3)
    pygame.draw.rect(surface, DARK_GRAY, (50, 415, 30, 25), 1, border_radius=3)
    surface.blit(font.render("+", True, BLACK), (58, 420))


# ── Draw current color preview ─────────────────────────────
def draw_color_preview(surface, color):
    """Show a preview box of the currently selected drawing color."""
    label = font.render("Current:", True, BLACK)
    surface.blit(label, (10, 460))
    pygame.draw.rect(surface, color,      (10, 478, 100, 30), border_radius=4)
    pygame.draw.rect(surface, DARK_GRAY,  (10, 478, 100, 30), 2, border_radius=4)


# ── Main application ───────────────────────────────────────
def main():
    # ── State variables ────────────────────────────────────
    current_tool  = "pencil"   # Active drawing tool
    current_color = BLACK      # Active drawing color
    brush_size    = 5          # Brush/pen radius in pixels

    drawing       = False      # True while mouse button is held
    start_pos     = None       # Where the mouse was first pressed (for shapes)
    last_pos      = None       # Previous mouse position (for pencil trail)

    # Preview surface for shape ghost while dragging
    # (shows shape outline before releasing mouse)
    preview = pygame.Surface((SCREEN_WIDTH - TOOLBAR_WIDTH, SCREEN_HEIGHT),
                              pygame.SRCALPHA)

    # Set pencil as default active tool
    btn_pencil.active = True

    while True:
        mouse_pos    = pygame.mouse.get_pos()
        # Offset mouse position relative to canvas (subtract toolbar width)
        canvas_mouse = (mouse_pos[0] - CANVAS_X, mouse_pos[1])

        # ── Events ─────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ── Key shortcuts ───────────────────────────────
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                # Switch tools with keyboard shortcuts
                if event.key == pygame.K_p:
                    current_tool = "pencil"
                if event.key == pygame.K_r:
                    current_tool = "rect"
                if event.key == pygame.K_c:
                    current_tool = "circle"
                if event.key == pygame.K_e:
                    current_tool = "eraser"

            # ── Mouse button pressed ────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check toolbar button clicks
                if mouse_pos[0] < TOOLBAR_WIDTH:

                    # Tool button clicks
                    if btn_pencil.is_clicked(mouse_pos):
                        current_tool = "pencil"
                    elif btn_rect.is_clicked(mouse_pos):
                        current_tool = "rect"
                    elif btn_circle.is_clicked(mouse_pos):
                        current_tool = "circle"
                    elif btn_eraser.is_clicked(mouse_pos):
                        current_tool = "eraser"
                    elif btn_clear.is_clicked(mouse_pos):
                        # Clear entire canvas back to white
                        canvas.fill(WHITE)

                    # Brush size buttons
                    minus_rect = pygame.Rect(10, 415, 30, 25)
                    plus_rect  = pygame.Rect(50, 415, 30, 25)
                    if minus_rect.collidepoint(mouse_pos):
                        brush_size = max(1, brush_size - 1)
                    if plus_rect.collidepoint(mouse_pos):
                        brush_size = min(50, brush_size + 1)

                    # Color swatch clicks
                    swatch_x, swatch_y, swatch_size, cols = 8, 250, 22, 4
                    clicked_color = get_swatch_click(
                        mouse_pos, swatch_x, swatch_y, swatch_size, cols)
                    if clicked_color is not None:
                        current_color = clicked_color

                else:
                    # Click is on the canvas — start drawing
                    drawing   = True
                    start_pos = canvas_mouse
                    last_pos  = canvas_mouse

                    # Pencil/eraser start dot on click
                    if current_tool == "pencil":
                        pygame.draw.circle(canvas, current_color,
                                           canvas_mouse, brush_size)
                    elif current_tool == "eraser":
                        pygame.draw.circle(canvas, WHITE,
                                           canvas_mouse, brush_size * 2)

            # ── Mouse button released ───────────────────────
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing and start_pos and mouse_pos[0] >= TOOLBAR_WIDTH:

                    # Finalize rectangle onto canvas
                    if current_tool == "rect":
                        x = min(start_pos[0], canvas_mouse[0])
                        y = min(start_pos[1], canvas_mouse[1])
                        w = abs(canvas_mouse[0] - start_pos[0])
                        h = abs(canvas_mouse[1] - start_pos[1])
                        pygame.draw.rect(canvas, current_color,
                                         (x, y, w, h), brush_size)

                    # Finalize circle onto canvas
                    elif current_tool == "circle":
                        dx     = canvas_mouse[0] - start_pos[0]
                        dy     = canvas_mouse[1] - start_pos[1]
                        radius = int((dx**2 + dy**2) ** 0.5)  # Distance formula
                        if radius > 0:
                            pygame.draw.circle(canvas, current_color,
                                               start_pos, radius, brush_size)

                drawing   = False
                start_pos = None
                preview.fill((0, 0, 0, 0))  # Clear the ghost preview

            # ── Mouse movement ──────────────────────────────
            if event.type == pygame.MOUSEMOTION and drawing:
                if mouse_pos[0] >= TOOLBAR_WIDTH:

                    # Pencil — draw continuous line between last and current pos
                    if current_tool == "pencil":
                        pygame.draw.line(canvas, current_color,
                                         last_pos, canvas_mouse, brush_size * 2)
                        pygame.draw.circle(canvas, current_color,
                                           canvas_mouse, brush_size)

                    # Eraser — erase with white circle
                    elif current_tool == "eraser":
                        pygame.draw.circle(canvas, WHITE,
                                           canvas_mouse, brush_size * 2)

                    # Rectangle/Circle — update ghost preview on preview surface
                    elif current_tool in ("rect", "circle"):
                        preview.fill((0, 0, 0, 0))   # Clear previous ghost
                        if current_tool == "rect":
                            x = min(start_pos[0], canvas_mouse[0])
                            y = min(start_pos[1], canvas_mouse[1])
                            w = abs(canvas_mouse[0] - start_pos[0])
                            h = abs(canvas_mouse[1] - start_pos[1])
                            pygame.draw.rect(preview, (*current_color, 180),
                                             (x, y, w, h), brush_size)
                        elif current_tool == "circle":
                            dx     = canvas_mouse[0] - start_pos[0]
                            dy     = canvas_mouse[1] - start_pos[1]
                            radius = int((dx**2 + dy**2) ** 0.5)
                            if radius > 0:
                                pygame.draw.circle(preview,
                                                   (*current_color, 180),
                                                   start_pos, radius, brush_size)

                    last_pos = canvas_mouse

        # ── Update active tool button highlights ────────────
        for btn in tool_buttons:
            btn.active = False
        if current_tool == "pencil": btn_pencil.active = True
        if current_tool == "rect":   btn_rect.active   = True
        if current_tool == "circle": btn_circle.active = True
        if current_tool == "eraser": btn_eraser.active = True

        # ── Draw everything ─────────────────────────────────

        # Draw toolbar background
        screen.fill(GRAY)
        pygame.draw.rect(screen, DARK_GRAY,
                         (TOOLBAR_WIDTH - 2, 0, 2, SCREEN_HEIGHT))  # Divider line

        # Draw canvas onto screen
        screen.blit(canvas,   (CANVAS_X, 0))
        screen.blit(preview,  (CANVAS_X, 0))   # Ghost preview on top

        # Draw all toolbar elements
        for btn in tool_buttons:
            btn.draw(screen)
        btn_clear.draw(screen)

        # Draw palette, brush size, and color preview in toolbar
        sx, sy, ss, sc = draw_palette(screen, current_color)
        draw_brush_size(screen, brush_size)
        draw_color_preview(screen, current_color)

        # Draw eraser cursor (white circle outline at mouse position)
        if current_tool == "eraser" and mouse_pos[0] >= CANVAS_X:
            pygame.draw.circle(screen, BLACK, mouse_pos, brush_size * 2, 1)

        # Draw pencil cursor dot
        if current_tool == "pencil" and mouse_pos[0] >= CANVAS_X:
            pygame.draw.circle(screen, current_color, mouse_pos, brush_size, 1)

        # Keyboard shortcut hints at bottom of toolbar
        hints = ["P - Pencil", "R - Rect", "C - Circle", "E - Eraser"]
        for i, hint in enumerate(hints):
            t = font_small.render(hint, True, DARK_GRAY)
            screen.blit(t, (8, 530 + i * 12))

        pygame.display.update()
        clock.tick(FPS)


main()