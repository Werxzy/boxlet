from . import *
from . import scene
import pygame

class App:
	def __init__(self, width, height) -> None:
		# self.build_glfw_window(width, height)

		self.display = pygame.display.set_mode((width,height), flags = pygame.DOUBLEBUF | pygame.RESIZABLE)
		wm_info = pygame.display.get_wm_info()

		self.graphics_engine = Engine(width, height, wm_info)
		self.scene = scene.Scene() # TODO, change this

		# self.last_time = glfw.get_time()
		# self.current_time = glfw.get_time()
		# self.num_frames = 0
		# self.frame_time = 0

	def build_glfw_window(self, width, height):

		#initialize glfw
		glfw.init()

		#no default rendering client, we'll hook vulkan up to the window later
		glfw.window_hint(GLFW_CONSTANTS.GLFW_CLIENT_API, GLFW_CONSTANTS.GLFW_NO_API)
		#resizing breaks the swapchain, we'll disable it for now
		glfw.window_hint(GLFW_CONSTANTS.GLFW_RESIZABLE, GLFW_CONSTANTS.GLFW_FALSE)
		
		#create_window(int width, int height, const char *title, GLFWmonitor *monitor, GLFWwindow *share)
		self.window = glfw.create_window(width, height, "ID Tech 12", None, None)

		if DEBUG_MODE:
			if self.window is not None:
				print(f"Successfully made a glfw window called \"ID Tech 12\", width: {width}, height: {height}\n")
			else:
				print("GLFW window creation failed\n")

	def calculate_framerate(self):
		self.current_time = glfw.get_time()
		delta = self.current_time - self.last_time

		if delta >= 1:
			framerate = max(1, self.num_frames // delta)
			glfw.set_window_title(self.window, f'Running at {framerate} fps.')
			self.last_time = self.current_time
			self.num_frames = -1
			self.frame_time = 1000.0 / framerate
		
		self.num_frames += 1

	def run(self):
		# while not glfw.window_should_close(self.window):

		# 	glfw.poll_events()
		# 	self.graphics_engine.render(self.scene)
		# 	self.calculate_framerate()
		while True:
			for event in pygame.event.get(pygame.QUIT):
				pygame.quit()
				return

			self.graphics_engine.render(self.scene)

			

	def close(self):
		self.graphics_engine.close()
