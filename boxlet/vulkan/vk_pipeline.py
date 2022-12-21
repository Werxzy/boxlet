from typing import Callable
from .vk_module import *
from . import *


class RenderPass(TrackedInstances):

	def __init__(self, render_target:RenderTarget = None):
		'Render Target as none assumes it will render to the primary render target.'

		self.render_target = render_target if render_target else BVKC.swapchain

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

		subpass = VkSubpassDescription(
			pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS,
			colorAttachmentCount = 1,
			pColorAttachments = [color_attachment_ref]
		)

		render_pass_info = VkRenderPassCreateInfo(
			attachmentCount = 1,
			pAttachments = color_attachment,
			subpassCount = 1,
			pSubpasses = subpass
		)

		self.vk_addr = vkCreateRenderPass(BVKC.logical_device.device, render_pass_info, None)

		self.attached_piplelines:'list[VulkanPipeline]' = []

	def begin(self, command_buffer):
		render_pass_info = VkRenderPassBeginInfo(
			renderPass = self.vk_addr,
			framebuffer = self.render_target.get_frame_buffer().vk_addr,
			renderArea = [[0,0], self.render_target.extent],
			clearValueCount = 1,
			pClearValues = [VkClearValue([[1.0, 0.5, 0.25, 1.0]])]
		)

		vkCmdBeginRenderPass(command_buffer, render_pass_info, VK_SUBPASS_CONTENTS_INLINE)

	def end(self, command_buffer):
		vkCmdEndRenderPass(command_buffer)

	def attach(self, pipeline):
		# TODO assert that pipeline is the correct type (graphics vs compute vs ...)
		self.attached_piplelines.append(pipeline)

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


class VulkanPipeline(TrackedInstances):
	def __init__(self) :
		self.pipeline = None
		self.attached_render_calls:list[Callable] = []

	def bind(self, command_buffer): ...

	def attach(self, render_call:Callable):
		self.attached_render_calls.append(render_call)

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
			binding_model:Mesh):

		super().__init__()

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
		
		pipeline_info = VkGraphicsPipelineCreateInfo(
			stageCount = len(shader_stages),
			pStages = shader_stages,
			pVertexInputState = vertex_input_info, 
			pInputAssemblyState = input_assembly,
			pViewportState = viewport_state,
			pRasterizationState = rasterizer,
			pMultisampleState = multisampling,
			pColorBlendState = color_blending, 
			layout = self.pipeline_layout.layout,
			renderPass = render_pass.vk_addr,
			subpass = 0
		)

		self.pipeline = vkCreateGraphicsPipelines(BVKC.logical_device.device, VK_NULL_HANDLE, 1, pipeline_info, None)[0]

		vertex_shader.destroy()
		fragment_shader.destroy()

		render_pass.attach(self)

	def bind(self, command_buffer):
		vkCmdBindPipeline(command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.pipeline)

	def on_destroy(self):
		vkDestroyPipeline(BVKC.logical_device.device, self.pipeline, None)


