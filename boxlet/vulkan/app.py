from . import *
from . import scene
import pygame
import time

class App:
	def __init__(self, width, height) -> None:
		# self.build_glfw_window(width, height)

		self.display = pygame.display.set_mode((width,height), flags = pygame.DOUBLEBUF | pygame.RESIZABLE)
		wm_info = pygame.display.get_wm_info()

		self.graphics_engine = Engine(width, height, wm_info)

		self.last_time = time.time()
		self.current_time = time.time()
		self.num_frames = 0
		self.frame_time = 0

	def calculate_framerate(self):
		self.current_time = time.time()
		delta = self.current_time - self.last_time

		if delta >= 1:
			framerate = max(1, self.num_frames // delta)
			pygame.display.set_caption(f'Running at {framerate} fps.')
			self.last_time = self.current_time
			self.num_frames = -1
			self.frame_time = 1000.0 / framerate
		
		self.num_frames += 1

	def run(self):
		while True:
			for event in pygame.event.get(pygame.QUIT):
				pygame.quit()
				return
			
			self.graphics_engine.render()
			self.calculate_framerate()
			
	def close(self):
		self.graphics_engine.close()
