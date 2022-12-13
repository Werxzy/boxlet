from .vk_module import *
from . import *
import pygame

class Texture(TrackedInstances):
	def __init__(self, input_image:pygame.Surface) -> None:
		
		self.format = VK_FORMAT_R8G8B8A8_UNORM
		self.extent = VkExtent3D(input_image.get_width(), input_image.get_height(), 1)
		self.image_layout = VK_IMAGE_LAYOUT_UNDEFINED

		image_create_info = VkImageCreateInfo(
			imageType = VK_IMAGE_TYPE_2D,
			format = self.format,
			extent = self.extent,
			mipLevels = 1,
			arrayLayers = 1,
			samples = VK_SAMPLE_COUNT_1_BIT,
			tiling = VK_IMAGE_TILING_LINEAR,
			usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
			sharingMode = VK_SHARING_MODE_EXCLUSIVE,
			initialLayout = self.image_layout
		)

		self.image = vkCreateImage(BVKC.logical_device.device, image_create_info, None)

		self.create_sampler()

		self.allocate()

		staging_buffer = vk_memory.Buffer(VK_BUFFER_USAGE_TRANSFER_SRC_BIT, pygame.image.tostring(input_image, "RGBA", True))

		self.transition_image_layout(VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL)
		self.copy_buffer_to_image(staging_buffer.buffer)
		self.transition_image_layout(VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL)

		staging_buffer.destroy()

		self.image_view = vk_frame.ImageView(self.image, self.format, self.extent)

	def allocate(self):
		memory_requirements = vkGetImageMemoryRequirements(
			BVKC.logical_device.device, self.image
		)
		
		alloc_info = VkMemoryAllocateInfo(
			allocationSize = memory_requirements.size,
			memoryTypeIndex = vk_memory.Buffer.find_memory_type_index(
				memory_requirements.memoryTypeBits,
				VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT
				# TODO ? these may need to be adjusted
			)
		)

		self.image_memory = vkAllocateMemory(
			BVKC.logical_device.device, alloc_info,
			None
		)

		vkBindImageMemory(
			BVKC.logical_device.device, self.image,
			self.image_memory, 0
		)

	def transition_image_layout(self, new_layout):
		temp_command_buffer = CommandBuffer(BVKC.command_pool)
		temp_command_buffer.single_time_begin()

		subresource = VkImageSubresourceRange(VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1)

		barrier = VkImageMemoryBarrier(
			oldLayout = self.image_layout,
			newLayout = new_layout,
			srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
			dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
			image = self.image,
			subresourceRange = subresource
		)

		if self.image_layout == VK_IMAGE_LAYOUT_UNDEFINED and new_layout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL:
			barrier.srcAccessMask = 0
			barrier.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT
			src_stage = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT
			dst_stage = VK_PIPELINE_STAGE_TRANSFER_BIT

		elif self.image_layout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL and new_layout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL:
			barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT
			barrier.dstAccessMask = VK_ACCESS_SHADER_READ_BIT
			src_stage = VK_PIPELINE_STAGE_TRANSFER_BIT
			dst_stage = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT

		else:
			raise Exception('unsupported layout transition')

		# TODO allow for more controlled transitions

		vkCmdPipelineBarrier(
			temp_command_buffer.vk_addr, 
			src_stage, dst_stage,
			0, 0, None, 0, None, 1, [barrier]
		)

		temp_command_buffer.single_time_end()
		self.image_layout = new_layout

	def copy_buffer_to_image(self, buffer):
		temp_command_buffer = CommandBuffer(BVKC.command_pool)
		temp_command_buffer.single_time_begin()

		subresource = VkImageSubresourceLayers(VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1)

		region = VkBufferImageCopy(0, 0, 0, subresource, [0, 0, 0], self.extent)

		vkCmdCopyBufferToImage(
			temp_command_buffer.vk_addr,
			buffer,
			self.image,
			self.image_layout,
			1, [region]
		)

		temp_command_buffer.single_time_end()

	def create_sampler(self):
		properties = vkGetPhysicalDeviceProperties(BVKC.physical_device)

		sampler_create_info = VkSamplerCreateInfo(
			magFilter = VK_FILTER_LINEAR,
			minFilter = VK_FILTER_LINEAR,
			mipmapMode = VK_SAMPLER_MIPMAP_MODE_LINEAR,
			addressModeU = VK_SAMPLER_ADDRESS_MODE_REPEAT,
			addressModeV = VK_SAMPLER_ADDRESS_MODE_REPEAT,
			addressModeW = VK_SAMPLER_ADDRESS_MODE_REPEAT,
			anisotropyEnable = VK_TRUE,
			maxAnisotropy = properties.limits.maxSamplerAnisotropy,
			compareEnable = VK_FALSE,
			compareOp = VK_COMPARE_OP_ALWAYS,
			borderColor = VK_BORDER_COLOR_INT_OPAQUE_BLACK,
			unnormalizedCoordinates = VK_FALSE
		)

		self.sampler = vkCreateSampler(BVKC.logical_device.device, sampler_create_info, None)
		# TODO ? there will probably be a lot of duplicate samplers
		# could consolidate and reuse the unique ones somehow.
	
	def on_destroy(self):
		self.image_view.destroy()
		vkDestroySampler(BVKC.logical_device.device, self.sampler, None)
		vkDestroyImage(BVKC.logical_device.device, self.image, None)
		vkFreeMemory(BVKC.logical_device.device, self.image_memory, None)
