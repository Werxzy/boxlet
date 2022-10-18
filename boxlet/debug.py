from boxlet import *
import time


class Debug(Entity):

	def __init__(self, draw_func, life_time = 30) -> None:
		self.draw_func = draw_func
		self.life_time = life_time

	def fixed_update(self):
		self.life_time -= manager.fixed_delta_time
		if self.life_time <= 0:
			self.destroy()

	@Entity.priority(float('inf'))
	def render(self):
		self.draw_func()

	@staticmethod
	def draw_line(start, end, color = 'red', life_time = 30, world_space = True):

		if world_space:
			def draw(): 
				pygame.draw.line(manager.canvas, color, start - manager.screen_pos, end - manager.screen_pos)
		else:
			def draw(): 
				pygame.draw.line(manager.canvas, color, start, end)

		Debug(draw, life_time)

	@staticmethod
	def draw_ray(start, dir, length = 10, color = 'red', life_time = 30, world_space = True):
		l = dir[0] ** 2 + dir[1] ** 2
		if l == 0: return
		l **= 0.5

		end = (start[0] + dir[0] / l * length, start[1] + dir[1] / l * length)
		
		Debug.draw_line(start, end, color, life_time, world_space)

	@staticmethod
	def clear():
		for e in Entity.entity_dict[Debug]:
			e.destroy()

	@staticmethod
	def simple_timer(test_count = 100):
		'Times the average amount of time the function takes to run every (100) times.\n\nTakes about 0.006ms to run.'

		def wrap2(func):

			func._timer_total = 0
			func._timer_count = 0
			func.track_count = test_count

			def wrap(*args, **kwargs):
				t1 = time.perf_counter()
				re = func(*args, **kwargs)
				t2 = time.perf_counter()	

				func._timer_total += t2 - t1
				func._timer_count += 1

				if func._timer_count >= func.track_count:
					print(func._timer_total * 1000 / func._timer_count)
					func._timer_count = 0
					func._timer_total = 0

				return re

			return wrap

		if not isinstance(test_count, int):
			func, test_count = test_count, 100
			return wrap2(func)

		return wrap2


