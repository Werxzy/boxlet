from ... import Mesh
from ...vk_module import *
from . import PushConstantManager, Renderer, RendererBindings

if TYPE_CHECKING:
	from ... import GraphicsPipeline

class ScreenRenderer(Renderer):

	default_mesh:Mesh = None

	def get_screen_mesh():
		if not ScreenRenderer.default_mesh:
			ScreenRenderer.default_mesh = Mesh(
				vertices = {
					'position':[
						-1,-1, 1,-1,  1,1, -1,1,
					], 
					'texcoord':[
						0,0, 1,0, 1,1, 0,1
					],
				},
				indices = [0,1,2, 0,2,3],
				dim = 2) 
		return ScreenRenderer.default_mesh 

	def __init__(self, pipeline:'GraphicsPipeline', defaults:dict[int], priority=0):
		super().__init__(priority)
		
		ScreenRenderer.default_mesh.init_buffers()
		self.mesh = ScreenRenderer.default_mesh

		pipeline.attach(self)
		self.pipeline = pipeline
		self.attributes = RendererBindings(pipeline, defaults)
		self.push_constants = PushConstantManager(pipeline.pipeline_layout)

	def begin(self, command_buffer):
		super().begin(command_buffer)

		vkCmdDrawIndexed(
			commandBuffer = command_buffer, 
			indexCount = 6,
			instanceCount = 1,
			firstIndex = 0,
			vertexOffset = 0,
			firstInstance = 0
		)
