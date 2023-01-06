import math

import numpy as np

from . import Tmath, Transform
from .. import pygame


class CameraBase(Transform):
	def __init__(self, *args, horizontal_fov = False, invert_y = 1, **kwargs) -> None:
		super().__init__(*args, **kwargs)

		self.horizontal_fov = horizontal_fov
		self.invert_y = invert_y

		self.perspective(90, 16.0/9.0, 0.1, 1000)
		# self.orthographic(-5, 5, -5 * 9 / 16, 5 * 9 / 16, 0.1, 1000)

	def perspective(self, fov:float, aspect:float, near:float, far:float):
		f = math.tan(math.radians(fov)/2)

		self.clip_near, self.clip_far = near, far

		x = 1 / (f if self.horizontal_fov else f * aspect)
		y = aspect * x * self.invert_y
		z1 = (near + far) / (near - far)
		z2 = 2 * near * far / (near - far)

		self.proj_matrix = np.array([[x, 0, 0, 0], [0, y, 0, 0], [0, 0, -z1, 1], [0, 0, z2, 0]])
		self.inv_proj_matrix = np.linalg.inv(self.proj_matrix)
		self.proj_type_perspective = True

	def perspective_full(self, 
			fov:float = 90, 
			aspect:float = 16/9, 
			left:float = -0.5, right:float = 0.5, 
			bottom:float = -0.5, top:float = 0.5, 
			near:float = 0.1, far:float = 1000):

		f = math.tan(math.radians(fov)/2)

		self.clip_near, self.clip_far = near, far

		x = 1 / (f if self.horizontal_fov else f * aspect)
		y = aspect * x * self.invert_y
		z1 = (near + far) / (near - far)
		z2 = 2 * near * far / (near - far)

		rl = right - left
		tb = top - bottom

		self.proj_matrix = np.array([
			[x/rl, 0, 0, 0], 
			[0, y/tb, 0, 0], 
			[-(left+right)/rl, -(top+bottom)/tb, -z1, 1], 
			[0, 0, z2, 0]])
		self.inv_proj_matrix = np.linalg.inv(self.proj_matrix)
		self.proj_type_perspective = True

	def orthographic(self, left:float, right:float, bottom:float, top:float, near:float, far:float):
		self.clip_near, self.clip_far = near, far

		dx = 1 / (right - left)
		dy = self.invert_y / (top - bottom)
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


	def get_mouse_ray(self, pos):
		'Returns the ray of the given mouse coordinate from screen space to world space.\n\nreturns (pos, direction)'

		coord = pos / np.array(pygame.display.get_window_size()) * 2 - 1

		if self.proj_type_perspective:
			ray_eye = np.matmul(self.inv_proj_matrix, np.array([coord[0],-coord[1],-1,1]))		
			ray_world = np.matmul(np.linalg.inv(self.model_matrix), np.array([ray_eye[0],ray_eye[1],1,0]))

			return self.position, Tmath.normalize(ray_world[0:3])

		else: # orthographic projection
			start_eye = np.matmul(self.inv_proj_matrix.T, np.array([coord[0],-coord[1],-1,1]))		
			start_world = np.matmul(self.model_matrix.T, np.array([start_eye[0],start_eye[1],start_eye[2],1]))

			return start_world[:3], Tmath.normalize(self.forward)

