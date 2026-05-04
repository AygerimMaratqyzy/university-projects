import pygame
import sys
import math   # needed for equilateral triangle height calculation

pygame.init()

# CONSTANTS
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
TOOLBAR_WIDTH = 120       # Width of the left toolbar panel
CANVAS_X      = TOOLBAR_WIDTH  # Canvas starts after toolbar
FPS           = 60

# COLOURS
WHITE      = (255, 255, 255)
BLACK      = (  0,   0,   0)
GRAY       = (200, 200, 200)
DARK_GRAY  = (100, 100, 100)
LIGHT_BLUE = (173, 216, 230)

# Colour palette available to the user
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

# DISPLAY
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Paint")
clock  = pygame.time.Clock()

# FONTS
font       = pygame.font.SysFont("Verdana", 11, bold=True)
font_small = pygame.font.SysFont("Verdana", 9)

# CANVAS SURFACE
# Drawing happens on this separate surface so the toolbar area is never affected
canvas = pygame.Surface((SCREEN_WIDTH - TOOLBAR_WIDTH, SCREEN_HEIGHT))
canvas.fill(WHITE)


# SHAPE HELPERS
def right_triangle_points(start, end):
    """
    Return the three vertices of a right triangle.
    The right angle is always at start_pos (top-left corner).
    - start = where the mouse was first pressed
    - end   = current mouse position

    Layout:
        start ──────── (end[0], start[1])
          |            /
          |           /
        (start[0], end[1])
    """
    x0, y0 = start
    x1, y1 = end
    return [
        (x0, y0),            # top-left  — the right-angle vertex
        (x1, y0),            # top-right
        (x0, y1),            # bottom-left
    ]


def equilateral_triangle_points(start, end):
    """
    Return the three vertices of an equilateral triangle.
    - The base runs horizontally from start to (end[0], start[1]).
    - The apex is centred above (or below) the base at height = base * sqrt(3)/2.
    - If the user drags downward the apex flips below the base.

    Math:
        base_len = |end[0] - start[0]|
        height   = base_len * sqrt(3) / 2   ← height of equilateral triangle
    """
    x0, y0 = start
    x1, y1 = end
    base_len = abs(x1 - x0)
    height   = int(base_len * math.sqrt(3) / 2)   # integer pixels

    # Base left and right x — always at y0
    bx_left  = min(x0, x1)
    bx_right = max(x0, x1)

    # Apex x is centred between the base endpoints
    apex_x = (bx_left + bx_right) // 2

    # Apex goes upward normally; downward if user dragged below start
    if y1 >= y0:
        apex_y = y0 - height   # above baseline
    else:
        apex_y = y0 + height   # below baseline (flipped)

    return [
        (bx_left,  y0),   # base left
        (bx_right, y0),   # base right
        (apex_x,   apex_y),  # apex
    ]


def rhombus_points(start, end):
    """
    Return the four vertices of a rhombus (diamond shape).
    The bounding box is defined by start (top-left) and end (bottom-right).
    The four vertices are the midpoints of each side of that bounding box:

        top-mid ──────────────────╮
          /                        \\
    left-mid                    right-mid
          \\                        /
        bot-mid ──────────────────╯
    """
    x0, y0 = start
    x1, y1 = end
    mid_x = (x0 + x1) // 2   # horizontal midpoint
    mid_y = (y0 + y1) // 2   # vertical midpoint
    return [
        (mid_x, y0),   # top-centre
        (x1,    mid_y),  # right-centre
        (mid_x, y1),   # bottom-centre
        (x0,    mid_y),  # left-centre
    ]


def square_rect(start, end):
    """
    Return (x, y, side, side) for a square whose side length equals
    the SMALLER of the width and height the user dragged, so it is
    always a perfect square regardless of drag direction.
    """
    x0, y0 = start
    x1, y1 = end
    # Use the smaller dimension so the shape is always square
    side = min(abs(x1 - x0), abs(y1 - y0))
    # Honour the drag direction (left/right and up/down)
    x = x0 if x1 >= x0 else x0 - side
    y = y0 if y1 >= y0 else y0 - side
    return pygame.Rect(x, y, side, side)


