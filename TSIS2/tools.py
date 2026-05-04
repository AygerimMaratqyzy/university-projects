import pygame
from collections import deque


WHITE = (255, 255, 255)


#pencil tool
class PencilTool:
    """Freehand drawing tool. Draws continuously while mouse is held."""

    def on_mouse_down(self, canvas, pos, color, size):
        pygame.draw.circle(canvas, color, pos, size)

    def on_mouse_move(self, canvas, preview, last_pos, pos, color, size):
        pygame.draw.line(canvas, color, last_pos, pos, size * 2)
        pygame.draw.circle(canvas, color, pos, size)
        return pos

    def on_mouse_up(self, canvas, start_pos, end_pos, color, size):
        pass

    def draw_preview(self, preview, start_pos, end_pos, color, size):
        pass

    def draw_cursor(self, surface, pos, color, size):
        pygame.draw.circle(surface, color, pos, size, 1)


#line tool
class LineTool:
    """Straight line: click start, drag, release to finalize."""

    def on_mouse_down(self, canvas, pos, color, size):
        pass

    def on_mouse_move(self, canvas, preview, last_pos, pos, color, size):
        return pos

    def on_mouse_up(self, canvas, start_pos, end_pos, color, size):
        if start_pos and end_pos:
            pygame.draw.line(canvas, color, start_pos, end_pos, size * 2)

    def draw_preview(self, preview, start_pos, end_pos, color, size):
        preview.fill((0, 0, 0, 0))
        if start_pos and end_pos:
            pygame.draw.line(preview, (*color, 180), start_pos, end_pos, size * 2)

    def draw_cursor(self, surface, pos, color, size):
        pygame.draw.line(surface, color, (pos[0] - 8, pos[1]), (pos[0] + 8, pos[1]), 1)
        pygame.draw.line(surface, color, (pos[0], pos[1] - 8), (pos[0], pos[1] + 8), 1)


#rectangle tool
class RectTool:
    """Rectangle: click-drag to define bounding box, release to draw."""

    def on_mouse_down(self, canvas, pos, color, size):
        pass

    def on_mouse_move(self, canvas, preview, last_pos, pos, color, size):
        return pos

    def on_mouse_up(self, canvas, start_pos, end_pos, color, size):
        if start_pos and end_pos:
            x = min(start_pos[0], end_pos[0])
            y = min(start_pos[1], end_pos[1])
            w = abs(end_pos[0] - start_pos[0])
            h = abs(end_pos[1] - start_pos[1])
            pygame.draw.rect(canvas, color, (x, y, w, h), size)

    def draw_preview(self, preview, start_pos, end_pos, color, size):
        preview.fill((0, 0, 0, 0))
        if start_pos and end_pos:
            x = min(start_pos[0], end_pos[0])
            y = min(start_pos[1], end_pos[1])
            w = abs(end_pos[0] - start_pos[0])
            h = abs(end_pos[1] - start_pos[1])
            pygame.draw.rect(preview, (*color, 180), (x, y, w, h), size)

    def draw_cursor(self, surface, pos, color, size):
        pygame.draw.line(surface, color, (pos[0] - 8, pos[1]), (pos[0] + 8, pos[1]), 1)
        pygame.draw.line(surface, color, (pos[0], pos[1] - 8), (pos[0], pos[1] + 8), 1)


#circle tool
class CircleTool:
    """Circle: center = start click, radius = distance to release point."""

    def on_mouse_down(self, canvas, pos, color, size):
        pass

    def on_mouse_move(self, canvas, preview, last_pos, pos, color, size):
        return pos

    def on_mouse_up(self, canvas, start_pos, end_pos, color, size):
        if start_pos and end_pos:
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            radius = int((dx ** 2 + dy ** 2) ** 0.5)
            if radius > 0:
                pygame.draw.circle(canvas, color, start_pos, radius, size)

    def draw_preview(self, preview, start_pos, end_pos, color, size):
        preview.fill((0, 0, 0, 0))
        if start_pos and end_pos:
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            radius = int((dx ** 2 + dy ** 2) ** 0.5)
            if radius > 0:
                pygame.draw.circle(preview, (*color, 180), start_pos, radius, size)

    def draw_cursor(self, surface, pos, color, size):
        pygame.draw.circle(surface, color, pos, 6, 1)

