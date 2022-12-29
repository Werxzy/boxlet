from ..vk_module import *
from .. import *


class Buffer:

	indirect_dtype = np.dtype([    
		('indexCount', 'u4'),
   		('instanceCount', 'u4'),
   		('firstIndex', 'u4'),
   		('vertexOffset', 'i4'),
   		('firstInstance', 'u4'),
	])

	def __init__(self, usage, data:np.ndarray = None) -> None:
		if data is None:
			self.data = np.array([], np.float32)
		elif isinstance(data, np.ndarray):
			self.data = data
		else:
			self.data = np.array(data)

		self.size = self.data.nbytes
		self.usage = usage

		self.buffer = None
		self.buffer_memory = None

		self.needs_update = False
		self.size_changed = False

		if self.size > 0:
			self.full_allocation()

	def full_allocation(self):
		self.create_buffer()
		self.allocate()
		self.map_memory(self.data)

	def create_buffer(self):
		buffer_info = VkBufferCreateInfo(
			size = self.size,
			usage = self.usage,
			sharingMode = VK_SHARING_MODE_EXCLUSIVE
		)

		self.buffer = vkCreateBuffer(
			device = BVKC.logical_device.device, pCreateInfo = buffer_info, 
			pAllocator = None
		)

	def allocate(self):
		memory_requirements = vkGetBufferMemoryRequirements(
			device = BVKC.logical_device.device, buffer = self.buffer
		)

		alloc_info = VkMemoryAllocateInfo(
			allocationSize = memory_requirements.size,
			memoryTypeIndex = Buffer.find_memory_type_index(
				memory_requirements.memoryTypeBits,
				VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
			)
		)

		self.buffer_memory = vkAllocateMemory(
			device = BVKC.logical_device.device, pAllocateInfo = alloc_info,
			pAllocator = None
		)

		vkBindBufferMemory(
			device = BVKC.logical_device.device, buffer = self.buffer,
			memory = self.buffer_memory, memoryOffset = 0
		)

	def map_memory(self, data:np.ndarray, offset = 0):
		memory_location = vkMapMemory(
			device = BVKC.logical_device.device, memory = self.buffer_memory,
			offset = offset, size = data.nbytes, flags = 0
		)

		ffi.memmove(memory_location, data, data.nbytes)

		vkUnmapMemory(device = BVKC.logical_device.device, memory = self.buffer_memory)

	def destroy(self):
		# vkDeviceWaitIdle(BVKC.logical_device.device)
		vkQueueWaitIdle(BVKC.graphics_queue)
		# I would rather not need this
		if self.buffer != None:
			vkDestroyBuffer(
				device = BVKC.logical_device.device, 
				buffer = self.buffer,
				pAllocator = None
			)

		if self.buffer_memory != None:
			vkFreeMemory(
				device = BVKC.logical_device.device,
				memory = self.buffer_memory,
				pAllocator = None
			)

	def update_memory(self):
		if not self.needs_update: return
		self.needs_update = False

		if self.size_changed: # data size changed, need to reshape buffer
			self.size_changed = False
			self.destroy()
			self.full_allocation()
		else:
			self.map_memory(self.data)
			# TODO potentially allow tracking of what memory needs to be updated

	def expand_memory(self, amount):
		'expands the data with the given amount of instances of the data\'s dtype.'

		self.data = np.concatenate([self.data, np.array([0] * amount, dtype=self.data.dtype)])
		self.size = self.data.nbytes
		self.size_changed = True
		self.needs_update = True

	@staticmethod
	def find_memory_type_index(supported_memory_indices, requested_properties):
		memory_properties = vkGetPhysicalDeviceMemoryProperties(
			physicalDevice = BVKC.physical_device.vk_addr
		)

		for i in range(memory_properties.memoryTypeCount):
			supported = supported_memory_indices & (1 << i)

			sufficient = (memory_properties.memoryTypes[i].propertyFlags & requested_properties) == requested_properties

			if supported and sufficient:
				return i

		return 0


class UniformBufferGroup:
	'''
	Holds a list of buffers for the use of uniform buffer descriptor set.
	
	They all share the same data, but only update in the gpu when calling
	update_memory() on the buffer associated with the current swapchain frame.
	'''

	def __init__(self, data, count) -> None:
		self.data = np.array(data)

		self.buffers = [
			Buffer(VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT, self.data)
			for _ in range(count)
		]
		# all the buffers will share the same numpy array 
		# due to 'self.data = data' in Buffer

	def update_memory(self, i):
		'only updates memory for a buffer that is currently not in use.'
		self.buffers[i].update_memory()

	def __setitem__(self, key, value):
		'Prefered method of updating values in the buffers.'

		# sets the value in the data and notifies 
		# the buffers that they need to update
		self.data[key] = value

		for b in self.buffers:
			b.needs_update = True

	def __getitem__(self, key):
		return self.data[key]

	def destroy(self):
		for b in self.buffers:
			b.destroy()

