from .vk_module import *
from . import *
import pygame

class Texture(TrackedInstances):
	def __init__(self, input_image:pygame.Surface = None,
			format = VK_FORMAT_R8G8B8A8_UNORM,
			extent:list|tuple|None = None,
			image_layout = VK_IMAGE_LAYOUT_UNDEFINED,
			tiling = VK_IMAGE_TILING_LINEAR,
			usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
			aspect_mask = VK_IMAGE_ASPECT_COLOR_BIT,
			access_mask = 0,
			stage_mask = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT
		) -> None:

		if input_image:
			image_layout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL
			access_mask = VK_ACCESS_SHADER_READ_BIT
			stage_mask = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT
		
		self.format = format
		self.image_layout = image_layout
		self.tiling = tiling
		self.usage = usage
		self.image = None
		self.aspect_mask = aspect_mask

		self.access_mask = access_mask
		self.stage_mask = stage_mask

		if input_image:
			extent = [input_image.get_width(), input_image.get_height(), 1]
		elif not extent:
			raise Exception('No valid extent provided.')

		self.remake(extent, input_image)

	def remake(self, extent, input_image = None):
		# so that a reference to the Texture is kept
		# and the vulkan changes can be tracked

		if self.image:
			self.on_destroy()

		# stores and resets the following so that the new image can be transitioned.
		image_layout = self.image_layout
		access_mask = self.access_mask
		stage_mask = self.stage_mask

		self.image_layout = VK_IMAGE_LAYOUT_UNDEFINED
		self.access_mask = 0
		self.stage_mask = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT

		if extent:
			if len(extent) == 3:
				self.extent = VkExtent3D(*extent)
			else:
				self.extent = VkExtent3D(*extent, 1)

		image_create_info = VkImageCreateInfo(
			imageType = VK_IMAGE_TYPE_2D,
			format = self.format,
			extent = self.extent,
			mipLevels = 1,
			arrayLayers = 1,
			samples = VK_SAMPLE_COUNT_1_BIT,
			tiling = self.tiling,
			usage = self.usage,
			sharingMode = VK_SHARING_MODE_EXCLUSIVE,
			initialLayout = self.image_layout
		)

		self.image = vkCreateImage(BVKC.logical_device.device, image_create_info, None)

		self.create_sampler()

		self.allocate()

		self.image_view = vk_frame.ImageView(self.image, self.format, self.extent, self.aspect_mask)

		if input_image:
			staging_buffer = vk_memory.Buffer(VK_BUFFER_USAGE_TRANSFER_SRC_BIT, pygame.image.tostring(input_image, "RGBA", True))

			self.transition_image_layout(
				VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
				VK_ACCESS_TRANSFER_WRITE_BIT,
				VK_PIPELINE_STAGE_TRANSFER_BIT
			)
			self.copy_buffer_to_image(staging_buffer.buffer)
			staging_buffer.destroy()

		if access_mask:
			self.transition_image_layout(
				image_layout,
				access_mask,
				stage_mask
			)

	def allocate(self):
		memory_requirements = vkGetImageMemoryRequirements(
			BVKC.logical_device.device, self.image
		)
		
		alloc_info = VkMemoryAllocateInfo(
			allocationSize = memory_requirements.size,
			memoryTypeIndex = vk_memory.Buffer.find_memory_type_index(
				memory_requirements.memoryTypeBits,
				VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT
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

	def transition_image_layout(self, new_layout, new_access, new_stage, command_buffer = None):
		if (self.image_layout == new_layout 
				and self.access_mask == new_access
				and self.stage_mask == new_stage): 
			return

		if command_buffer is None:
			temp_command_buffer = CommandBuffer(BVKC.command_pool)
			command_buffer_addr = temp_command_buffer.vk_addr
			temp_command_buffer.single_time_begin()
		else:
			command_buffer_addr = command_buffer

		subresource = VkImageSubresourceRange(self.aspect_mask, 0, 1, 0, 1)

		barrier = VkImageMemoryBarrier(
			srcAccessMask = self.access_mask,
			dstAccessMask = new_access,
			oldLayout = self.image_layout,
			newLayout = new_layout,
			srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
			dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
			image = self.image,
			subresourceRange = subresource
		)

		vkCmdPipelineBarrier(
			command_buffer_addr, 
			self.stage_mask, new_stage,
			0, 0, None, 0, None, 1, [barrier]
		)

		if command_buffer is None:
			temp_command_buffer.single_time_end()

		self.image_layout = new_layout
		self.access_mask = new_access
		self.stage_mask = new_stage

	def copy_buffer_to_image(self, buffer):
		temp_command_buffer = CommandBuffer(BVKC.command_pool)
		temp_command_buffer.single_time_begin()

		subresource = VkImageSubresourceLayers(self.aspect_mask, 0, 0, 1)

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
