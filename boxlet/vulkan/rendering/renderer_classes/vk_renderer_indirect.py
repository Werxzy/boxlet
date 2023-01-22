from ... import IndirectBufferSet
from ...vk_module import *
from . import Renderer

if TYPE_CHECKING:
	from ... import GraphicsPipeline, MultiMesh


class IndirectRenderer(Renderer):
	def __init__(self, pipeline:'GraphicsPipeline', meshes:'MultiMesh', defaults:dict[int] = {}, priority = 0):
		super().__init__(pipeline, meshes, defaults, priority)

		self.buffer_set = IndirectBufferSet(
			meshes,
			pipeline.shader_attribute.data_type
		)

	def create_instance(self, model_id):
		return self.buffer_set.create_instance(model_id)

	def is_enabled(self):
		return self.buffer_set.indirect_count > 0

	def draw_command(self, command_buffer):
		vkCmdDrawIndexedIndirect(
			commandBuffer = command_buffer, 
			buffer = self.buffer_set.indirect_buffer.buffer,
			offset = 0,
			drawCount = self.buffer_set.indirect_count,
			stride = 20
		)
