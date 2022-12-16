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

	def __init__(self):
		push_constant_info = VkPushConstantRange(
			stageFlags = VK_SHADER_STAGE_ALL_GRAPHICS, offset = 0,
			size = 4 * 4 * 4
		)

		ubo_layout_binding = VkDescriptorSetLayoutBinding(
			binding = 0, descriptorCount = 1,
			descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,
			stageFlags = VK_SHADER_STAGE_VERTEX_BIT,
			pImmutableSamplers = VK_NULL_HANDLE 
		)

		self.ubo_dtype = np.dtype('(3,3)f4')
		self.ubo_default = np.array([((1,1,0), (1,0,1), (0,1,1))], self.ubo_dtype)

		sampler_layout_binding = VkDescriptorSetLayoutBinding(
			binding = 1, descriptorCount = 1,
			descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
			stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT,
			pImmutableSamplers = VK_NULL_HANDLE 
		)

		bindings = [ubo_layout_binding, sampler_layout_binding]

		set_layout_info = VkDescriptorSetLayoutCreateInfo(
			bindingCount = len(bindings), pBindings = bindings
		)

		self.set_layouts = [
			vkCreateDescriptorSetLayout(BVKC.logical_device.device, set_layout_info, None)
		]

		pipeline_layout_info = VkPipelineLayoutCreateInfo(
			setLayoutCount = len(self.set_layouts), pSetLayouts = self.set_layouts,
			pushConstantRangeCount = 1, pPushConstantRanges = [push_constant_info],
		)

		self.layout = vkCreatePipelineLayout(BVKC.logical_device.device, pipeline_layout_info, None)

	def create_descriptor_pool(self):
		# TODO more dynamic creation

		pool_sizes = [
			VkDescriptorPoolSize(
				VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,
				BVKC.swapchain.max_frames
			),
			VkDescriptorPoolSize(
				VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
				BVKC.swapchain.max_frames
			)
		]

		descriptor_pool_info = VkDescriptorPoolCreateInfo(
			maxSets = BVKC.swapchain.max_frames,
			flags = VK_DESCRIPTOR_POOL_CREATE_FREE_DESCRIPTOR_SET_BIT,
			poolSizeCount = len(pool_sizes), pPoolSizes = pool_sizes
		)
		# the above flag is a vulkan 1.2 feature and may not be necessary
		# unsure if descriptor sets will ever need to be removed

		return vkCreateDescriptorPool(BVKC.logical_device.device, descriptor_pool_info, None)

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

	def __init__(self, render_pass:RenderPass, pipeline_layout:PipelineLayout, vertex_filepath, fragment_filepath):
		super().__init__()

		self.render_pass = render_pass
		self.pipeline_layout = pipeline_layout

		binding_desc = [vk_mesh.get_pos_color_binding_description()]
		attribute_desc = vk_mesh.get_pos_color_attribute_descriptions()
		# TODO move this differently


		# TEMP INSTANCE DATA DESCRIPTIONS
		binding_desc.append(
				VkVertexInputBindingDescription(
					binding = 1, stride = 64, inputRate = VK_VERTEX_INPUT_RATE_INSTANCE
				)	
			)

		attribute_desc.extend([
			VkVertexInputAttributeDescription(
				binding = 1, location = 2,
				format = VK_FORMAT_R32G32B32A32_SFLOAT,
				offset = 0
			),
			VkVertexInputAttributeDescription(
				binding = 1, location = 3,
				format = VK_FORMAT_R32G32B32A32_SFLOAT,
				offset = 16
			),
			VkVertexInputAttributeDescription(
				binding = 1, location = 4,
				format = VK_FORMAT_R32G32B32A32_SFLOAT,
				offset = 32
			),
			VkVertexInputAttributeDescription(
				binding = 1, location = 5,
				format = VK_FORMAT_R32G32B32A32_SFLOAT,
				offset = 48
			),
		])

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
			layout = pipeline_layout.layout,
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


