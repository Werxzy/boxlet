from .vk_module import *
from . import *


class Renderer(TrackedInstances):

	def prepare(self, command_buffer):
		...


class IndirectRenderer(Renderer):
	def __init__(self, pipeline:GraphicsPipeline, meshes:vk_mesh.MultiMesh, data_type):

		self.meshes = meshes

		self.buffer_set = vk_memory.InstanceBufferSet(
			meshes,
			data_type
		)
		
		pipeline.attach(self.prepare)

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

	def on_destroy(self):
		self.buffer_set.destroy()

