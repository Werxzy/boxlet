import numpy as np
import math

from boxlet import Renderer, Shader, Tmath, manager
from OpenGL.GL import glUniformMatrix4fv


class Camera3D(Renderer):
	def __init__(self, queue) -> None:
		super().__init__(queue)

		self.view_matrix = np.identity(4)
		self.perspective(90, 16.0/9.0, 0.1, 1000)
		# self.orthographic(-5, 5, -5 * 9 / 16, 5 * 9 / 16, 0.1, 1000)
		Shader.add_global_matrix_uniform('viewProj', glUniformMatrix4fv, np.identity(4, dtype=np.float32))

	def render(self):
		Shader.set_global_uniform('viewProj', np.matmul(np.linalg.inv(self.view_matrix), self.proj_matrix))

	def move(self, amount):
		# self.view_matrix = np.matmul(self.translate(amount), self.view_matrix)
		self.view_matrix[3,:3] += amount # simpler

	def perspective(self, fov:float, aspect:float, near:float, far:float):
		f = math.tan(math.radians(fov)/2)

		self.clip_near, self.clip_far = near, far

		x = 1 / f
		y = aspect * x
		z1 = (near + far) / (near - far)
		z2 = 2 * near * far / (near - far)

		# return np.array([[x, 0, 0, 0], [0, y, 0, 0], [0, 0, z1, -1], [0, 0, z2, 0]])
		self.proj_matrix = np.array([[x, 0, 0, 0], [0, y, 0, 0], [0, 0, -z1, 1], [0, 0, z2, 0]]) # tempting to flip the z axis for (0,0,1) to be the camera forward
		self.inv_proj_matrix = np.linalg.inv(self.proj_matrix)
		self.proj_type_perspective = True


	def orthographic(self, left:float, right:float, bottom:float, top:float, near:float, far:float):
		self.clip_near, self.clip_far = near, far

		dx = 1 / (right - left)
		dy = 1 / (top - bottom)
		dz = 1 / (far - near)

		rx = -(right + left) * dx
		ry = -(top + bottom) * dy
		rz = -(far + near) * dz

		self.proj_matrix = np.array([[2*dx, 0, 0, rx], [0, 2*dy, 0, ry], [0, 0, 2*dz, rz], [0, 0, 0, 1]]).T
		self.inv_proj_matrix = np.linalg.inv(self.proj_matrix)
		self.proj_type_perspective = False

	# def orthographic_simple(self, width:float, height:float, depth:float):
	# 	# 0,0 is the center of the screen

	# 	dx = 4 / width
	# 	dy = 4 / height
	# 	dz = -2 / depth
		
		# self.proj_matrix = return np.array([[dx, 0, 0, 0], [0, dy, 0, 0], [0, 0, dz, -1], [0, 0, 0, 1]])
		# self.inv_proj_matrix = np.linalg.inv(self.proj_matrix)


	def look_at(self, eye, target, up):
		self.view_matrix = Tmath.look_at(eye, target, up)

	def look_at_2(self, pos, forward, up):
		self.view_matrix = Tmath.make_matrix(pos, forward, up)

	def reset_pos(self):
		self.view_matrix = np.identity(4)

	def fps_look(self, pos, x, y):
		self.view_matrix = Tmath.fps_look(pos, x, y)

	@property
	def right(self):
		return Tmath.normalize(self.view_matrix[0,:3])

	@property
	def up(self):
		return Tmath.normalize(self.view_matrix[1,:3])

	@property
	def forward(self):
		return Tmath.normalize(self.view_matrix[2,:3])

	@property
	def position(self):
		return self.view_matrix[3,:3]

	@position.setter
	def position(self, value):
		self.view_matrix[3,:3] = value

	@property
	def x(self):
		return self.view_matrix[3,0]

	@x.setter
	def x(self, value):
		self.view_matrix[3,0] = value

	@property
	def y(self):
		return self.view_matrix[3,1]

	@y.setter
	def y(self, value):
		self.view_matrix[3,1] = value

	@property
	def z(self):
		return self.view_matrix[3,2]

	@z.setter
	def z(self, value):
		self.view_matrix[3,2] = value

	def get_mouse_ray(self, pos):
		'Returns the ray of the given mouse coordinate from screen space to world space.\n\nreturns (pos, direction)'

		coord = pos / manager.display_size * 2 - 1

		if self.proj_type_perspective:
			ray_eye = np.matmul(self.inv_proj_matrix, np.array([coord[0],-coord[1],-1,1]))		
			ray_world = np.matmul(np.linalg.inv(self.view_matrix), np.array([ray_eye[0],ray_eye[1],1,0]))

			return self.position, Tmath.normalize(ray_world[0:3])

		else: # orthographic projection
			start_eye = np.matmul(self.inv_proj_matrix.T, np.array([coord[0],-coord[1],-1,1]))		
			start_world = np.matmul(self.view_matrix.T, np.array([start_eye[0],start_eye[1],start_eye[2],1]))

			return start_world[:3], Tmath.normalize(self.forward)



