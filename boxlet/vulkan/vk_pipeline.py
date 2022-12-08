from typing import Callable
from .vk_module import *
from . import *


class RenderPass(TrackedInstances):

	def __init__(self, image_format):

		self.image_format = image_format

		color_attachment = VkAttachmentDescription(
			format = image_format.format,
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
			pColorAttachments = color_attachment_ref
		)

		render_pass_info = VkRenderPassCreateInfo(
			attachmentCount = 1,
			pAttachments = color_attachment,
			subpassCount = 1,
			pSubpasses = subpass
		)

		self.vk_addr = vkCreateRenderPass(BVKC.logical_device.device, render_pass_info, None)

		self.attached_piplelines:'list[VulkanPipeline]' = []

	def begin(self, command_buffer, frame_buffer:FrameBuffer, area):
		render_pass_info = VkRenderPassBeginInfo(
			renderPass = self.vk_addr,
			framebuffer = frame_buffer.vk_addr,
			renderArea = area,
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
			stageFlags = VK_SHADER_STAGE_VERTEX_BIT, offset = 0,
			size = 4 * 4 * 4
		)

		pipeline_layout_info = VkPipelineLayoutCreateInfo(
			pushConstantRangeCount = 1, pPushConstantRanges = [push_constant_info],
			setLayoutCount = 0
		)

		self.layout = vkCreatePipelineLayout(BVKC.logical_device.device, pipeline_layout_info, None)

	def on_destroy(self):
		vkDestroyPipelineLayout(BVKC.logical_device.device, self.layout, None)


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

class GraphicsPipeline(VulkanPipeline):
	
	# NOTE a compute pipeline would need it's own object
	# at that point, create a PipelineBase class that have functions meant to be overridden

	def __init__(self, render_pass:RenderPass, pipeline_layout:PipelineLayout, extent, vertex_filepath, fragment_filepath):

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

		self.attached_render_calls:list[Callable] = []
		render_pass.attach(self)

	def bind(self, command_buffer):
		vkCmdBindPipeline(command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, self.pipeline)

	def on_destroy(self):
		vkDestroyPipeline(BVKC.logical_device.device, self.pipeline, None)