# BUTTON CLASS
class Button:
    def __init__(self, x, y, w, h, label, color=GRAY):
        self.rect   = pygame.Rect(x, y, w, h)
        self.label  = label
        self.color  = color    # Default background colour
        self.active = False    # True when this tool is currently selected

    def draw(self, surface):
        """Draw button; highlight with LIGHT_BLUE when it is the active tool."""
        bg = LIGHT_BLUE if self.active else self.color
        pygame.draw.rect(surface, bg,        self.rect, border_radius=4)
        pygame.draw.rect(surface, DARK_GRAY, self.rect, 2, border_radius=4)
        text = font.render(self.label, True, BLACK)
        # Centre the text label inside the button rectangle
        tx = self.rect.x + (self.rect.w - text.get_width())  // 2
        ty = self.rect.y + (self.rect.h - text.get_height()) // 2
        surface.blit(text, (tx, ty))

    def is_clicked(self, pos):
        """Return True if the given mouse position is inside this button."""
        return self.rect.collidepoint(pos)


# TOOLBAR BUTTONS
# Original tools
btn_pencil  = Button(10,  10, 100, 28, "Pencil")
btn_rect    = Button(10,  42, 100, 28, "Rectangle")
btn_circle  = Button(10,  74, 100, 28, "Circle")
btn_eraser  = Button(10, 106, 100, 28, "Eraser")

# Extra task buttons
btn_square  = Button(10, 138, 100, 28, "Square")        # Task 1
btn_rtri    = Button(10, 170, 100, 28, "R.Triangle")    # Task 2 — right triangle
btn_etri    = Button(10, 202, 100, 28, "Eq.Triangle")   # Task 3 — equilateral triangle
btn_rhombus = Button(10, 234, 100, 28, "Rhombus")       # Task 4

btn_clear   = Button(10, 272, 100, 28, "Clear", color=(255, 200, 200))

# All shape/drawing tool buttons (used to reset .active flags each frame)
tool_buttons = [btn_pencil, btn_rect, btn_circle, btn_eraser,
                btn_square, btn_rtri, btn_etri, btn_rhombus]


# PALETTE DRAWING
def draw_palette(surface, selected_color):
    """
    Draw the colour swatch grid in the toolbar.
    The currently selected colour gets a white+black border highlight.
    Returns (start_x, start_y, swatch_size, cols) for hit-testing.
    """
    label = font.render("Colors:", True, BLACK)
    surface.blit(label, (10, 315))

    swatch_size = 22
    cols        = 4      # 4 swatches per row
    start_x     = 8
    start_y     = 333

    for i, color in enumerate(PALETTE):
        col  = i % cols
        row  = i // cols
        x    = start_x + col * (swatch_size + 3)
        y    = start_y + row * (swatch_size + 3)
        rect = pygame.Rect(x, y, swatch_size, swatch_size)

        pygame.draw.rect(surface, color, rect, border_radius=3)

        # Highlight border for the active colour
        if color == selected_color:
            pygame.draw.rect(surface, WHITE, rect, 2, border_radius=3)
            pygame.draw.rect(surface, BLACK, rect, 1, border_radius=3)
        else:
            pygame.draw.rect(surface, DARK_GRAY, rect, 1, border_radius=3)

    return start_x, start_y, swatch_size, cols


