from . import *


class Renderer:

	all_renderers:list['Renderer'] = [] # TODO move this to pipeline object

	def prepare(self, command_buffer):
		...

	@staticmethod
	def _destroy_all():
		for r in list(Renderer.all_renderers):
			r.destroy()


class TestRenderer(Renderer):
	def __init__(self, physical_device, logical_device, meshes:vk_mesh.MultiMesh, data_type):
		Renderer.all_renderers.append(self)

		self.meshes = meshes

		self.instance_buffer = vk_memory.InstanceBuffer(
			physical_device, 
			logical_device, 
			np.array([0], dtype = data_type)
		)

		indirect_data = np.array([0], dtype = vk_memory.Buffer.indirect_dtype)

		self.indirect_buffer = vk_memory.Buffer(
			physical_device, 
			logical_device,
			VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT,
			indirect_data
		)

		# for each model, there is a range of instance ids that are unused in memory
		self.memory_free = [[],[],[]]
		self.indirect_free = []

		self.draw_count = 0

	def create_indirect_group(self, model_id):
		if not self.indirect_free:
			f = self.indirect_buffer.data.shape[0] - 1 
			# TODO this managements needs to be refined
			# the -1 is because there is required to be at least 1 element when instancing the 

			self.indirect_free.extend([i+f for i in range(4)])
			self.indirect_buffer.expand_memory(4)
			self.instance_buffer.expand_memory(4 * 16)

		id = self.indirect_free.pop(0)
		self.indirect_buffer.data[id] = (
			self.meshes.index_counts[model_id],
			0,
			self.meshes.index_offsets[model_id],
			self.meshes.vertex_offsets[model_id],
			16 * id
		)
		self.indirect_buffer.needs_update = True
		self.draw_count += 1
		
		self.memory_free[model_id].extend([(id, i + id*16) for i in range(16)])

	def create_instance(self, model_id):
		if not self.memory_free[model_id]:
			self.create_indirect_group(model_id)

		indirect, id = self.memory_free[model_id].pop(0)

		self.indirect_buffer.data[indirect][1] += 1 # increase useage count
		self.indirect_buffer.needs_update = True

		return self.instance_buffer.data[id]
		# TODO probably return an object instead

	def prepare(self, command_buffer):
		self.meshes.bind(command_buffer)

		self.instance_buffer.update_memory()
		self.indirect_buffer.update_memory()
		
		self.instance_buffer.bind_to_vertex(command_buffer)

		vkCmdDrawIndexedIndirect(
			commandBuffer = command_buffer, 
			buffer = self.indirect_buffer.buffer,
			offset = 0,
			drawCount = self.draw_count,
			stride = 20
		)

	def destroy(self):
		self.instance_buffer.destroy()
		self.indirect_buffer.destroy()
		Renderer.all_renderers.remove(self)
