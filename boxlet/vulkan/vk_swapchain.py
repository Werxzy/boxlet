from .vk_module import *
from . import *


class SwapChainSupportDetails:

	def __init__(self, instance, physical_device, surface):
		"""
		typedef struct VkSurfaceCapabilitiesKHR {
			uint32_t                         minImageCount;
			uint32_t                         maxImageCount;
			VkExtent2D                       currentExtent;
			VkExtent2D                       minImageExtent;
			VkExtent2D                       maxImageExtent;
			uint32_t                         maxImageArrayLayers;
			VkSurfaceTransformFlagsKHR       supportedTransforms;
			VkSurfaceTransformFlagBitsKHR    currentTransform;
			VkCompositeAlphaFlagsKHR         supportedCompositeAlpha;
			VkImageUsageFlags                supportedUsageFlags;
		} VkSurfaceCapabilitiesKHR;
		"""
		
		vkGetPhysicalDeviceSurfaceCapabilitiesKHR = vkGetInstanceProcAddr(instance, 'vkGetPhysicalDeviceSurfaceCapabilitiesKHR')
		self.capabilities = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical_device, surface)
		
		if DEBUG_MODE:
				
			print("Swapchain can support the following surface capabilities:")

			print(f"\tminimum image count: {self.capabilities.minImageCount}")
			print(f"\tmaximum image count: {self.capabilities.maxImageCount}")

			print("\tcurrent extent:")
			"""
			typedef struct VkExtent2D {
				uint32_t    width;
				uint32_t    height;
			} VkExtent2D;
			"""
			print(f"\t\twidth: {self.capabilities.currentExtent.width}")
			print(f"\t\theight: {self.capabilities.currentExtent.height}")

			print("\tminimum supported extent:")
			print(f"\t\twidth: {self.capabilities.minImageExtent.width}")
			print(f"\t\theight: {self.capabilities.minImageExtent.height}")

			print("\tmaximum supported extent:")
			print(f"\t\twidth: {self.capabilities.maxImageExtent.width}")
			print(f"\t\theight: {self.capabilities.maxImageExtent.height}")

			print(f"\tmaximum image array layers: {self.capabilities.maxImageArrayLayers}")

				
			print("\tsupported transforms:")
			stringList = vk_logging.log_transform_bits(self.capabilities.supportedTransforms)
			for line in stringList:
				print(f"\t\t{line}")

			print("\tcurrent transform:")
			stringList = vk_logging.log_transform_bits(self.capabilities.currentTransform)
			for line in stringList:
				print(f"\t\t{line}")

			print("\tsupported alpha operations:")
			stringList = vk_logging.log_alpha_composite_bits(self.capabilities.supportedCompositeAlpha)
			for line in stringList:
				print(f"\t\t{line}")

			print("\tsupported image usage:")
			stringList = vk_logging.log_image_usage_bits(self.capabilities.supportedUsageFlags)
			for line in stringList:
				print(f"\t\t{line}")

		vkGetPhysicalDeviceSurfaceFormatsKHR = vkGetInstanceProcAddr(instance, 'vkGetPhysicalDeviceSurfaceFormatsKHR')
		self.formats = vkGetPhysicalDeviceSurfaceFormatsKHR(physical_device, surface)

		if DEBUG_MODE:
			for supportedFormat in self.formats:
				"""
				* typedef struct VkSurfaceFormatKHR {
					VkFormat           format;
					VkColorSpaceKHR    colorSpace;
				} VkSurfaceFormatKHR;
				"""

				print(f"supported pixel format: {vk_logging.format_to_string(supportedFormat.format)}")
				print(f"supported color space: {vk_logging.colorspace_to_string(supportedFormat.colorSpace)}")

		vkGetPhysicalDeviceSurfacePresentModesKHR = vkGetInstanceProcAddr(instance, 'vkGetPhysicalDeviceSurfacePresentModesKHR')
		self.presentModes = vkGetPhysicalDeviceSurfacePresentModesKHR(physical_device, surface)

		if DEBUG_MODE:
			for presentMode in self.presentModes:
				print(f"\t{vk_logging.log_present_mode(presentMode)}")


def choose_swapchain_surface_format(formats):

	for format in formats:
		if (format.format == VK_FORMAT_B8G8R8A8_UNORM
			and format.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR):
			return format

	return formats[0]

def choose_swapchain_present_mode(presentModes):
		
	if VK_PRESENT_MODE_MAILBOX_KHR in presentModes:
		return VK_PRESENT_MODE_MAILBOX_KHR

	return VK_PRESENT_MODE_FIFO_KHR

def choose_swapchain_extent(width, height, capabilities):
	
	extent = VkExtent2D(width, height)

	extent.width = min(
		capabilities.maxImageExtent.width, 
		max(capabilities.minImageExtent.width, extent.width)
	)

	extent.height = min(
		capabilities.maxImageExtent.height,
		max(capabilities.minImageExtent.height, extent.height)
	)

	return extent


