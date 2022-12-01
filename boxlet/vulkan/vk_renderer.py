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

	def prepare(self, command_buffer):
		self.meshes.bind(command_buffer)
		
		self.instance_buffer.bind_to_vertex(command_buffer)
		
		vkCmdDrawIndexed(
			commandBuffer = command_buffer, 
			indexCount = self.meshes.index_counts[self.model],
			instanceCount = 10,
			firstIndex = self.meshes.index_offsets[self.model],
			vertexOffset = self.meshes.vertex_offsets[self.model],
			firstInstance = 0
		)

	def destroy(self):
		self.instance_buffer.destroy()
		Renderer.all_renderers.remove(self)
