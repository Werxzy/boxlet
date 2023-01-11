from .. import RenderingStep, Shader
from ..vk_module import *

if TYPE_CHECKING:
	from .. import *


class PipelineLayout(TrackedInstances):

	def __init__(self, shader_attribtues:'ShaderAttributeLayout', shader_layout:dict):
		
		if consts := shader_layout['push constants']:
			push_constant_info, self.push_constant_dtype = shader_attribtues.get_push_constant_range(
				consts
			)
		else:
			push_constant_info = []
			self.push_constant_dtype = None

		bindings = shader_attribtues.get_desc_set_layout_bindings(shader_layout['bindings'])

		# self.ubo_dtype = np.dtype('(3,3)f4')
		# self.ubo_default = np.array([((1,1,0), (1,0,1), (0,1,1))], self.ubo_dtype)
		# TODO any ubo's need a dtype generated

		set_layout_info = VkDescriptorSetLayoutCreateInfo(
			bindingCount = len(bindings), pBindings = bindings
		)

		self.set_layouts = [
			vkCreateDescriptorSetLayout(BVKC.logical_device.device, set_layout_info, None)
		]

		pipeline_layout_info = VkPipelineLayoutCreateInfo(
			setLayoutCount = len(self.set_layouts), pSetLayouts = self.set_layouts,
			pushConstantRangeCount = len(push_constant_info), pPushConstantRanges = push_constant_info,
		)

		self.layout = vkCreatePipelineLayout(BVKC.logical_device.device, pipeline_layout_info, None)

	def on_destroy(self):
		vkDestroyPipelineLayout(BVKC.logical_device.device, self.layout, None)

		for layout in self.set_layouts:
			vkDestroyDescriptorSetLayout(BVKC.logical_device.device, layout, None)


class VulkanPipeline(TrackedInstances, RenderingStep):
	def __init__(self, priority = 0) :
		super().__init__(priority)
		self.pipeline = None

	def bind(self, command_buffer): ...


class ComputePipeline(VulkanPipeline):

	def bind(self, command_buffer):
		vkCmdBindPipeline(command_buffer, VK_PIPELINE_BIND_POINT_COMPUTE, self.pipeline)
	
	# TODO complete implementation

