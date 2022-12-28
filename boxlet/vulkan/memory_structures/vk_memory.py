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
			physicalDevice = BVKC.physical_device
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


class InstanceData:
	def __init__(self, owner:'InstanceBufferSet', indirect_id, instance_id) -> None:
		self.owner = owner
		self.indirect_id = indirect_id
		self.instance_id = instance_id

	# get and set functions are probably inefficient due to the number of getattr calls
	def get(self, attribute):
		return self.owner.instance_buffer.data[self.instance_id][attribute]

	def set(self, attribute, value):
		self.owner.instance_buffer.data[self.instance_id][attribute] = value

	def destroy(self):
		self.owner._destroy_instance(self.indirect_id, self.instance_id)
		self.owner = None


class InstanceBufferSet:
	def __init__(self, meshes:'MultiMesh', data_type: np.dtype) -> None:
		
		# TODO more control over the buffer size increase, indirect buffer size, etc

		self._instances:list[InstanceData] = []
		
		self.instance_buffer = Buffer(
			VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
			np.array([], data_type)
		)

		self.indirect_buffer = Buffer(
			VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT,
			np.array([], Buffer.indirect_dtype)
		)

		self._meshes = meshes

		self._indirect_max = 0
		# Max number of indirect draw calls that can fit in the current buffer
		self.indirect_count = 0
		# Number of indirect draw calls
		self._indirect_unfilled:list[list[int]] = [list() for _ in range(meshes.mesh_count)]
		# list of indirect structs ids that are in use, but have not been filled yet

	def create_indirect_group(self, model_id):
		if self._indirect_max == self.indirect_count:
			self.indirect_buffer.expand_memory(4)
			self.instance_buffer.expand_memory(4 * 16)
			self.instance_buffer.needs_update = True
			self._indirect_max += 4
			self._instances.extend(None for _ in range(4 * 16))

		ind_id = self.indirect_count
		self.indirect_count += 1
		self._indirect_unfilled[model_id].append(ind_id)

		self.indirect_buffer.data[ind_id] = (
			self._meshes.index_counts[model_id],
			0,
			self._meshes.index_offsets[model_id],
			self._meshes.vertex_offsets[model_id],
			16 * ind_id 
			# TODO more dynamic offset if each model has a different max count
		)

		self.indirect_buffer.needs_update = True
		# the needs update here is a bit redundant, but might be needed

	def create_instance(self, model_id):
		# TODO, add function for creating multiple instances
		if not self._indirect_unfilled[model_id]:
			self.create_indirect_group(model_id)

		ind_id = self._indirect_unfilled[model_id][0]
		count = self.indirect_buffer.data[ind_id][1]
		id = self.indirect_buffer.data[ind_id][4] + count
		count += 1
		self.indirect_buffer.data[ind_id][1] = count

		if count == 16: # TODO configurable max count
			self._indirect_unfilled[model_id].pop(0)
			# max count reached, consider filled

		self.instance_buffer.needs_update = True
		self.indirect_buffer.needs_update = True
		
		self._instances[id] = new_instance = InstanceData(self, ind_id, id)
		return new_instance

	def _destroy_instance(self, indirect_id, instance_id):
		'removes an instance while moving the end of the indirect group into its place'
		count = self.indirect_buffer.data[indirect_id][1] - 1
		self.indirect_buffer.data[indirect_id][1] = count
		end_id = count + self.indirect_buffer.data[indirect_id][4]
		self.indirect_buffer.needs_update = True

		if instance_id < end_id: # if the destroyed instance wasn't at the end
			self.instance_buffer.data[instance_id] = self.instance_buffer.data[end_id]
			moved_instance = self._instances[end_id]
			moved_instance.instance_id = instance_id
			self._instances[instance_id] = moved_instance
			self.instance_buffer.needs_update = True

		self._instances[end_id] = None

	# def repack(self):
	# 	moves all the instances into as few groups as possible and removes the empty groups
	#	potentially puts all the instances with the same model into a single group
	#	probably a time consuming task
	#	potentially add a function for just removing empty groups

	def bind_to_vertex(self, command_buffer):
		vkCmdBindVertexBuffers(
			commandBuffer = command_buffer, firstBinding = 1, bindingCount = 1,
			pBuffers = [self.instance_buffer.buffer],
			pOffsets = (0,)
		)

	def update_memory(self):
		self.indirect_buffer.update_memory()
		self.instance_buffer.update_memory()

	def destroy(self):
		self.indirect_buffer.destroy()
		self.instance_buffer.destroy()

