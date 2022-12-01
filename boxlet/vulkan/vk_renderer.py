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
	def __init__(self, physical_device, logical_device, meshes:vk_mesh.MultiMesh, pos_data:np.ndarray, model):
		Renderer.all_renderers.append(self)

		self.meshes = meshes
		self.model = model

		self.instance_buffer = vk_memory.InstanceBuffer(
			physical_device, 
			logical_device, 
			pos_data
		)

		indirect_data = np.array([(		
			self.meshes.index_counts[model],
			10,
			self.meshes.index_offsets[model],
			self.meshes.vertex_offsets[model],
			0)], 
			dtype = vk_memory.Buffer.indirect_dtype)

		self.indirect_buffer = vk_memory.Buffer(
			physical_device, 
			logical_device,
			VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT,
			indirect_data
		)

	def prepare(self, command_buffer):
		self.meshes.bind(command_buffer)
		
		self.instance_buffer.bind_to_vertex(command_buffer)

		vkCmdDrawIndexedIndirect(
			commandBuffer = command_buffer, 
			buffer = self.indirect_buffer.buffer,
			offset = 0,
			drawCount = 1,
			stride = 20
		)

	def destroy(self):
		self.instance_buffer.destroy()
		self.indirect_buffer.destroy()
		Renderer.all_renderers.remove(self)
