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

		for presentMode in self.presentModes:
			print(f"\t{vk_logging.log_present_mode(presentMode)}")

def choose_swapchain_surface_format(formats):

	for format in formats:
		if (format.format == VK_FORMAT_B8G8R8A8_UNORM
			and format.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR):
			return format

	return formats[0]

def choose_swapchain_present_mode(presentModes):
		
	for presentMode in presentModes:
		if presentMode == VK_PRESENT_MODE_MAILBOX_KHR:
			return presentMode

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

class SwapChainBundle:

	def __init__(self, logical_device:'vk_device.LogicalDevice', queue_family:'vk_queue_families.QueueFamilyIndices', width, height):
		support = SwapChainSupportDetails(queue_family.instance, queue_family.physical_device, queue_family.surface)
		format = choose_swapchain_surface_format(support.formats)
		presentMode = choose_swapchain_present_mode(support.presentModes)
		self.extent = choose_swapchain_extent(width, height, support.capabilities)

		imageCount = min(
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

		if (queue_family.graphics_family != queue_family.present_family):
			imageSharingMode = VK_SHARING_MODE_CONCURRENT
			queueFamilyIndexCount = 2
			pQueueFamilyIndices = [
				queue_family.graphics_family, queue_family.present_family
			]
		else:
			imageSharingMode = VK_SHARING_MODE_EXCLUSIVE
			queueFamilyIndexCount = 0
			pQueueFamilyIndices = None

		createInfo = VkSwapchainCreateInfoKHR(
			surface = queue_family.surface, minImageCount = imageCount, imageFormat = format.format,
			imageColorSpace = format.colorSpace, imageExtent = self.extent, imageArrayLayers = 1,
			imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT, imageSharingMode = imageSharingMode,
			queueFamilyIndexCount = queueFamilyIndexCount, pQueueFamilyIndices = pQueueFamilyIndices,
			preTransform = support.capabilities.currentTransform, compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
			presentMode = presentMode, clipped = VK_TRUE
		)

		vkCreateSwapchainKHR = vkGetDeviceProcAddr(logical_device.device, 'vkCreateSwapchainKHR')
		self.swapchain = vkCreateSwapchainKHR(logical_device.device, createInfo, None)

		vkGetSwapchainImagesKHR = vkGetDeviceProcAddr(logical_device.device, 'vkGetSwapchainImagesKHR')
		images = vkGetSwapchainImagesKHR(logical_device.device, self.swapchain)

		self.frames:list[vk_frame.SwapChainFrame] = []
		for image in images:
			# TODO if allowed in the future
			# move this stuff to swapChainFrame and make a list comprehension

			components = VkComponentMapping(
				VK_COMPONENT_SWIZZLE_IDENTITY,
				VK_COMPONENT_SWIZZLE_IDENTITY,
				VK_COMPONENT_SWIZZLE_IDENTITY,
				VK_COMPONENT_SWIZZLE_IDENTITY,
			)

			subresource_range = VkImageSubresourceRange(
				aspectMask = VK_IMAGE_ASPECT_COLOR_BIT,
				baseMipLevel = 0, levelCount = 1,
				baseArrayLayer = 0, layerCount = 1
			)

			create_info = VkImageViewCreateInfo(
				image = image, viewType = VK_IMAGE_VIEW_TYPE_2D,
				format = format.format, components = components,
				subresourceRange = subresource_range
			)
			
			swapchain_frame = vk_frame.SwapChainFrame(logical_device, image, 
				vkCreateImageView(device = logical_device.device, pCreateInfo = create_info, pAllocator = None)
				)
			self.frames.append(swapchain_frame)


		self.format = format.format
		self.logical_device = logical_device
		# TODO watch this as it may need to be removed and added to self.destroy(...)
		# as a parameter
		# this ultimately depends on if the device number ever changes

		self.max_frames_in_flight = len(self.frames)
		self.current_frame = 0

	def increment_frame(self):
		self.current_frame += 1
		self.current_frame %= self.max_frames_in_flight

	def destroy(self):
		for frame in self.frames:
			frame.destroy()
			


		destruction_function = vkGetDeviceProcAddr(self.logical_device.device, 'vkDestroySwapchainKHR')
		destruction_function(self.logical_device.device, self.swapchain, None)
