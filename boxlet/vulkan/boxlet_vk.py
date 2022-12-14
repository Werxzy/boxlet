from pygame import display as pg_display

from . import (DEBUG_MODE, CommandPool, DebugMessenger, GraphicsPipeline,
               LogicalDevice, Mesh, PhysicalDevice, PipelineLayout,
               QueueFamilyIndices, Renderer, RenderingStep, RenderPass,
               RenderTarget, Shader, SwapChainBundle, Texture, VulkanInstance)
from .vk_module import *


class BoxletVK:
	def __init__(self, width, height, wm_info):

		BVKC.width = width
		BVKC.height = height

		if DEBUG_MODE:
			print("Making a graphics engine")
		
		self.make_pygame_instance(wm_info)

		self.make_device()		

	def make_pygame_instance(self, wm_info):
		driver = pg_display.get_driver()
		self.instance = VulkanInstance('Boxlet Application', driver)

		if DEBUG_MODE:
			self.debug_messenger = DebugMessenger(self.instance)

		match driver:
			case 'windows':
				create_surface = vkGetInstanceProcAddr(self.instance.vk_addr, 'vkCreateWin32SurfaceKHR')

				surface_create_info = VkWin32SurfaceCreateInfoKHR(
					hwnd = wm_info['window'], 
					hinstance = wm_info['hinstance']
				)

			case 'x11':
				print('Unsure if this is the correct implementation')
				create_surface = vkGetInstanceProcAddr(self.instance.vk_addr, 'vkCreateXlibSurfaceKHR')

				# TODO check this with a valid system
				# (my virtual machine can't test this)
				surface_create_info = VkXlibSurfaceCreateInfoKHR(
					dpy = id(wm_info['display']),
					window = wm_info['window']
				)

			case 'cocoa':
				print('Unsure if this is the correct implementation')
				create_surface = vkGetInstanceProcAddr(self.instance.vk_addr, 'vkCreateMacOSSurfaceMVK')

				surface_create_info = VkMacOSSurfaceCreateInfoMVK(
					pView = id(wm_info['window'])
				)

			case _:
				raise Exception(f'Unsupported driver : {driver}')

		self.surface = create_surface(
			instance = self.instance.vk_addr,
			pCreateInfo = surface_create_info, 
			pAllocator = None, 
			pSurface = ffi.new('VkSurfaceKHR*')
		)[0]

		# TODO ??? would SDL_Vulkan_CreateSurface create the surface with less trouble?
		
	def make_device(self):
		BVKC.physical_device = PhysicalDevice(self.instance)
		self.queue_families = QueueFamilyIndices(self.instance, self.surface)
		BVKC.logical_device = LogicalDevice(self.queue_families)
		[BVKC.graphics_queue, BVKC.present_queue] = self.queue_families.get_queue()

		BVKC.command_pool = CommandPool(
			self.queue_families,
			self.surface,
			self.instance
		)
		
		BVKC.swapchain = SwapChainBundle(self.queue_families, BVKC.width, BVKC.height)

	def finalize_setup(self):
		for target in RenderTarget.get_all_instances():
			target.init_frame_buffer()

	def recreate_swapchain(self):
		if DEBUG_MODE:
			print('recreate swapchain')

		for target in RenderTarget.get_all_instances():
			target.remake(BVKC.width, BVKC.height)

		BVKC.command_pool.destroy() 

		BVKC.command_pool = CommandPool(
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
		if pg_display.get_window_size() != (BVKC.width, BVKC.height):
			BVKC.width, BVKC.height = pg_display.get_window_size()
			self.recreate_swapchain()
			return

		vkAcquireNextImageKHR = vkGetDeviceProcAddr(BVKC.logical_device.device, 'vkAcquireNextImageKHR')
		vkQueuePresentKHR = vkGetDeviceProcAddr(BVKC.logical_device.device, 'vkQueuePresentKHR')

		prev_frame = BVKC.swapchain.frames[BVKC.swapchain.current_frame]
		prev_frame.in_flight.wait_for()
		prev_frame.in_flight.reset()

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

		Mesh._destroy_all()

		if DEBUG_MODE:
			print("Goodbye see you!\n")

		Renderer._destroy_all()

		BVKC.command_pool.destroy()

		GraphicsPipeline._destroy_all()
		PipelineLayout._destroy_all()
		RenderPass._destroy_all()
		
		Shader._destroy_all()

		RenderTarget._destroy_all()

		Texture._destroy_all()

		BVKC.logical_device.destroy()

		destruction_function = vkGetInstanceProcAddr(self.instance.vk_addr, 'vkDestroySurfaceKHR')
		destruction_function(self.instance.vk_addr, self.surface, None)

		if DEBUG_MODE:
			self.debug_messenger.destroy()

		self.instance.destroy()

