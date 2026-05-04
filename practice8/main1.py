import pygame, sys
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Hello World")
while True:
 for event in pygame.event.get():
  if event.type == pygame.QUIT:
   pygame.quit()
   sys.exit()
  if event.type == pygame.MOUSEBUTTONDOWN:
   pos=pygame.mouse.get_pos()
   btn=pygame.mouse
   print ("x = {}, y = {}".format(pos[0], pos[1]))