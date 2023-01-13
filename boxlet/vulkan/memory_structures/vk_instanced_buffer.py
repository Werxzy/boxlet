from .. import Buffer, np
from ..vk_module import *


class InstancedData:
	def __init__(self, owner:'InstancedBufferSet', instance_id) -> None:
		self.owner = owner
		self.instance_id = instance_id

	# get and set functions are probably inefficient due to the number of getattr calls
	def get(self, attribute):
		return self.owner.instance_buffer.data[self.instance_id][attribute]

	def set(self, attribute, value):
		self.owner.instance_buffer.needs_update = True
		self.owner.instance_buffer.data[self.instance_id][attribute] = value

	def destroy(self):
		self.owner._destroy_instance(self.instance_id)
		self.owner = None


class InstancedBufferSet:
	def __init__(self, data_type:np.dtype) -> None:
		self._instances:list[InstancedData] = []

		self.instance_buffer = Buffer(
			VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
			np.array([], data_type)
		)	

		self.instance_count = 0

	def create_instance(self):
		new_id = self.instance_count
		self.instance_count += 1
		
		if new_id == len(self.instance_buffer.data):
			extend_amount = max(64, new_id)
			self.instance_buffer.expand_memory(extend_amount)
			self._instances.extend([None] * extend_amount)
			
		new_instance = InstancedData(self, new_id)
		self._instances[new_id] = new_instance
		self.instance_buffer.data[new_id] = 0
		return new_instance

	def _destroy_instance(self, instance_id):
		'removes an instance while moving the end of the indirect group into its place'
		self.instance_count -= 1
		end_id = self.instance_count

		if instance_id < end_id: # if the destroyed instance wasn't at the end
			self.instance_buffer.data[instance_id] = self.instance_buffer.data[end_id]
			moved_instance = self._instances[end_id]
			moved_instance.instance_id = instance_id
			self._instances[instance_id] = moved_instance
			self.instance_buffer.needs_update = True

		self._instances[end_id] = None

	def bind_to_vertex(self, command_buffer):
		vkCmdBindVertexBuffers(
			commandBuffer = command_buffer, firstBinding = 1, bindingCount = 1,
			pBuffers = [self.instance_buffer.buffer],
			pOffsets = (0,)
		)

	def sort_instances(self, attribute):
		'''
		Reorders the instances and data based on the given attribute.

		This can be an expensive operation and is meant to be done sparingly.
		'''

		sorted_index = np.argsort(self.instance_buffer.data[:self.instance_count][attribute], axis = 0).flatten()
		self.instance_buffer.data[:self.instance_count] = np.take_along_axis(
			self.instance_buffer.data[:self.instance_count], sorted_index, axis = 0)
		
		self._instances:list[InstancedData] = [self._instances[i] for i in sorted_index] + [None for _ in range(len(self._instances) - self.instance_count)]
		for i, inst in enumerate(self._instances):
			if inst:
				inst.instance_id = i
			else:
				break

		self.instance_buffer.needs_update = True

	def update_memory(self):
		self.instance_buffer.update_memory()

	def destroy(self):
		self.instance_buffer.destroy()