#eraser tool
class EraserTool:
    """Erases by painting white circles along the cursor path."""

    def on_mouse_down(self, canvas, pos, color, size):
        pygame.draw.circle(canvas, WHITE, pos, size * 2)

    def on_mouse_move(self, canvas, preview, last_pos, pos, color, size):
        pygame.draw.circle(canvas, WHITE, pos, size * 2)
        return pos

    def on_mouse_up(self, canvas, start_pos, end_pos, color, size):
        pass

    def draw_preview(self, preview, start_pos, end_pos, color, size):
        pass

    def draw_cursor(self, surface, pos, color, size):
        pygame.draw.circle(surface, (0, 0, 0), pos, size * 2, 1)


#flood fill tool
class FillTool:
    """
    Flood-fill using BFS over canvas pixels.
    Fills connected region of the same color with the selected color.
    """

    def on_mouse_down(self, canvas, pos, color, size):
        self._flood_fill(canvas, pos, color)

    def on_mouse_move(self, canvas, preview, last_pos, pos, color, size):
        return pos

    def on_mouse_up(self, canvas, start_pos, end_pos, color, size):
        pass

    def draw_preview(self, preview, start_pos, end_pos, color, size):
        pass

    def draw_cursor(self, surface, pos, color, size):
        pygame.draw.circle(surface, color, pos, 4, 1)
        pygame.draw.line(surface, color, (pos[0] - 10, pos[1]), (pos[0] + 10, pos[1]), 1)
        pygame.draw.line(surface, color, (pos[0], pos[1] - 10), (pos[0], pos[1] + 10), 1)

    @staticmethod
    def _flood_fill(canvas, pos, new_color):
        width, height = canvas.get_size()
        x, y = pos
        if x < 0 or x >= width or y < 0 or y >= height:
            return
        target_color = canvas.get_at((x, y))[:3]
        if target_color == new_color:
            return
        queue = deque()
        queue.append((x, y))
        visited = set()
        visited.add((x, y))
        while queue:
            cx, cy = queue.popleft()
            canvas.set_at((cx, cy), new_color)
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if (nx, ny) not in visited and 0 <= nx < width and 0 <= ny < height:
                    if canvas.get_at((nx, ny))[:3] == target_color:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

#text tool
class TextTool:
    """
    Click to place cursor, type characters, Enter to commit, Escape to cancel.
    """

    def __init__(self):
        self.active     = False
        self.text       = ""
        self.cursor_pos = None
        self.font       = pygame.font.SysFont("Verdana", 20)

    def on_canvas_click(self, pos, color):
        self.active     = True
        self.cursor_pos = pos
        self.text       = ""

    def on_key(self, event, canvas, color):
        if not self.active:
            return False
        if event.key == pygame.K_RETURN:
            self._commit(canvas, color)
            return True
        elif event.key == pygame.K_ESCAPE:
            self._cancel()
            return True
        elif event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            return True
        else:
            char = event.unicode
            if char and char.isprintable():
                self.text += char
            return True

    def draw_overlay(self, surface, color, canvas_x_offset):
        if not self.active or self.cursor_pos is None:
            return
        screen_x = self.cursor_pos[0] + canvas_x_offset
        screen_y = self.cursor_pos[1]
        rendered = self.font.render(self.text, True, color)
        surface.blit(rendered, (screen_x, screen_y))
        tick = pygame.time.get_ticks()
        if (tick // 500) % 2 == 0:
            cursor_x = screen_x + rendered.get_width() + 1
            pygame.draw.line(surface, color,
                             (cursor_x, screen_y),
                             (cursor_x, screen_y + self.font.get_height()), 2)

    def _commit(self, canvas, color):
        if self.cursor_pos and self.text:
            rendered = self.font.render(self.text, True, color)
            canvas.blit(rendered, self.cursor_pos)
        self._cancel()

    def _cancel(self):
        self.active     = False
        self.text       = ""
        self.cursor_pos = None

    def draw_cursor(self, surface, pos, color, size):
        pygame.draw.line(surface, color, (pos[0], pos[1] - 10), (pos[0], pos[1] + 10), 2)
        pygame.draw.line(surface, color, (pos[0] - 4, pos[1] - 10), (pos[0] + 4, pos[1] - 10), 2)
        pygame.draw.line(surface, color, (pos[0] - 4, pos[1] + 10), (pos[0] + 4, pos[1] + 10), 2)