from .vk_module import *
from . import *


class SwapChainFrame:
	def __init__(self, image, image_view) -> None:
		self.image = image
		self.image_view = image_view
		self.frame_buffer = None
		self.command_buffer = None

		self.in_flight = vk_sync.Fence()
		self.image_available = vk_sync.Semaphore()
		self.render_finished = vk_sync.Semaphore()

		# TODO if this is created in only one way
		# or requires all future variables
		# move everything into this init function

	def destroy(self):
		self.in_flight.destroy()
		self.image_available.destroy()
		self.render_finished.destroy()

		vkDestroyImageView(
			BVKC.logical_device.device, self.image_view, None
		)
		if self.frame_buffer is not None:
			vkDestroyFramebuffer(
				BVKC.logical_device.device, self.frame_buffer, None
			)
		