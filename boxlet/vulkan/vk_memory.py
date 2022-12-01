from . import *


class Buffer:

	def __init__(self, physical_device, logical_device, usage, data:np.ndarray = None) -> None:
		self.physical_device = physical_device
		self.logical_device = logical_device

		self.buffer_memory = None

		buffer_info = VkBufferCreateInfo(
			size = data.nbytes,
			usage = usage,
			sharingMode = VK_SHARING_MODE_EXCLUSIVE
		)

		self.buffer = vkCreateBuffer(
			device = logical_device.device, pCreateInfo = buffer_info, 
			pAllocator = None
		)

		self.allocate()

		if data is not None:
			self.map_memory(data)

	def allocate(self):
		memory_requirements = vkGetBufferMemoryRequirements(
			device = self.logical_device.device, buffer = self.buffer
		)

		alloc_info = VkMemoryAllocateInfo(
			allocationSize = memory_requirements.size,
			memoryTypeIndex = self.find_memory_type_index(
				self.physical_device,
				memory_requirements.memoryTypeBits,
				VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
				# TODO ? these may need to be adjusted
			)
		)

		self.buffer_memory = vkAllocateMemory(
			device = self.logical_device.device, pAllocateInfo = alloc_info,
			pAllocator = None
		)

		vkBindBufferMemory(
			device = self.logical_device.device, buffer = self.buffer,
			memory = self.buffer_memory, memoryOffset = 0
		)

	def map_memory(self, data:np.ndarray):
		memory_location = vkMapMemory(
			device = self.logical_device.device, memory = self.buffer_memory,
			offset = 0, size = data.nbytes, flags = 0
		)

		ffi.memmove(memory_location, data, data.nbytes)

		vkUnmapMemory(device = self.logical_device.device, memory = self.buffer_memory)

	def destroy(self):
		vkDestroyBuffer(
			device = self.logical_device.device, 
			buffer = self.buffer,
			pAllocator = None
		)

		vkFreeMemory(
			device = self.logical_device.device,
			memory = self.buffer_memory,
			pAllocator = None
		)

	@staticmethod
	def find_memory_type_index(physical_device, supported_memory_indices, requested_properties):
		memory_properties = vkGetPhysicalDeviceMemoryProperties(
			physicalDevice = physical_device
		)

		for i in range(memory_properties.memoryTypeCount):
			supported = supported_memory_indices & (1 << i)

			sufficient = (memory_properties.memoryTypes[i].propertyFlags & requested_properties) == requested_properties

			if supported and sufficient:
				return i

		return 0


class InstanceBuffer(Buffer):
	def __init__(self, physical_device, logical_device, data: np.ndarray = None) -> None:
		super().__init__(physical_device, logical_device, VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, data)

	#TODO add extra allocation methods

	def bind_to_vertex(self, command_buffer):
		vkCmdBindVertexBuffers(
			commandBuffer = command_buffer, firstBinding = 1, bindingCount = 1,
			pBuffers = [self.buffer],
			pOffsets = (0,)
		)
