from ...vk_module import *
from . import (InstanceBufferSet, PushConstantManager, Renderer,
               RendererBindings)

if TYPE_CHECKING:
	from ... import GraphicsPipeline, MultiMesh


class IndirectRenderer(Renderer):
	def __init__(self, pipeline:'GraphicsPipeline', meshes:'MultiMesh', defaults:dict[int], priority = 0):
		super().__init__(priority)
		
		self.meshes = meshes
		meshes.init_buffers()

		self.buffer_set = InstanceBufferSet(
			meshes,
			pipeline.shader_attribute.data_type
		)
		
		pipeline.attach(self)
		self.pipeline = pipeline
		self.attributes = RendererBindings(pipeline, defaults)
		self.push_constants = PushConstantManager(pipeline.pipeline_layout)

	def create_instance(self, model_id):
		return self.buffer_set.create_instance(model_id)

	def begin(self, command_buffer):
		if self.buffer_set.indirect_count == 0:
			return

		self.meshes.bind(command_buffer)

		self.push_constants.push(command_buffer)
		self.buffer_set.update_memory()
		self.buffer_set.bind_to_vertex(command_buffer)
		self.attributes.bind(command_buffer)

		vkCmdDrawIndexedIndirect(
			commandBuffer = command_buffer, 
			buffer = self.buffer_set.indirect_buffer.buffer,
			offset = 0,
			drawCount = self.buffer_set.indirect_count,
			stride = 20
		)

	def on_destroy(self):
		self.buffer_set.destroy()
		self.attributes.destroy()
