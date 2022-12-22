from .vk_module import *
from . import *
from pygame import display as pg_display


class BoxletVK:
	def __init__(self, width, height, wm_info):

		#glfw window parameters
		self.width = width
		self.height = height
		# self.window = window

		if DEBUG_MODE:
			print("Making a graphics engine")
		
		# self.make_instance()
		self.make_pygame_instance(wm_info)

		self.make_device()

		BVKC.command_pool = vk_commands.CommandPool(
			self.queue_families,
			self.surface,
			self.instance
		)


	def make_pygame_instance(self, wm_info):
		self.instance = vk_instance.make_instance('ID Tech 12')

		if DEBUG_MODE:
			self.debug_messenger = vk_logging.DebugMessenger(self.instance)

		vkCreateWin32SurfaceKHR = vkGetInstanceProcAddr(self.instance, 'vkCreateWin32SurfaceKHR')

		surface_create_info = VkWin32SurfaceCreateInfoKHR(
			hwnd = wm_info['window'], 
			hinstance = wm_info['hinstance']
		)

		self.surface = vkCreateWin32SurfaceKHR(
			instance = self.instance,
			pCreateInfo = surface_create_info, 
			pAllocator = None, 
			pSurface = ffi.new('VkSurfaceKHR*')
		)[0]

	def make_device(self):
		BVKC.physical_device = vk_device.choose_physical_device(self.instance)
		self.queue_families = vk_queue_families.QueueFamilyIndices(self.instance, self.surface)
		BVKC.logical_device = vk_device.LogicalDevice(self.queue_families)
		[BVKC.graphics_queue, BVKC.present_queue] = self.queue_families.get_queue()
		
		BVKC.swapchain = vk_swapchain.SwapChainBundle(self.queue_families, self.width, self.height)

	def finalize_setup(self):
		BVKC.swapchain.init_frame_buffers(RenderPass.get_all_instances()[0], BVKC.command_pool)

	def recreate_swapchain(self):
		if DEBUG_MODE:
			print('recreate swapchain')

		BVKC.swapchain.remake(self.width, self.height)

		BVKC.command_pool.destroy() 
		# TODO remove .destroy()? but not destroying the command pool causes a memory leak
		# probably would need to free what is in the command_buffer
		# I think they would normally be freed when the command pool was destroyed

		BVKC.command_pool = vk_commands.CommandPool(
			self.queue_families,
			self.surface,
			self.instance
		)

		self.finalize_setup()

	def record_draw_commands(self, command_buffer):
		begin_info = VkCommandBufferBeginInfo()

		vkBeginCommandBuffer(command_buffer, begin_info)

		RenderingStep.begin_from_base(command_buffer)

		vkEndCommandBuffer(command_buffer)

	def render(self):
		# if the window is minimized, skip the renderloop
		if not pg_display.get_active():
			return

		# if the window is a different size than before, than recreate the swapchain
		if pg_display.get_window_size() != (self.width, self.height):
			self.width, self.height = pg_display.get_window_size()
			self.recreate_swapchain()
			return

		vkAcquireNextImageKHR = vkGetDeviceProcAddr(BVKC.logical_device.device, 'vkAcquireNextImageKHR')
		vkQueuePresentKHR = vkGetDeviceProcAddr(BVKC.logical_device.device, 'vkQueuePresentKHR')

		prev_frame = BVKC.swapchain.frames[BVKC.swapchain.current_frame]
		prev_frame.in_flight.wait_for()
		prev_frame.in_flight.reset()
		# These semaphores and fences are probably used in a bad way, even though it works

		image_index = vkAcquireNextImageKHR(
			device = BVKC.logical_device.device, swapchain = BVKC.swapchain.vk_addr, timeout = 1000000000,
			semaphore = prev_frame.image_available.vk_addr, fence = VK_NULL_HANDLE
		)

		BVKC.swapchain.current_frame = image_index 
		next_frame = BVKC.swapchain.frames[image_index]

		command_buffer = next_frame.command_buffer.vk_addr
		vkResetCommandBuffer(commandBuffer = command_buffer, flags = 0)
		self.record_draw_commands(command_buffer)

		submit_info = VkSubmitInfo(
			waitSemaphoreCount = 1, pWaitSemaphores = [prev_frame.image_available.vk_addr],
			pWaitDstStageMask = [VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT],
			commandBufferCount = 1, pCommandBuffers = [command_buffer],
			signalSemaphoreCount = 1, pSignalSemaphores = [prev_frame.render_finished.vk_addr] 
		)

		vkQueueSubmit(
			queue = BVKC.graphics_queue, submitCount = 1,
			pSubmits = submit_info, fence = prev_frame.in_flight.vk_addr
		)

		present_info = VkPresentInfoKHR(
			waitSemaphoreCount = 1, pWaitSemaphores = [prev_frame.render_finished.vk_addr],
			swapchainCount = 1, pSwapchains = [BVKC.swapchain.vk_addr],
			pImageIndices = [image_index]
		)

		vkQueuePresentKHR(BVKC.present_queue, present_info)

	def close(self):

		vkDeviceWaitIdle(BVKC.logical_device.device)

		vk_mesh.Mesh._destroy_all()

		if DEBUG_MODE:
			print("Goodbye see you!\n")

		vk_renderer.Renderer._destroy_all()

		BVKC.command_pool.destroy()

		vk_pipeline.GraphicsPipeline._destroy_all()
		vk_pipeline.PipelineLayout._destroy_all()
		vk_pipeline.RenderPass._destroy_all()

		BVKC.swapchain.destroy()

		Texture._destroy_all()

		BVKC.logical_device.destroy()

		destruction_function = vkGetInstanceProcAddr(self.instance, 'vkDestroySurfaceKHR')
		destruction_function(self.instance, self.surface, None)

		if DEBUG_MODE:
			self.debug_messenger.destroy()

		vkDestroyInstance(self.instance, None)

