from .vk_module import *
from . import *


class RenderingStep:
	'''
	Manages a tree of render steps, such as 
	beginning and ending render passes,
	binding piplines, or making render calls.

	After a RenderingStep begins, 
	it will loop through all its attachments to begin,
	afterwhich the original RenderingStep will call its end function.
	'''
	base_attachments:list['RenderingStep'] = []

	keyed_attachments:dict[str, list['RenderingStep']] = {}

	def __init__(self, priority = 0, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.attached_steps:list['RenderingStep'] = []
		self.priority = priority

	def attach(self, step:'RenderingStep'):
		RenderingStep._attach_to_list(self.attached_steps, step)

	def attach_to_key(self, key:str):
		att = RenderingStep.keyed_attachments.setdefault(key, list())
		RenderingStep._attach_to_list(att, self)

	def attach_to_base(self):
		RenderingStep._attach_to_list(RenderingStep.base_attachments, self)

	def full_begin(self, command_buffer):
		'''
		Calls the begin and end functions while looping through any attached render steps.
		'''
		self.begin(command_buffer)

		for att in self.attached_steps:
			att.full_begin(command_buffer)
			
		self.end(command_buffer)

	def begin(self, command_buffer): ...

	def end(self, command_buffer): ...

	@staticmethod
	def _attach_to_list(attach_list:list['RenderingStep'], step):
		attach_list.append(step)
		attach_list.sort(key = lambda r : r.priority)

	@staticmethod
	def begin_from_base(command_buffer):
		'Loops through all rendering steps attached to the base class'
		for att in RenderingStep.base_attachments:
			att.full_begin(command_buffer)


class KeyedStep(RenderingStep):
	'''
	Loops through a list of rendering steps that are attached to a key instead of ones that are attached to this object.
	'''
	def __init__(self, key, priority):
		self.key = key
		self.priority = priority

	def full_begin(self, command_buffer):
		for att in RenderingStep.keyed_attachments[self.key]:
			att.full_begin(command_buffer)


class RenderPass(TrackedInstances, RenderingStep):

	def __init__(self, render_target:RenderTarget = None, priority = 0):
		'Render Target as none assumes it will render to the primary render target.'

		super().__init__(priority)
		self.attach_to_base()

		self.render_target = render_target if render_target else BVKC.swapchain
		self.render_target.set_recent_render_pass(self)

		color_attachment = VkAttachmentDescription(
			format = self.render_target.format,
			samples = VK_SAMPLE_COUNT_1_BIT,

			loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
			storeOp = VK_ATTACHMENT_STORE_OP_STORE,
			
			stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
			stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,

			initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
			finalLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR
		)

		color_attachment_ref = VkAttachmentReference(
			attachment = 0,
			layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL
		)

		depth_attachment = VkAttachmentDescription(
			format = vk_device.find_depth_format(BVKC.physical_device),
			samples = VK_SAMPLE_COUNT_1_BIT,

			loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR,
			storeOp = VK_ATTACHMENT_STORE_OP_STORE,
			
			stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
			stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,

			initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
			finalLayout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
		)

		depth_attachment_ref = VkAttachmentReference(
			attachment = 1,
			layout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
		)

		attachments = [color_attachment, depth_attachment]

		subpass = VkSubpassDescription(
			pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS,
			colorAttachmentCount = 1,
			pColorAttachments = [color_attachment_ref],
			pDepthStencilAttachment = [depth_attachment_ref]
		)

		render_pass_info = VkRenderPassCreateInfo(
			attachmentCount = len(attachments),
			pAttachments = attachments,
			subpassCount = 1,
			pSubpasses = subpass
		)

		self.vk_addr = vkCreateRenderPass(BVKC.logical_device.device, render_pass_info, None)

	def begin(self, command_buffer):
		render_pass_info = VkRenderPassBeginInfo(
			renderPass = self.vk_addr,
			framebuffer = self.render_target.get_frame_buffer().vk_addr,
			renderArea = [[0,0], self.render_target.extent],
			clearValueCount = 2,
			pClearValues = [VkClearValue([[1.0, 0.5, 0.25, 1.0]]), VkClearValue([[1.0, 0.0]])]
		)

		vkCmdBeginRenderPass(command_buffer, render_pass_info, VK_SUBPASS_CONTENTS_INLINE)

	def end(self, command_buffer):
		vkCmdEndRenderPass(command_buffer)

	def on_destroy(self):
		vkDestroyRenderPass(BVKC.logical_device.device, self.vk_addr, None)


class PipelineLayout(TrackedInstances):

	def __init__(self, shader_attribtues:ShaderAttributeLayout, shader_layout:dict):
		
		push_constant_info, self.push_constant_dtype = shader_attribtues.get_push_constant_range(
			shader_layout['push constants']
		)

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
			render_pass:RenderPass, 
			shader_attribute:ShaderAttributeLayout, 
			shader_layout:dict, vertex_filepath, 
			fragment_filepath, 
			binding_model:Mesh,
			priority = 0):

		super().__init__(priority)

		self.render_pass = render_pass
		self.shader_attribute = shader_attribute
		self.shader_layout = shader_layout
		self.pipeline_layout = PipelineLayout(shader_attribute, shader_layout)

		binding_desc, attribute_desc = binding_model.get_descriptions(shader_layout['vertex attributes'])

		bd, ad = shader_attribute.get_vertex_descriptions(shader_layout['instance attributes'])
		binding_desc.extend(bd)
		attribute_desc.extend(ad)

		vertex_input_info = VkPipelineVertexInputStateCreateInfo(
			vertexBindingDescriptionCount = len(binding_desc), pVertexBindingDescriptions = binding_desc,
			vertexAttributeDescriptionCount = len(attribute_desc), pVertexAttributeDescriptions = attribute_desc
		)

		vertex_shader = vk_shaders.Shader('vertex', vertex_filepath)

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

		fragment_shader = vk_shaders.Shader('fragment', fragment_filepath)

		shader_stages = [vertex_shader.stage_create_info(), fragment_shader.stage_create_info()]

		color_blend_attachment = VkPipelineColorBlendAttachmentState(
			colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT | VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT,
			blendEnable = VK_FALSE
		)

		color_blending = VkPipelineColorBlendStateCreateInfo(
			logicOpEnable = VK_FALSE,
			attachmentCount = 1,
			pAttachments = color_blend_attachment,
			blendConstants = [0.0, 0.0, 0.0, 0.0]
		)

		depth_stencil = VkPipelineDepthStencilStateCreateInfo(
			depthTestEnable = True,
			depthWriteEnable = True,
			depthCompareOp = VK_COMPARE_OP_LESS,
			depthBoundsTestEnable = False,
			minDepthBounds = 0.0,
			maxDepthBounds = 1.0,
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

		vertex_shader.destroy()
		fragment_shader.destroy()

		render_pass.attach(self)

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


