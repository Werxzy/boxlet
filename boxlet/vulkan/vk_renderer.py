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

		self.buffer_set = vk_memory.InstanceBufferSet(
			physical_device,
			logical_device,
			meshes,
			data_type
		)

	def create_instance(self, model_id):
		return self.buffer_set.create_instance(model_id)

	def prepare(self, command_buffer):
		if self.buffer_set.indirect_count == 0:
			return

		self.meshes.bind(command_buffer)

		self.buffer_set.update_memory()
		self.buffer_set.bind_to_vertex(command_buffer)

		vkCmdDrawIndexedIndirect(
			commandBuffer = command_buffer, 
			buffer = self.buffer_set.indirect_buffer.buffer,
			offset = 0,
			drawCount = self.buffer_set.indirect_count,
			stride = 20
		)

	def destroy(self):
		self.buffer_set.destroy()
		Renderer.all_renderers.remove(self)