class SwapChainBundle(RenderTarget):

	def __init__(self, queue_family:'vk_queue_families.QueueFamilyIndices', width, height):
		self.queue_family = queue_family

		self.vk_addr = None
		self.frames:list[vk_frame.SwapChainFrame] = []

		self.remake(width, height)

	def remake(self, width, height):
		vkDeviceWaitIdle(BVKC.logical_device.device)

		# if the original still exists, we need to destroy it
		if self.vk_addr is not None:
			self.destroy()

		support = SwapChainSupportDetails(self.queue_family.instance, BVKC.physical_device, self.queue_family.surface)
		format = choose_swapchain_surface_format(support.formats)
		presentMode = choose_swapchain_present_mode(support.presentModes)
		extent = choose_swapchain_extent(width, height, support.capabilities)
		super().__init__(format.format, extent)
		print(self.format, self.extent)

		image_count = min(
			support.capabilities.maxImageCount,
			support.capabilities.minImageCount + 1
		)

		"""
			* VULKAN_HPP_CONSTEXPR SwapchainCreateInfoKHR(
				VULKAN_HPP_NAMESPACE::SwapchainCreateFlagsKHR flags_         = {},
				VULKAN_HPP_NAMESPACE::SurfaceKHR              surface_       = {},
				uint32_t                                      minImageCount_ = {},
				VULKAN_HPP_NAMESPACE::Format                  imageFormat_   = VULKAN_HPP_NAMESPACE::Format::eUndefined,
				VULKAN_HPP_NAMESPACE::ColorSpaceKHR   imageColorSpace_  = VULKAN_HPP_NAMESPACE::ColorSpaceKHR::eSrgbNonlinear,
				VULKAN_HPP_NAMESPACE::Extent2D        imageExtent_      = {},
				uint32_t                              imageArrayLayers_ = {},
				VULKAN_HPP_NAMESPACE::ImageUsageFlags imageUsage_       = {},
				VULKAN_HPP_NAMESPACE::SharingMode     imageSharingMode_ = VULKAN_HPP_NAMESPACE::SharingMode::eExclusive,
				uint32_t                              queueFamilyIndexCount_ = {},
				const uint32_t *                      pQueueFamilyIndices_   = {},
				VULKAN_HPP_NAMESPACE::SurfaceTransformFlagBitsKHR preTransform_ =
				VULKAN_HPP_NAMESPACE::SurfaceTransformFlagBitsKHR::eIdentity,
				VULKAN_HPP_NAMESPACE::CompositeAlphaFlagBitsKHR compositeAlpha_ =
				VULKAN_HPP_NAMESPACE::CompositeAlphaFlagBitsKHR::eOpaque,
				VULKAN_HPP_NAMESPACE::PresentModeKHR presentMode_  = VULKAN_HPP_NAMESPACE::PresentModeKHR::eImmediate,
				VULKAN_HPP_NAMESPACE::Bool32         clipped_      = {},
				VULKAN_HPP_NAMESPACE::SwapchainKHR   oldSwapchain_ = {} 
			) VULKAN_HPP_NOEXCEPT
		"""

		if self.queue_family.graphics_family != self.queue_family.present_family:
			imageSharingMode = VK_SHARING_MODE_CONCURRENT
			queueFamilyIndexCount = 2
			pQueueFamilyIndices = [
				self.queue_family.graphics_family, self.queue_family.present_family
			]
		else:
			imageSharingMode = VK_SHARING_MODE_EXCLUSIVE
			queueFamilyIndexCount = 0
			pQueueFamilyIndices = None

		createInfo = VkSwapchainCreateInfoKHR(
			surface = self.queue_family.surface, minImageCount = image_count, imageFormat = format.format,
			imageColorSpace = format.colorSpace, imageExtent = extent, imageArrayLayers = 1,
			imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT, imageSharingMode = imageSharingMode,
			queueFamilyIndexCount = queueFamilyIndexCount, pQueueFamilyIndices = pQueueFamilyIndices,
			preTransform = support.capabilities.currentTransform, compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
			presentMode = presentMode, clipped = VK_TRUE
		)

		vkCreateSwapchainKHR = vkGetDeviceProcAddr(BVKC.logical_device.device, 'vkCreateSwapchainKHR')
		self.vk_addr = vkCreateSwapchainKHR(BVKC.logical_device.device, createInfo, None)

		vkGetSwapchainImagesKHR = vkGetDeviceProcAddr(BVKC.logical_device.device, 'vkGetSwapchainImagesKHR')
		images = vkGetSwapchainImagesKHR(BVKC.logical_device.device, self.vk_addr)

		self.frames = [
			vk_frame.SwapChainFrame(image, self)
			for image in images
			]

		self.max_frames = len(self.frames)
		self.current_frame = -1

		self.depth_image = Texture(
			format = vk_device.find_depth_format(BVKC.physical_device),
			extent = [width, height],
			tiling = VK_IMAGE_TILING_OPTIMAL,
			usage = VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT,
			aspect_mask = VK_IMAGE_ASPECT_DEPTH_BIT
		)

	def init_frame_buffers(self, render_pass, command_pool):
		for frame in self.frames:
			frame.init_buffers(render_pass, command_pool, [self.depth_image.image_view.vk_addr])

	def get_frame_buffer(self) -> FrameBuffer:
		'Used by BoxletVK to get the correct framebuffer to render to.'
		return self.frames[self.current_frame].frame_buffer

	def destroy(self):
		for frame in self.frames:
			frame.destroy()

		self.depth_image.destroy()

		destruction_function = vkGetDeviceProcAddr(BVKC.logical_device.device, 'vkDestroySwapchainKHR')
		destruction_function(BVKC.logical_device.device, self.vk_addr, None)
