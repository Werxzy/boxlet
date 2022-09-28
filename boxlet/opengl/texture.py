import pygame
from OpenGL.GL import *
import numpy as np

class Texture:
	def __init__(self, image:pygame.Surface, nearest = True) -> None:
		# Generate: request a texture
		self.image_texture = glGenTextures(1)

		# Bind: set the newly requested texture as the active GL_TEXTURE_2D.
		#   All subsequent modifications of GL_TEXTURE_2D will affect our texture (or how it is used)
		glBindTexture(GL_TEXTURE_2D, self.image_texture)

		self.size = np.array([image.get_width(), image.get_height()], np.int32)
		self.orignal = image

		glTexImage2D(GL_TEXTURE_2D, 
			0, 
			GL_RGBA, 
			self.size[0], 
			self.size[1], 
			0, 
			GL_RGBA, 
			GL_UNSIGNED_BYTE, 
			pygame.image.tostring(image, "RGBA", True))

		# set the filtering mode for the texture
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST if nearest else GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST if nearest else GL_LINEAR)

	# def __del__(self):
	# 	glDeleteTextures(1, [self.image_texture])