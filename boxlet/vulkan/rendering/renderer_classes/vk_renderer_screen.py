from ... import Mesh
from ...vk_module import *
from . import Renderer

if TYPE_CHECKING:
	from ... import GraphicsPipeline

class ScreenRenderer(Renderer):

	_default_mesh:Mesh = None

	@staticmethod
	def get_screen_mesh():
		if not ScreenRenderer._default_mesh:
			ScreenRenderer._default_mesh = Mesh.gen_quad_2d(flip = True)
		return ScreenRenderer._default_mesh 

	def __init__(self, pipeline:'GraphicsPipeline|list[GraphicsPipeline]', defaults:dict[int] = {}, priority=0):
		super().__init__(pipeline, self.get_screen_mesh(), defaults, priority)

	def draw_command(self, command_buffer):
		vkCmdDrawIndexed(
			commandBuffer = command_buffer, 
			indexCount = 6,
			instanceCount = 1,
			firstIndex = 0,
			vertexOffset = 0,
			firstInstance = 0
		)
