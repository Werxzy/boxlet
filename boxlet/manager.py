import time
from boxlet import *


class Manager:

	def __init__(self) -> None:
		pygame.init()

		import os

		def get_else(name:str, default:str):
			return os.environ[name] if name in os.environ else default

		# settings TODO : windowed vs fullscreen

		self.screen_pos = np.zeros(2)
		self.screen_size = np.array([int(i) for i in get_else('BOXLET_RESOLUTION', '960,540').split(',')])
		
		self.render_mode = get_else('BOXLET_RENDER_MODE', 'sdl2')
		match(self.render_mode):
			case 'sdl2': 
				self.display = pygame.display.set_mode(self.screen_size, flags = pygame.DOUBLEBUF)

				self.fill_color = get_else('BOXLET_FILL_COLOR', 'black')
				if self.fill_color.count(',') > 0: # instead create a list
					self.fill_color = [int(c) for c in self.fill_color.split(',')]

				self.pixel_scale = int(get_else('BOXLET_PIXEL_SCALE', '4'))
				if self.pixel_scale > 1:
					self.pixel_display = pygame.surface.Surface(round(self.screen_size / self.pixel_scale))

			case 'opengl': 
				self.display = pygame.display.set_mode(self.screen_size, flags = pygame.OPENGL | pygame.DOUBLEBUF)
			
			case _:
				raise Exception('Unrecognized render mode.')
				
		
		# self.display = pygame.display.set_mode(flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN, vsync = 1)
		# self.screen_size[:] = self.display.get_size()

		self.clock = pygame.time.Clock()

		self.fps = 100 # frames per second, may get replaced by turning on vsync
		self.ups = int(get_else('BOXLET_UPDATE_RATE', '60')) # fixed updates per second
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

			self.clock.tick_busy_loop(self.fps)

	def render(self):
		if self.render_mode == 'sdl2':
			if self.pixel_scale != 1:
				self.screen.fill(self.fill_color)
				Entity.__call_function__('render')
				pygame.transform.scale(self.screen, self.display.get_size(), self.display)

			else:
				self.display.fill(self.fill_color)
				Entity.__call_function__('render')

			pygame.display.update()
		
		else:
			Renderer.render_all()
			pygame.display.flip()

	def quit(self):
		self.exit_program = True
		pygame.quit()


instance = Manager()

