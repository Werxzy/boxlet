from . import *
from .vk_library import *


class Shader:
	TYPES = {
		'vertex': VK_SHADER_STAGE_VERTEX_BIT,
		'fragment': VK_SHADER_STAGE_FRAGMENT_BIT
	}

	def __init__(self, shader_type:str, logical_device:vk_device.LogicalDevice, filename) -> None:
		if DEBUG_MODE:
			print(f'Load shader module:{filename}')

		if shader_type not in Shader.TYPES:
			raise Exception(f'Invalid Shader type {shader_type}')

		self.shader_type = shader_type
		self.logical_device = logical_device

		with open(get_path(filename), 'rb') as file:
			code = file.read()

		create_info = VkShaderModuleCreateInfo(
			codeSize = len(code),
			pCode = code
		)

		self.module = vkCreateShaderModule(
			device = logical_device.device, pCreateInfo = create_info, pAllocator = None
		)

	def stage_create_info(self):
		return VkPipelineShaderStageCreateInfo(
			stage =  Shader.TYPES[self.shader_type],
			module = self.module,
			pName = 'main'
		)

	def destroy(self):
		vkDestroyShaderModule(self.logical_device.device, self.module, None)

