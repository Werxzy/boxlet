import time
from boxlet import *


class Manager:

	def __init__(self) -> None:
		pygame.init()

		from os import environ

		self.fullscreen = int(environ.get('BOXLET_FULLSCREEN', '0'))
		if not self.fullscreen:
			self.display_size = np.array([int(i) for i in environ.get('BOXLET_RESOLUTION', '960,540').split(',')])
		
		self.render_mode = environ.get('BOXLET_RENDER_MODE', 'sdl2')
		if self.render_mode == 'sdl2':
			self.vsync = 0
			self.screen_pos = np.zeros(2)
			if self.fullscreen:
				self.display = pygame.display.set_mode(flags = pygame.DOUBLEBUF | pygame.FULLSCREEN)
				self.display_size = np.array(self.display.get_size())
			else:
				self.display = pygame.display.set_mode(self.display_size, flags = pygame.DOUBLEBUF)

			self.fill_color = environ.get('BOXLET_FILL_COLOR', 'black')
			if self.fill_color.count(',') > 0: # instead create a list
				self.fill_color = [int(c) for c in self.fill_color.split(',')]

			self.canvas_size = np.array([int(i) for i in environ.get('BOXLET_CANVAS_SIZE', '0,0').split(',')])
			if 0 in self.canvas_size:
				self.canvas_size = np.array(self.display_size)
			self.canvas = pygame.surface.Surface(self.canvas_size)
		
		elif self.render_mode == 'opengl':
			self.vsync = int(environ.get('BOXLET_OPENGL_VSYNC', '1'))

			if environ.get('BOXLET_SKIP_GL_CONTEXT_SETUP', '0') == '0':
				pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, int(environ.get('BOXLET_GL_CONTEXT_MAJOR_VERSION', '3')))
				pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, int(environ.get('BOXLET_GL_CONTEXT_MINOR_VERSION', '3')))
				pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
			if self.fullscreen:
				self.display = pygame.display.set_mode(flags = pygame.OPENGL | pygame.FULLSCREEN | pygame.DOUBLEBUF, vsync = self.vsync)
				self.display_size = np.array(self.display.get_size())
			else:
				self.display = pygame.display.set_mode(self.display_size, flags = pygame.OPENGL | pygame.DOUBLEBUF, vsync = self.vsync)

		else:
			raise Exception('Unrecognized render mode.')
		
		# self.display = pygame.display.set_mode(flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN, vsync = 1)
		# self.screen_size[:] = self.display.get_size()

		self.clock = pygame.time.Clock()

		self.fps = int(environ.get('BOXLET_FRAME_RATE', '120')) # frames per second, may get replaced by turning on vsync
		self.ups = int(environ.get('BOXLET_UPDATE_RATE', '60')) # fixed updates per second
		self.fixed_delta_time = 1 / self.ups # time passed for fixed update
		self.delta_time = 0.0 # time passed for vary update
		self.max_delta_time = self.fixed_delta_time * 3 # prevents large jumps in time, either from lag or changing the clock
		self.time = 0 # time since start
		self.fixed_time = 0 # fixed time since start
		self.system_time = time.time() # system time
		self.interpolate_time = 0 # interpolation between fixed updates for vary updates

		pygame.joystick.init()
		self.joysticks = []
		self.current_joystick = None

		self.exit_program = False

	def run(self):
		pygame.event.set_blocked(None)
		pygame.event.set_allowed(Entity.watched_events)
		pygame.event.set_allowed([pygame.WINDOWEXPOSED, pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED, pygame.QUIT])

		self.system_time = time.time()

		while True:
			for _ in pygame.event.get(eventtype=pygame.WINDOWEXPOSED):
				self.system_time = time.time() # this still does not help every case it freezes, maybe have a maximum delta time.

			new_system_time = time.time()
			self.delta_time = clamp(new_system_time - self.system_time, 0, self.max_delta_time)
			self.time += self.delta_time
			self.system_time = new_system_time

			for event in pygame.event.get(Entity.watched_events, False):
				Entity.__call_event_function__(event.type, event)

			if self.exit_program: return

			for event in pygame.event.get([pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED], False):
				self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
				if event.type == pygame.JOYDEVICEADDED:
					self.current_joystick = self.joysticks[event.device_index]
				elif self.current_joystick.get_instance_id() == event.instance_id:
					self.current_joystick = None

			for event in pygame.event.get(pygame.QUIT, False):
				pygame.quit()
				return

			pygame.event.clear(pump=False)
			
			for i in range(5):
				if self.time >= self.fixed_time + self.fixed_delta_time:
					self.fixed_time += self.fixed_delta_time
					Entity.__call_function__('fixed_update')
				else:
					break

			if self.exit_program: return
			
			self.interpolate_time = clamp((self.time - self.fixed_time) / self.fixed_delta_time, 0, 1)

			Entity.__call_function__('vary_update')
			Entity.__add_new_entities__()
			Entity.__destroy_entities__()
			
			if self.exit_program: return

			self.render()	

			if not self.vsync:
				self.clock.tick_busy_loop(self.fps)

	def render(self):
		if self.render_mode == 'sdl2':
			self.canvas.fill(self.fill_color)
			Entity.__call_function__('render')
			pygame.transform.scale(self.canvas, self.display.get_size(), self.display)
			pygame.display.update()
		
		else:
			BoxletGL.render()
			pygame.display.flip()

	def set_display(self, display_size = None, canvas_size = None, fullscreen = None, vsync = None):
		self.fullscreen = fullscreen
		if not self.fullscreen and not display_size:
			self.display_size = np.array([960, 540])
		
		if self.render_mode == 'sdl2':
			if self.fullscreen:
				self.display = pygame.display.set_mode(flags = pygame.DOUBLEBUF | pygame.FULLSCREEN)
				self.display_size = np.array(self.display.get_size())
			else:
				self.display = pygame.display.set_mode(self.display_size, flags = pygame.DOUBLEBUF)

			if canvas_size is not None:
				self.canvas_size = np.array(canvas_size)
			if 0 in self.canvas_size:
				self.canvas_size = np.array(self.display_size)
			self.canvas = pygame.surface.Surface(self.canvas_size)

		elif self.render_mode == 'opengl':
			self.vsync = vsync or self.vsync
			if self.fullscreen:
				self.display = pygame.display.set_mode(flags = pygame.OPENGL | pygame.FULLSCREEN, vsync = self.vsync)
				self.display_size = np.array(self.display.get_size())
			else:
				self.display = pygame.display.set_mode(self.display_size, flags = pygame.OPENGL | pygame.DOUBLEBUF, vsync = self.vsync)

	def quit(self):
		self.exit_program = True
		pygame.quit()


instance = Manager()

