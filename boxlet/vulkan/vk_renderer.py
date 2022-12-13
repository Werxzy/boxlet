from .vk_module import *
from . import *


class Renderer(TrackedInstances):

	def prepare(self, command_buffer):
		...


class RendererAttributes:
	
	# can also be considered a vulkan descriptor set

	def __init__(self, pipeline:GraphicsPipeline, texture:Texture) -> None:

		alloc_info = VkDescriptorSetAllocateInfo(
			descriptorPool = pipeline.descriptor_pool,
			descriptorSetCount = BVKC.swapchain.max_frames,
			pSetLayouts = pipeline.pipeline_layout.set_layouts * BVKC.swapchain.max_frames
		)

		self.descriptor_sets = vkAllocateDescriptorSets(BVKC.logical_device.device, alloc_info)
		self.pipeline_layout = pipeline.pipeline_layout

		for desc_set in self.descriptor_sets:

			image_info = VkDescriptorImageInfo(
				sampler = texture.sampler,
				imageView = texture.image_view.vk_addr,
				imageLayout = texture.image_layout
			)

			write = VkWriteDescriptorSet(
				dstSet = desc_set,
				dstBinding = 0,
				dstArrayElement = 0,
				descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
				descriptorCount = 1,
				pImageInfo = image_info
			)

			vkUpdateDescriptorSets(BVKC.logical_device.device, 1, write, 0, None)

	def bind(self, command_buffer):
		vkCmdBindDescriptorSets(
			command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, 
			self.pipeline_layout.layout,
			0, 1, [self.descriptor_sets[BVKC.swapchain.current_frame]],
			0, None
		)


class IndirectRenderer(Renderer):
	def __init__(self, pipeline:GraphicsPipeline, meshes:vk_mesh.MultiMesh, data_type, texture):

		self.meshes = meshes

		self.buffer_set = vk_memory.InstanceBufferSet(
			meshes,
			data_type
		)
		
		pipeline.attach(self.prepare)
		self.pipeline = pipeline
		self.attributes = RendererAttributes(pipeline, texture)

	def create_instance(self, model_id):
		return self.buffer_set.create_instance(model_id)

	def prepare(self, command_buffer):
		if self.buffer_set.indirect_count == 0:
			return

		self.meshes.bind(command_buffer)

		push_constant_test = np.identity(4, np.float32)
		push_constant_test[0][0] = 9/16
		obj_data = ffi.cast('float *', ffi.from_buffer(push_constant_test))
		# don't really like this, but there doesn't seem to be any other solution

		vkCmdPushConstants(
			command_buffer, self.pipeline.pipeline_layout.layout,
			VK_SHADER_STAGE_VERTEX_BIT, 
			0, 4 * 4 * 4,
			obj_data
		)

		self.buffer_set.update_memory()
		self.buffer_set.bind_to_vertex(command_buffer)
		self.attributes.bind(command_buffer)

		vkCmdDrawIndexedIndirect(
			commandBuffer = command_buffer, 
			buffer = self.buffer_set.indirect_buffer.buffer,
			offset = 0,
			drawCount = self.buffer_set.indirect_count,
			stride = 20
		)

	def on_destroy(self):
		self.buffer_set.destroy()