def get_swatch_click(pos, start_x, start_y, swatch_size, cols):
    """
    Check whether a mouse click landed on any colour swatch.
    Returns the (R,G,B) colour tuple if hit, None otherwise.
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


# BRUSH SIZE INDICATOR
def draw_brush_size(surface, size):
    """Draw the brush-size label and the +/- adjustment buttons."""
    label = font.render(f"Size: {size}", True, BLACK)
    surface.blit(label, (10, 475))
    # Minus button
    pygame.draw.rect(surface, GRAY,      (10, 495, 30, 25), border_radius=3)
    pygame.draw.rect(surface, DARK_GRAY, (10, 495, 30, 25), 1, border_radius=3)
    surface.blit(font.render("-", True, BLACK), (20, 500))
    # Plus button
    pygame.draw.rect(surface, GRAY,      (50, 495, 30, 25), border_radius=3)
    pygame.draw.rect(surface, DARK_GRAY, (50, 495, 30, 25), 1, border_radius=3)
    surface.blit(font.render("+", True, BLACK), (58, 500))


# COLOUR PREVIEW
def draw_color_preview(surface, color):
    """Show a filled rectangle preview of the currently selected colour."""
    label = font.render("Current:", True, BLACK)
    surface.blit(label, (10, 530))
    pygame.draw.rect(surface, color,     (10, 548, 100, 28), border_radius=4)
    pygame.draw.rect(surface, DARK_GRAY, (10, 548, 100, 28), 2, border_radius=4)

# GHOST PREVIEW HELPER
def draw_ghost(preview_surf, tool, start, current, color, thickness):
    """
    Clear the preview surface and redraw the shape outline at its
    current drag position.  This gives the user live feedback while
    dragging without permanently marking the canvas.

    preview_surf — SRCALPHA surface overlaid on top of the canvas
    tool         — active tool name string
    start        — (x, y) where the drag began (canvas coords)
    current      — (x, y) current mouse position (canvas coords)
    color        — current drawing colour
    thickness    — brush_size value
    """
    # Clear previous ghost with full transparency
    preview_surf.fill((0, 0, 0, 0))

    # Ghost colour = current colour at 70% opacity so it looks like a preview
    ghost_color = (*color, 180)

    if tool == "rect":
        # Axis-aligned rectangle from start to current
        x = min(start[0], current[0])
        y = min(start[1], current[1])
        w = abs(current[0] - start[0])
        h = abs(current[1] - start[1])
        pygame.draw.rect(preview_surf, ghost_color, (x, y, w, h), thickness)

    elif tool == "circle":
        # Circle centred at start with radius = distance to current
        dx     = current[0] - start[0]
        dy     = current[1] - start[1]
        radius = int((dx**2 + dy**2) ** 0.5)
        if radius > 0:
            pygame.draw.circle(preview_surf, ghost_color, start, radius, thickness)

    elif tool == "square":
        # Perfect square — side = min(width, height) of drag bounding box
        rect = square_rect(start, current)
        pygame.draw.rect(preview_surf, ghost_color, rect, thickness)

    elif tool == "rtri":
        # Right triangle — right angle at start
        pts = right_triangle_points(start, current)
        pygame.draw.polygon(preview_surf, ghost_color, pts, thickness)

    elif tool == "etri":
        # Equilateral triangle — base from start-x to current-x
        pts = equilateral_triangle_points(start, current)
        pygame.draw.polygon(preview_surf, ghost_color, pts, thickness)

    elif tool == "rhombus":
        # Rhombus — vertices at midpoints of bounding box sides
        pts = rhombus_points(start, current)
        pygame.draw.polygon(preview_surf, ghost_color, pts, thickness)

# FINALISE SHAPE ONTO CANVAS
def finalise_shape(canvas_surf, tool, start, end, color, thickness):
    """
    Commit the completed shape permanently to the canvas surface.
    Called when the mouse button is released.

    canvas_surf — the drawing canvas (not the screen)
    tool        — active tool name
    start / end — drag start and end in canvas coordinates
    color       — drawing colour
    thickness   — brush_size (0 = filled shape; >0 = outline only)
    """
    if tool == "rect":
        x = min(start[0], end[0])
        y = min(start[1], end[1])
        w = abs(end[0] - start[0])
        h = abs(end[1] - start[1])
        pygame.draw.rect(canvas_surf, color, (x, y, w, h), thickness)

    elif tool == "circle":
        dx     = end[0] - start[0]
        dy     = end[1] - start[1]
        radius = int((dx**2 + dy**2) ** 0.5)
        if radius > 0:
            pygame.draw.circle(canvas_surf, color, start, radius, thickness)

    elif tool == "square":
        # Task 1 — perfect square using helper
        rect = square_rect(start, end)
        pygame.draw.rect(canvas_surf, color, rect, thickness)

    elif tool == "rtri":
        # Task 2 — right triangle using helper
        pts = right_triangle_points(start, end)
        pygame.draw.polygon(canvas_surf, color, pts, thickness)

    elif tool == "etri":
        # Task 3 — equilateral triangle using helper
        pts = equilateral_triangle_points(start, end)
        pygame.draw.polygon(canvas_surf, color, pts, thickness)

    elif tool == "rhombus":
        # Task 4 — rhombus using helper
        pts = rhombus_points(start, end)
        pygame.draw.polygon(canvas_surf, color, pts, thickness)


# MAIN APPLICATION LOOP
def main():
    #State variables
    current_tool  = "pencil"  # Which tool is currently active
    current_color = BLACK     # Current drawing colour
    brush_size    = 5         # Radius / thickness in pixels

    drawing   = False   # True while the left mouse button is held down
    start_pos = None    # Canvas-coord position where the drag began
    last_pos  = None    # Previous mouse position (used for pencil trail)

    # Preview surface (SRCALPHA = supports transparency) layered on top of
    # the canvas so ghost outlines don't permanently mark the drawing
    preview = pygame.Surface((SCREEN_WIDTH - TOOLBAR_WIDTH, SCREEN_HEIGHT),
                              pygame.SRCALPHA)

    # Pencil is selected by default
    btn_pencil.active = True

    #Event / Render Loop
    while True:
        mouse_pos    = pygame.mouse.get_pos()
        # Translate screen coordinates to canvas-local coordinates
        # by subtracting the toolbar width from the x component
        canvas_mouse = (mouse_pos[0] - CANVAS_X, mouse_pos[1])

        #Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_p: current_tool = "pencil"
                if event.key == pygame.K_r: current_tool = "rect"
                if event.key == pygame.K_c: current_tool = "circle"
                if event.key == pygame.K_e: current_tool = "eraser"
                if event.key == pygame.K_s: current_tool = "square"    # Task 1
                if event.key == pygame.K_t: current_tool = "rtri"      # Task 2
                if event.key == pygame.K_g: current_tool = "etri"      # Task 3
                if event.key == pygame.K_h: current_tool = "rhombus"   # Task 4

            # Mouse button pressed
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if mouse_pos[0] < TOOLBAR_WIDTH:
                    # Toolbar click
                    # Original tools
                    if   btn_pencil.is_clicked(mouse_pos):  current_tool = "pencil"
                    elif btn_rect.is_clicked(mouse_pos):    current_tool = "rect"
                    elif btn_circle.is_clicked(mouse_pos):  current_tool = "circle"
                    elif btn_eraser.is_clicked(mouse_pos):  current_tool = "eraser"
                    # New shape tools
                    elif btn_square.is_clicked(mouse_pos):  current_tool = "square"   # Task 1
                    elif btn_rtri.is_clicked(mouse_pos):    current_tool = "rtri"     # Task 2
                    elif btn_etri.is_clicked(mouse_pos):    current_tool = "etri"     # Task 3
                    elif btn_rhombus.is_clicked(mouse_pos): current_tool = "rhombus"  # Task 4
                    elif btn_clear.is_clicked(mouse_pos):   canvas.fill(WHITE)        # Wipe canvas

                    # Brush size ± buttons
                    if pygame.Rect(10, 495, 30, 25).collidepoint(mouse_pos):
                        brush_size = max(1, brush_size - 1)   # minimum 1 px
                    if pygame.Rect(50, 495, 30, 25).collidepoint(mouse_pos):
                        brush_size = min(50, brush_size + 1)  # maximum 50 px

                    # Colour swatch click
                    clicked_color = get_swatch_click(mouse_pos, 8, 333, 22, 4)
                    if clicked_color is not None:
                        current_color = clicked_color

                else:
                    # Canvas click — begin drawing
                    drawing   = True
                    start_pos = canvas_mouse
                    last_pos  = canvas_mouse

                    # Pencil and eraser place a dot immediately on click
                    if current_tool == "pencil":
                        pygame.draw.circle(canvas, current_color,
                                           canvas_mouse, brush_size)
                    elif current_tool == "eraser":
                        pygame.draw.circle(canvas, WHITE,
                                           canvas_mouse, brush_size * 2)

            # Mouse button released
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drawing and start_pos and mouse_pos[0] >= TOOLBAR_WIDTH:
                    # Commit the completed shape to the canvas permanently
                    finalise_shape(canvas, current_tool,
                                   start_pos, canvas_mouse,
                                   current_color, brush_size)

                drawing   = False
                start_pos = None
                # Clear ghost preview — fill with fully transparent pixels
                preview.fill((0, 0, 0, 0))

            # Mouse motion
            if event.type == pygame.MOUSEMOTION and drawing:
                if mouse_pos[0] >= TOOLBAR_WIDTH:

                    if current_tool == "pencil":
                        # Draw a line from the previous position to the current one
                        # for a smooth continuous stroke, then cap with a circle
                        pygame.draw.line(canvas, current_color,
                                         last_pos, canvas_mouse, brush_size * 2)
                        pygame.draw.circle(canvas, current_color,
                                           canvas_mouse, brush_size)

                    elif current_tool == "eraser":
                        # Erase by painting white under the cursor
                        pygame.draw.circle(canvas, WHITE,
                                           canvas_mouse, brush_size * 2)

                    else:
                        # All shape tools — update the live ghost preview
                        draw_ghost(preview, current_tool,
                                   start_pos, canvas_mouse,
                                   current_color, brush_size)

                    last_pos = canvas_mouse   # remember position for next frame

        #Update which toolbar button appears highlighted
        btn_map = {
            "pencil": btn_pencil, "rect": btn_rect,
            "circle": btn_circle, "eraser": btn_eraser,
            "square": btn_square, "rtri": btn_rtri,
            "etri": btn_etri,     "rhombus": btn_rhombus,
        }
        for btn in tool_buttons:
            btn.active = False
        if current_tool in btn_map:
            btn_map[current_tool].active = True

        #Render

        # 1. Toolbar background
        screen.fill(GRAY)
        pygame.draw.rect(screen, DARK_GRAY,
                         (TOOLBAR_WIDTH - 2, 0, 2, SCREEN_HEIGHT))  # Divider

        # 2. Canvas + ghost preview (ghost is transparent, layered on top)
        screen.blit(canvas,   (CANVAS_X, 0))
        screen.blit(preview,  (CANVAS_X, 0))

        # 3. Toolbar widgets
        for btn in tool_buttons:
            btn.draw(screen)
        btn_clear.draw(screen)
        draw_palette(screen, current_color)
        draw_brush_size(screen, brush_size)
        draw_color_preview(screen, current_color)

        # 4. Cursor overlay — visual feedback for eraser and pencil
        if current_tool == "eraser" and mouse_pos[0] >= CANVAS_X:
            # Eraser cursor: white circle with black outline
            pygame.draw.circle(screen, BLACK, mouse_pos, brush_size * 2, 1)
        if current_tool == "pencil" and mouse_pos[0] >= CANVAS_X:
            # Pencil cursor: coloured ring at current size
            pygame.draw.circle(screen, current_color, mouse_pos, brush_size, 1)

        # 5. Keyboard shortcut hints at the bottom of the toolbar
        hints = ["P-Pencil", "R-Rect", "C-Circle",
                 "E-Eraser", "S-Square", "T-RTri",
                 "G-EqTri",  "H-Rhombus"]
        for i, hint in enumerate(hints):
            t = font_small.render(hint, True, DARK_GRAY)
            screen.blit(t, (5, 410 + i * 11))

        pygame.display.update()
        clock.tick(FPS)


main()