class GraphicsPipeline(VulkanPipeline):

	def __init__(self, 
			render_pass:'RenderPass', 
			shader_attribute:'ShaderAttributeLayout', 
			shader_layout:dict, 
			vertex_shader:Shader, 
			fragment_shader:Shader, 
			binding_model:'Mesh',
			priority = 0,
			**kwargs):
		# TODO find a better method than kwargs

		super().__init__(priority)

		self.render_pass = render_pass
		self.shader_attribute = shader_attribute
		self.shader_layout = {
			'vertex attributes' : [],
			'instance attributes' : [],
			'push constants' : [],
			'bindings' : []
		} | shader_layout
		self.pipeline_layout = PipelineLayout(shader_attribute, self.shader_layout)

		binding_desc, attribute_desc = binding_model.get_descriptions(self.shader_layout['vertex attributes'])

		if attr := self.shader_layout['instance attributes']:
			bd, ad = shader_attribute.get_vertex_descriptions(attr)
			binding_desc.extend(bd)
			attribute_desc.extend(ad)

		vertex_input_info = VkPipelineVertexInputStateCreateInfo(
			vertexBindingDescriptionCount = len(binding_desc), pVertexBindingDescriptions = binding_desc,
			vertexAttributeDescriptionCount = len(attribute_desc), pVertexAttributeDescriptions = attribute_desc
		)

		input_assembly = VkPipelineInputAssemblyStateCreateInfo(
			topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST
		)

		extent = render_pass.render_target.extent

		viewport = VkViewport(
			x = 0, y = 0,
			width = extent.width,
			height = extent.height,
			minDepth = 0.0, maxDepth = 1.0
		)

		scissor = VkRect2D(
			offset = [0,0],
			extent = extent
		)

		viewport_state = VkPipelineViewportStateCreateInfo(
			viewportCount = 1,
			pViewports = viewport,
			scissorCount = 1,
			pScissors = scissor
		)

		rasterizer = VkPipelineRasterizationStateCreateInfo(
			depthClampEnable = VK_FALSE,
			rasterizerDiscardEnable = VK_FALSE,
			polygonMode = VK_POLYGON_MODE_FILL,
			lineWidth = 1.0,
			cullMode = VK_CULL_MODE_BACK_BIT,
			frontFace = VK_FRONT_FACE_CLOCKWISE,
			depthBiasEnable = VK_FALSE
		)

		multisampling = VkPipelineMultisampleStateCreateInfo(
			sampleShadingEnable = VK_FALSE,
			rasterizationSamples = VK_SAMPLE_COUNT_1_BIT
		)

		shader_stages = [vertex_shader.stage_create_info(), fragment_shader.stage_create_info()]
		
		if 'blend' in kwargs:
			match kwargs['blend']:
				case 'transparent':
					color_blend_attachment = self._gen_blend_transparent()
				case _:
					color_blend_attachment = self._gen_blend_opaque()
		else:
			color_blend_attachment = self._gen_blend_opaque()

		color_blending = VkPipelineColorBlendStateCreateInfo(
			logicOpEnable = VK_FALSE,
			attachmentCount = 1,
			pAttachments = color_blend_attachment,
			blendConstants = [0.0, 0.0, 0.0, 0.0]
		)

		if 'depth' not in kwargs or kwargs['depth']:
			depth_stencil = VkPipelineDepthStencilStateCreateInfo(
				depthTestEnable = True,
				depthWriteEnable = True,
				depthCompareOp = VK_COMPARE_OP_LESS,
				depthBoundsTestEnable = False,
				minDepthBounds = 0.0,
				maxDepthBounds = 1.0,
			)

		else:
			depth_stencil = VkPipelineDepthStencilStateCreateInfo(
				depthTestEnable = False,
				depthWriteEnable = False,
			)

		dynamic_state = VkPipelineDynamicStateCreateInfo(
			dynamicStateCount = 2,
			pDynamicStates = [
				VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR
			]
		)
		self.viewport_needs_update = True		
		
		pipeline_info = VkGraphicsPipelineCreateInfo(
			stageCount = len(shader_stages),
			pStages = shader_stages,
			pVertexInputState = vertex_input_info, 
			pInputAssemblyState = input_assembly,
			pViewportState = viewport_state,
			pRasterizationState = rasterizer,
			pMultisampleState = multisampling,
			pDepthStencilState = depth_stencil,
			pColorBlendState = color_blending, 
			pDynamicState = dynamic_state,
			layout = self.pipeline_layout.layout,
			renderPass = render_pass.vk_addr,
			subpass = 0
		)

		self.pipeline = vkCreateGraphicsPipelines(BVKC.logical_device.device, VK_NULL_HANDLE, 1, pipeline_info, None)[0]

		render_pass.attach(self)

	@staticmethod
	def _gen_blend_opaque():
		return VkPipelineColorBlendAttachmentState(
			blendEnable = VK_FALSE,
			colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT | VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT
		)

	@staticmethod
	def _gen_blend_transparent():
		return VkPipelineColorBlendAttachmentState(
			blendEnable = VK_TRUE,
			srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA,
			dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA,
			colorBlendOp = VK_BLEND_OP_ADD,
			srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE,
			dstAlphaBlendFactor = VK_BLEND_FACTOR_ZERO,
			alphaBlendOp = VK_BLEND_OP_ADD,
			colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT | VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT
		)

	def begin(self, command_buffer):
		if self.viewport_needs_update:
			self.update_viewport(command_buffer)

		vkCmdBindPipeline(command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.pipeline)

	def update_viewport(self, command_buffer):
		# self.viewport_needs_update = False
		extent = self.render_pass.render_target.extent
		
		viewport = VkViewport(
			x = 0, y = 0,
			width = extent.width,
			height = extent.height,
			minDepth = 0.0, maxDepth = 1.0
		)
		vkCmdSetViewport(command_buffer, 0, 1, [viewport])

		scissor = VkRect2D(
			offset = [0,0],
			extent = extent
		)
		vkCmdSetScissor(command_buffer, 0, 1, [scissor])

	def on_destroy(self):
		vkDestroyPipeline(BVKC.logical_device.device, self.pipeline, None)


