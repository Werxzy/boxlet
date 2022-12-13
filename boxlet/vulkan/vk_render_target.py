from .vk_module import *
from . import *


class RenderTarget:
	'Encapsulates everything about the object that is being rendered to.'

	def __init__(self, format, extent) -> None:
		self.format = format
		self.extent = extent

	def remake(self, width, height):
		'''
		reinitializes anything that may have gone out of date.
		
		This is usually used to remake the framebuffers.
		'''

	def get_image(self):
		'Used by BoxletVK to get the correct image to sample from?'

	def get_frame_buffer(self) -> FrameBuffer:
		'Used by BoxletVK to get the correct framebuffer to render to.'

	def destroy(self):
		...


class SimpleRenderTarget:
	def __init__(self) -> None:
		pass
