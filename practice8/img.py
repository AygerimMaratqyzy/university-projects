import pygame
pygame.init()
screen = pygame.display.set_mode((600,500))
img = pygame.image.load("C:\\Users\\Asus\\Pictures\\image.png")
done = False
bg = (127,127,127,127)
while not done:
    for event in pygame.event.get():
        screen.fill(bg)
        rect = img.get_rect()
        rect.center=300,250
        screen.blit(img,rect)
        if event.type == pygame.QUIT:
            done = True
    pygame.display.update()