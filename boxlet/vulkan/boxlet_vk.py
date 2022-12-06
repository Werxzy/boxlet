from . import *
from .vk_library import *
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
		self.make_pipeline()
		self.finalize_setup()


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
		self.physical_device = vk_device.choose_physical_device(self.instance)
		self.queue_families = vk_queue_families.QueueFamilyIndices(self.physical_device, self.instance, self.surface)
		self.logical_device = vk_device.LogicalDevice(self.physical_device, self.queue_families)
		[self.graphics_queue, self.present_queue] = self.queue_families.get_queue(self.logical_device)
		# vk_device.query_swapchain_support(self.instance, self.physical_device, self.surface, True)
		
		self.swapchain_bundle = vk_swapchain.SwapChainBundle(self.logical_device, self.queue_families, self.width, self.height)

	def make_pipeline(self):
		input_bundle = vk_pipeline.InputBundle(
			self.logical_device,
			self.swapchain_bundle.format,
			self.swapchain_bundle.extent,
			'shaders/vert.spv',
			'shaders/frag.spv'
		)

		output_bundle = vk_pipeline.create_graphics_pipeline(input_bundle)

		self.pipeline_layout = output_bundle.pipeline_layout
		self.render_pass = output_bundle.render_pass
		self.pipeline = output_bundle.pipeline

	def finalize_setup(self):
		self.frame_buffer_input = vk_framebuffer.FramebufferInput(
			self.logical_device,
			self.render_pass,
			self.swapchain_bundle.extent,
			self.swapchain_bundle.frames
		)

		self.command_pool = vk_commands.CommandPool(
			self.physical_device,
			self.logical_device,
			self.queue_families,
			self.surface,
			self.instance
		)

		self.command_buffer = vk_commands.CommandBuffer(
			self.logical_device,
			self.command_pool,
			self.swapchain_bundle.frames
		)

	def recreate_swapchain(self):
		if DEBUG_MODE:
			print('recreate swapchain')

		self.swapchain_bundle.remake(self.width, self.height)

		self.command_pool.destroy() 
		# TODO remove .destroy()? but not destroying the command pool causes a memory leak
		# probably would need to free what is in the command_buffer
		# I think they would normally be freed when the command pool was destroyed

		self.finalize_setup()

	def record_draw_commands(self, command_buffer, image_index):
		begin_info = VkCommandBufferBeginInfo()

		vkBeginCommandBuffer(command_buffer, begin_info)

		render_pass_info = VkRenderPassBeginInfo(
			renderPass = self.render_pass,
			framebuffer = self.swapchain_bundle.frames[image_index].frame_buffer,
			renderArea = [[0,0], self.swapchain_bundle.extent]
		)

		clear_color = VkClearValue([[1.0, 0.5, 0.25, 1.0]])
		render_pass_info.clearValueCount = 1
		render_pass_info.pClearValues = ffi.addressof(clear_color)

		vkCmdBeginRenderPass(command_buffer, render_pass_info, VK_SUBPASS_CONTENTS_INLINE)

		vkCmdBindPipeline(command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.pipeline)

		for r in vk_renderer.Renderer.all_renderers:
			r.prepare(command_buffer)

		vkCmdEndRenderPass(command_buffer)

		vkEndCommandBuffer(command_buffer)

	def render(self):
		# TODO, double check the semphores
		# I wasn't sure if the tutorial was correct, so I modified them
		# it appears to work currently, but could have frame lag

		# TODO, remove scene parameter

		# if the window is minimized, skip the renderloop
		if not pg_display.get_active():
			return

		# if the window is a different size than before, than recreate the swapchain
		if pg_display.get_window_size() != (self.width, self.height):
			self.width, self.height = pg_display.get_window_size()
			self.recreate_swapchain()
			return

		vkAcquireNextImageKHR = vkGetDeviceProcAddr(self.logical_device.device, 'vkAcquireNextImageKHR')
		vkQueuePresentKHR = vkGetDeviceProcAddr(self.logical_device.device, 'vkQueuePresentKHR')

		prev_frame = self.swapchain_bundle.frames[self.swapchain_bundle.current_frame]
		prev_frame.in_flight.wait_for()
		prev_frame.in_flight.reset()

		image_index = vkAcquireNextImageKHR(
			device = self.logical_device.device, swapchain = self.swapchain_bundle.swapchain, timeout = 1000000000,
			semaphore = prev_frame.image_available.vk_id, fence = VK_NULL_HANDLE
		)

		next_frame = self.swapchain_bundle.frames[image_index]

		command_buffer = next_frame.command_buffer
		vkResetCommandBuffer(commandBuffer = command_buffer, flags = 0)
		self.record_draw_commands(command_buffer, image_index)

		submit_info = VkSubmitInfo(
			waitSemaphoreCount = 1, pWaitSemaphores = [next_frame.image_available.vk_id],
			pWaitDstStageMask = [VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT],
			commandBufferCount = 1, pCommandBuffers = [command_buffer],
			signalSemaphoreCount = 1, pSignalSemaphores = [next_frame.render_finished.vk_id] 
		)

		vkQueueSubmit(
			queue = self.graphics_queue, submitCount = 1,
			pSubmits = submit_info, fence = next_frame.in_flight.vk_id
		)

		present_info = VkPresentInfoKHR(
			waitSemaphoreCount = 1, pWaitSemaphores = [next_frame.render_finished.vk_id],
			swapchainCount = 1, pSwapchains = [self.swapchain_bundle.swapchain],
			pImageIndices = [image_index]
		)

		vkQueuePresentKHR(self.present_queue, present_info)

		self.swapchain_bundle.increment_frame()

	def close(self):

		vkDeviceWaitIdle(self.logical_device.device)

		vk_mesh.Mesh.destroy_all()

		if DEBUG_MODE:
			print("Goodbye see you!\n")

		self.command_pool.destroy()

		vkDestroyPipeline(self.logical_device.device, self.pipeline, None)
		vkDestroyPipelineLayout(self.logical_device.device, self.pipeline_layout, None)
		vkDestroyRenderPass(self.logical_device.device, self.render_pass, None)

		self.swapchain_bundle.destroy()

		vk_renderer.Renderer._destroy_all()

		self.logical_device.destroy()

		destruction_function = vkGetInstanceProcAddr(self.instance, 'vkDestroySurfaceKHR')
		destruction_function(self.instance, self.surface, None)

		if DEBUG_MODE:
			self.debug_messenger.destroy()

		vkDestroyInstance(self.instance, None)

		#terminate glfw
		# glfw.terminate()