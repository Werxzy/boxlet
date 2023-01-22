from ... import InstancedBufferSet
from ...vk_module import *
from . import Renderer

if TYPE_CHECKING:
	from ... import GraphicsPipeline, Mesh


class InstancedRenderer(Renderer):
	def __init__(self, pipeline:'GraphicsPipeline|list[GraphicsPipeline]', mesh:'Mesh', defaults:dict[int] = {}, priority = 0):
		super().__init__(pipeline, mesh, defaults, priority)

		self.buffer_set = InstancedBufferSet(
			self.pipeline.shader_attribute.data_type
		)

	def create_instance(self):
		return self.buffer_set.create_instance()

	def is_enabled(self):
		return self.buffer_set.instance_count > 0

	def draw_command(self, command_buffer):
		vkCmdDrawIndexed(
			commandBuffer = command_buffer, 
			indexCount = self.mesh.index_count,
			instanceCount = self.buffer_set.instance_count,
			firstIndex = 0,
			vertexOffset = 0,
			firstInstance = 0
		)
