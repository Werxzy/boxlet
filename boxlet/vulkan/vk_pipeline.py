from . import *
from .vk_module import *


class RenderPass:

	def __init__(self, logical_device:vk_device.LogicalDevice, swapchain_image_format):
		
		self.logical_device = logical_device

		color_attachment = VkAttachmentDescription(
			format = swapchain_image_format,
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

		self.vk_addr = vkCreateRenderPass(logical_device.device, render_pass_info, None)

	def begin(self, command_buffer, frame_buffer, area):
		render_pass_info = VkRenderPassBeginInfo(
			renderPass = self.vk_addr,
			framebuffer = frame_buffer,
			renderArea = area
		)

		clear_color = VkClearValue([[1.0, 0.5, 0.25, 1.0]])
		render_pass_info.clearValueCount = 1
		render_pass_info.pClearValues = ffi.addressof(clear_color)

		vkCmdBeginRenderPass(command_buffer, render_pass_info, VK_SUBPASS_CONTENTS_INLINE)

	def end(self, command_buffer):
		vkCmdEndRenderPass(command_buffer)

	def destroy(self):
		vkDestroyRenderPass(self.logical_device.device, self.vk_addr, None)

def create_pipeline_layout(device):
	
	push_constant_info = VkPushConstantRange(
		stageFlags = VK_SHADER_STAGE_VERTEX_BIT, offset = 0,
		size = 4 * 4 * 4
	)

	pipeline_layout_info = VkPipelineLayoutCreateInfo(
		pushConstantRangeCount = 1, pPushConstantRanges = [push_constant_info],
		setLayoutCount = 0
	)

	return vkCreatePipelineLayout(device, pipeline_layout_info, None)

class GraphicsPipeline:
	
	def __init__(self, logical_device:vk_device.LogicalDevice, image_format, extent, vertex_filepath, fragment_filepath):
		
		self.logical_device = logical_device

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

		vertex_shader = vk_shaders.Shader('vertex', logical_device, vertex_filepath)

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

		fragment_shader = vk_shaders.Shader('fragment', logical_device, fragment_filepath)

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

		self.layout = create_pipeline_layout(logical_device.device)

		self.render_pass = RenderPass(logical_device, image_format)

		pipeline_info = VkGraphicsPipelineCreateInfo(
			stageCount = len(shader_stages),
			pStages = shader_stages,
			pVertexInputState = vertex_input_info, 
			pInputAssemblyState = input_assembly,
			pViewportState = viewport_state,
			pRasterizationState = rasterizer,
			pMultisampleState = multisampling,
			pColorBlendState = color_blending, 
			layout = self.layout,
			renderPass = self.render_pass.vk_addr,
			subpass = 0
		)

		self.pipeline = vkCreateGraphicsPipelines(logical_device.device, VK_NULL_HANDLE, 1, pipeline_info, None)[0]

		vertex_shader.destroy()
		fragment_shader.destroy()

	def destroy(self):
		vkDestroyPipeline(self.logical_device.device, self.pipeline, None)
		vkDestroyPipelineLayout(self.logical_device.device, self.layout, None)
		self.render_pass.destroy()
