from .. import Buffer, np
from ..vk_module import *

if TYPE_CHECKING:
	from .. import MultiMesh


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
		if isinstance(model_id, str):
			model_id = self._meshes.names[model_id]

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

