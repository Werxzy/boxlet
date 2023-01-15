from ... import InstancedBufferSet
from ...vk_module import *
from . import Renderer

if TYPE_CHECKING:
	from ... import GraphicsPipeline, Mesh


class InstancedRenderer(Renderer):
	def __init__(self, pipeline:'GraphicsPipeline', mesh:'Mesh', defaults:dict[int] = {}, priority = 0):
		super().__init__(pipeline, mesh, defaults, priority)

		self.buffer_set = InstancedBufferSet(
			pipeline.shader_attribute.data_type
		)

	def create_instance(self):
		return self.buffer_set.create_instance()

	def begin(self, command_buffer):
		if self.buffer_set.instance_count == 0:
			return

		super().begin(command_buffer)

		vkCmdDrawIndexed(
			commandBuffer = command_buffer, 
			indexCount = self.mesh.index_count,
			instanceCount = self.buffer_set.instance_count,
			firstIndex = 0,
			vertexOffset = 0,
			firstInstance = 0
		)
