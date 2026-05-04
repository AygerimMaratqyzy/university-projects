import pygame
pygame.init()

screen = pygame.display.set_mode((400,300))
pygame.display.set_caption("My First Game")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))  # clear screen

    pygame.draw.rect(screen, (0, 128, 255), (30, 30, 60, 60))  # draw rectangle

    pygame.display.flip()  # 🔥 update screen

pygame.quit()