from ..vk_module import *
from .. import *


class SwapChainFrame:
	def __init__(self, image, swapchain:'vk_swapchain.SwapChainBundle') -> None:
		self.image_view = ImageView(image, swapchain.format, swapchain.extent)

		self.frame_buffer:FrameBuffer = None
		self.command_buffer = None

		self.in_flight = vk_sync.Fence()
		self.image_available = vk_sync.Semaphore()
		self.render_finished = vk_sync.Semaphore()

	def init_buffers(self, render_pass, command_pool:'CommandPool', depth_buffer:ImageView):
		'''
		Initializes some buffers seperate from __init__.
		
		These buffers are seperate because they may be initialized/destroyed multiple times during the application's lifetime.
		'''
		extent = self.image_view.extent
		self.frame_buffer = FrameBuffer(render_pass, extent.width, extent.height, [self.image_view.vk_addr, depth_buffer.vk_addr])
		self.command_buffer = CommandBuffer(command_pool)
		
	def destroy(self):
		self.in_flight.destroy()
		self.image_available.destroy()
		self.render_finished.destroy()

		self.image_view.destroy()
		if self.frame_buffer is not None:
			self.frame_buffer.destroy()
		
