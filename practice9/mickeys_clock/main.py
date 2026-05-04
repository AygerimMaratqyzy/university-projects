import pygame
from clock import MickeyClock

pygame.init()

# LOAD IMAGE FIRST (no distortion)
image = pygame.image.load("mickeyclock.jpeg")
width, height = image.get_size()

# EXACT MATCH WINDOW
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Mickey Clock")

clock = pygame.time.Clock()
mickey_clock = MickeyClock(width, height)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    mickey_clock.update()
    mickey_clock.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()