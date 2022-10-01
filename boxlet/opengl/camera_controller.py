from boxlet import *


class CameraController(Entity):
	def __init__(self, camera:Camera3D) -> None:
		self.pos = np.array([0,0,0], float)
		self.x_rot = 0
		self.y_rot = 0
		self.camera = camera
		self.lock_mouse(True)

	def vary_update(self):
		if self.mouse_is_locked:
			pygame.mouse.set_pos(manager.display_size * 0.5)

		b = pygame.key.get_pressed()
		mov = np.zeros(3, float)

		if b[pygame.K_a] != b[pygame.K_d]: mov += self.camera.right * (1 if b[pygame.K_d] else -1)
		if b[pygame.K_s] != b[pygame.K_w]: mov += self.camera.forward * (1 if b[pygame.K_w] else -1)
		if b[pygame.K_q] != b[pygame.K_e]: mov += self.camera.up * (1 if b[pygame.K_e] else -1)
		mov = Tmath.clip_vector(mov)

		self.pos[:] += mov * manager.delta_time * (30 if b[pygame.K_LSHIFT] else 10)
		self.camera.fps_look(self.pos, self.x_rot, self.y_rot)
	
	@Entity.watch_event(pygame.MOUSEMOTION)
	def mouse_movement(self, event):
		if self.mouse_is_locked:
			self.x_rot += event.rel[0] * -0.5
			self.y_rot += event.rel[1] * -0.5
			self.y_rot = clamp(self.y_rot, -90, 90)
			

	@Entity.watch_event(pygame.KEYDOWN)
	def keydown(self, event):
		if event.key == pygame.K_ESCAPE:
			manager.quit()
		if event.key == pygame.K_SPACE:
			self.lock_mouse(not self.mouse_is_locked)
		if event.key == pygame.K_t:
			print(pygame.mouse.get_pos(), self.camera.get_mouse_ray(pygame.mouse.get_pos()))

	def lock_mouse(self, on):
		self.mouse_is_locked = on
		pygame.mouse.set_visible(not on)
		pygame.event.set_grab(on)
		# set_grab is important to speed up pygame.mouse.set_pos
			