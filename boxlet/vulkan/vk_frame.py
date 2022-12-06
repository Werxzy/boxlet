from . import *
from .vk_module import *


class SwapChainFrame:
	def __init__(self, logical_device, image, image_view) -> None:
		self.logical_device = logical_device
		self.image = image
		self.image_view = image_view
		self.frame_buffer = None
		self.command_buffer = None

		self.in_flight = vk_sync.Fence(logical_device)
		self.image_available = vk_sync.Semaphore(logical_device)
		self.render_finished = vk_sync.Semaphore(logical_device)

		# TODO if this is created in only one way
		# or requires all future variables
		# move everything into this init function

	def destroy(self):
		self.in_flight.destroy()
		self.image_available.destroy()
		self.render_finished.destroy()

		vkDestroyImageView(
			self.logical_device.device, self.image_view, None
		)
		if self.frame_buffer is not None:
			vkDestroyFramebuffer(
				self.logical_device.device, self.frame_buffer, None
			)
		