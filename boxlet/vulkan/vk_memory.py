from . import *


class Buffer:

	indirect_dtype = np.dtype([    
		('indexCount', 'u4'),
   		('instanceCount', 'u4'),
   		('firstIndex', 'u4'),
   		('vertexOffset', 'i4'),
   		('firstInstance', 'u4'),
	])

	def __init__(self, physical_device, logical_device, usage, data:np.ndarray = None) -> None:
		self.physical_device = physical_device
		self.logical_device = logical_device
		self.usage = usage
		self.data = data if data is not None else np.array([], np.float32)
		self.size = self.data.nbytes # TODO not sure if zero bytes will mess things up

		self.buffer = None
		self.buffer_memory = None

		self.needs_update = False
		self.size_changed = False

		if self.size > 0:
			self.create_buffer()
			self.allocate()
			self.map_memory(data)

	def create_buffer(self):
		buffer_info = VkBufferCreateInfo(
			size = self.size,
			usage = self.usage,
			sharingMode = VK_SHARING_MODE_EXCLUSIVE
		)

		self.buffer = vkCreateBuffer(
			device = self.logical_device.device, pCreateInfo = buffer_info, 
			pAllocator = None
		)

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

	def map_memory(self, data:np.ndarray, offset = 0):
		memory_location = vkMapMemory(
			device = self.logical_device.device, memory = self.buffer_memory,
			offset = offset, size = data.nbytes, flags = 0
		)

		ffi.memmove(memory_location, data, data.nbytes)

		vkUnmapMemory(device = self.logical_device.device, memory = self.buffer_memory)

	def destroy(self):
		if self.buffer != None:
			vkDestroyBuffer(
				device = self.logical_device.device, 
				buffer = self.buffer,
				pAllocator = None
			)

		if self.buffer_memory != None:
			vkFreeMemory(
				device = self.logical_device.device,
				memory = self.buffer_memory,
				pAllocator = None
			)

	def update_memory(self):
		if not self.needs_update: return
		self.needs_update = False

		if self.size_changed: # data size changed, need to reshape buffer
			self.size_changed = False
			self.destroy()
			self.create_buffer()
			self.allocate()
			self.map_memory(self.data)
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
	def __init__(self, physical_device, logical_device, meshes:'vk_mesh.MultiMesh', data_type: np.dtype) -> None:
		
		# TODO more control over the buffer size increase, indirect buffer size, etc

		self._instances:list[InstanceData] = []
		
		self.instance_buffer = Buffer(
			physical_device, 
			logical_device, 
			VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
			np.array([], data_type)
		)

		self.indirect_buffer = Buffer(
			physical_device, 
			logical_device,
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
		# TODO, add function for creating multiple meshes
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


class InstanceBufferLayout:

	# NOTE binding is currently expected to always be set to 1 for instance buffers

	def __init__(self, layout:list[tuple[str, str, int]]) -> None:
		#layout is a list of (name, datatype, location)
		
		self.vertex_attributes:list[tuple[int, int, int]] = []
		offset = 0
		dtype_build = []

		for name, data_type, location in layout:
			if data_type == 'vec4':
				dtype_build.append((name, '(4,)f4'))
				self.vertex_attributes.append((location, VK_FORMAT_R32G32B32A32_SFLOAT, offset))
				offset += 16

			elif data_type == 'mat4':
				dtype_build.append((name, '(4,4)f4'))
				for _ in range(4):
					self.vertex_attributes.append((location, VK_FORMAT_R32G32B32A32_SFLOAT, offset))
					location += 1
					offset += 16

		self.dtype = np.dtype(dtype_build)
		self.stride = offset

	def get_binding_description(self):
		return VkVertexInputBindingDescription(
			binding = 1, stride = self.stride, inputRate = VK_VERTEX_INPUT_RATE_INSTANCE
		)	

	def get_attribute_descriptions(self):
		return [
			VkVertexInputAttributeDescription(
				binding = 1, location = loc, format = form, offset = off
			)
			for (loc, form, off) in self.vertex_attributes
		]
