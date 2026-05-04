import pygame, sys
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Hello World")
while True:
 for event in pygame.event.get():
  if event.type == pygame.QUIT:
   pygame.quit()
   sys.exit()
  if event.type == pygame.MOUSEMOTION:
   pos=event.pos
   print ("x = {}, y = {}".format(pos[0], pos[1]))