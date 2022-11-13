import numpy as np
import pygame
from OpenGL.GL import *


class Texture:
	def __init__(self, image:pygame.Surface, nearest = True, mipmap = False) -> None:
		# Generate: request a texture
		self.image_texture = glGenTextures(1)

		# Bind: set the newly requested texture as the active GL_TEXTURE_2D.
		#   All subsequent modifications of GL_TEXTURE_2D will affect our texture (or how it is used)
		glBindTexture(GL_TEXTURE_2D, self.image_texture)

		self.size = np.array([image.get_width(), image.get_height()], np.int32)
		self.orignal = image

		glTexImage2D(GL_TEXTURE_2D, 
			0, 
			GL_RGBA32F, 
			self.size[0], 
			self.size[1], 
			0, 
			GL_RGBA, 
			GL_UNSIGNED_BYTE, 
			pygame.image.tostring(image, "RGBA", True))

		# set the filtering mode for the texture
		if mipmap:
			glGenerateMipmap(GL_TEXTURE_2D)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
			glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_LOD_BIAS, -1)
		else:
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST if nearest else GL_LINEAR)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST if nearest else GL_LINEAR)


		glBindTexture(GL_TEXTURE_2D, 0)

	# def __del__(self):
	# 	glDeleteTextures(1, [self.image_texture])


class MultiTexture(Texture):
	def __init__(self, image:pygame.Surface, sub_image_data:list[tuple[float, float, float, float]], nearest = True, mipmap = False):
		super().__init__(image, nearest, mipmap)

		self.sub_image_data = list(sub_image_data)

	# @staticmethod
	# def create_from_textures(*images:list[pygame.Surface]):
	# 	...
		# TODO creates a single image from multiple images and stores their coordinates in sub_image_data


