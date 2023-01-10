from ... import InstancedBufferSet
from ...vk_module import *
from . import PushConstantManager, Renderer, RendererBindings

if TYPE_CHECKING:
	from ... import GraphicsPipeline, Mesh


class InstancedRenderer(Renderer):
	def __init__(self, pipeline:'GraphicsPipeline', mesh:'Mesh', defaults:dict[int], priority = 0):
		super().__init__(priority)
		
		self.mesh = mesh
		mesh.init_buffers()

		self.buffer_set = InstancedBufferSet(
			pipeline.shader_attribute.data_type
		)
		
		pipeline.attach(self)
		self.pipeline = pipeline
		self.attributes = RendererBindings(pipeline, defaults)
		self.push_constants = PushConstantManager(pipeline.pipeline_layout)

	def create_instance(self):
		return self.buffer_set.create_instance()

	def begin(self, command_buffer):
		count = len(self.buffer_set.instance_buffer.data)
		if count == 0:
			return

		super().begin(command_buffer)

		vkCmdDrawIndexed(
			commandBuffer = command_buffer, 
			indexCount = self.mesh.index_count,
			instanceCount = count,
			firstIndex = 0,
			vertexOffset = 0,
			firstInstance = 0
		)
