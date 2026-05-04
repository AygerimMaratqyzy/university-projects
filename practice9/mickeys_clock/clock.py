import pygame
import datetime
import math


class MickeyClock:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)

        # ❌ NO SCALING (this was breaking everything)
        self.clock_img = pygame.image.load("mickeyclock.jpeg").convert_alpha()

    def get_angles(self):
        now = datetime.datetime.now()

        hours = now.hour % 12
        minutes = now.minute
        seconds = now.second + now.microsecond / 1_000_000

        minute_angle = minutes * 6 + seconds * 0.1
        hour_angle = hours * 30 + minutes * 0.5 + seconds * (0.5 / 60)

        return hour_angle, minute_angle

    def draw_hand(self, screen, angle, length, width):
        # correct rotation direction
        rad = math.radians(angle - 90)

        end_x = self.center[0] + math.cos(rad) * length
        end_y = self.center[1] + math.sin(rad) * length

        pygame.draw.line(screen, (0, 0, 0),
                          self.center,
                          (end_x, end_y),
                          width)

    def update(self):
        self.hour_angle, self.minute_angle = self.get_angles()

    def draw(self, screen):
        # FIXED IMAGE (no distortion)
        screen.blit(self.clock_img, (0, 0))

        # tuned lengths (for 1400x1050 image)
        self.draw_hand(screen, self.hour_angle, length=250, width=8)
        self.draw_hand(screen, self.minute_angle, length=380, width=5)