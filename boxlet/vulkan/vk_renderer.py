from .vk_module import *
from . import *


class Renderer(TrackedInstances):

	def prepare(self, command_buffer):
		...


class RendererBindings:
	
	# can also be considered a vulkan descriptor set

	def __init__(self, pipeline:GraphicsPipeline, defaults:dict[int]) -> None:
		bindings = pipeline.shader_layout['bindings']
		self.descriptor_pool = pipeline.shader_attribute.create_descriptor_pool(bindings)

		alloc_info = VkDescriptorSetAllocateInfo(
			descriptorPool = self.descriptor_pool,
			descriptorSetCount = BVKC.swapchain.max_frames,
			pSetLayouts = pipeline.pipeline_layout.set_layouts * BVKC.swapchain.max_frames
		)

		self.descriptor_sets = vkAllocateDescriptorSets(BVKC.logical_device.device, alloc_info)
		self.pipeline_layout = pipeline.pipeline_layout
		self.ubo_set:list[vk_memory.Buffer] = []

		for desc_set in self.descriptor_sets:
			
			write = []
			for name, binding, _ in bindings:
				desc_type = pipeline.shader_attribute.descriptor_types[name]
				buffer_info = None
				image_info = None

				if desc_type == VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER:
					new_buffer = vk_memory.Buffer(VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT, defaults[binding])
					# TODO parameter to keep memory map?
					self.ubo_set.append(new_buffer)

					buffer_info = VkDescriptorBufferInfo(
						buffer = new_buffer.buffer,
						offset = 0,
						range = new_buffer.size
					)

				elif desc_type == VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER:
					texture = defaults[binding]

					if not isinstance(texture, Texture):
						raise Exception('Expected Texture object.')

					image_info = VkDescriptorImageInfo(
						sampler = texture.sampler,
						imageView = texture.image_view.vk_addr,
						imageLayout = texture.image_layout
					)

				write.append(
					VkWriteDescriptorSet(
						dstSet = desc_set,
						dstBinding = binding,
						dstArrayElement = 0,
						descriptorCount = 1,
						descriptorType = desc_type,
						pBufferInfo = buffer_info,
						pImageInfo = image_info
					)
				)
				# TODO add more functionality for other possible types
				# does dstArrayElement or descriptorCount need be different

			vkUpdateDescriptorSets(BVKC.logical_device.device, len(write), write, 0, None)

		# TODO get some way to update the data
		# maybe just update the buffer and it will handle it's range when it's about to be used
		# don't know what to do for images

	def bind(self, command_buffer):
		vkCmdBindDescriptorSets(
			command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, 
			self.pipeline_layout.layout,
			0, 1, [self.descriptor_sets[BVKC.swapchain.current_frame]],
			0, None
		)

	def destroy(self):
		vkFreeDescriptorSets(
			BVKC.logical_device.device, 
			self.descriptor_pool, 
			BVKC.swapchain.max_frames,
			self.descriptor_sets
		)
		# Might be unnecessary.

		vkDestroyDescriptorPool(BVKC.logical_device.device, self.descriptor_pool, None)
			
		for b in self.ubo_set:
			b.destroy()


class PushConstantManager:

	global_values:dict[str,np.ndarray] = {}

	def __init__(self, pipeline_layout:PipelineLayout) -> None:
		self.pipeline_layout = pipeline_layout
		self.data = np.array([0], pipeline_layout.push_constant_dtype)
		self.itemsize = pipeline_layout.push_constant_dtype.itemsize
		self.globals_to_update = [
			n for n in pipeline_layout.push_constant_dtype.names
			if n.lower().startswith('box_') 
		]

	def __setitem__(self, key, value):
		self.data[0][key] = value

	def __getitem__(self, key):
		return self.data[0][key]

	def push(self, command_buffer):
		for key in self.globals_to_update:
			self.data[key] = PushConstantManager.global_values[key]

		obj_data = ffi.cast('float *', ffi.from_buffer(self.data))
		# don't really like this, but there doesn't seem to be any other solution

		vkCmdPushConstants(
			command_buffer, self.pipeline_layout.layout, 
			VK_SHADER_STAGE_ALL_GRAPHICS,
			0, self.itemsize,
			obj_data
		)
		# TODO restrict stage flag to only used stages

	@staticmethod
	def set_global(key:str, value:np.ndarray):
		'''
		Sets the global value that is shared between all PushConstantManagers.
		
		The key should always start with 'box_'.
		'''
		assert key.lower().startswith('box_')

		PushConstantManager.global_values[key] = value

	@staticmethod
	def get_global(key:str):
		return PushConstantManager.global_values[key]


class IndirectRenderer(Renderer):
	def __init__(self, pipeline:GraphicsPipeline, meshes:vk_mesh.MultiMesh, defaults:dict[int]):

		self.meshes = meshes

		self.buffer_set = vk_memory.InstanceBufferSet(
			meshes,
			pipeline.shader_attribute.data_type
		)
		
		pipeline.attach(self.prepare)
		self.pipeline = pipeline
		self.attributes = RendererBindings(pipeline, defaults)
		self.push_constants = PushConstantManager(pipeline.pipeline_layout)

	def create_instance(self, model_id):
		return self.buffer_set.create_instance(model_id)

	def prepare(self, command_buffer):
		if self.buffer_set.indirect_count == 0:
			return

		self.meshes.bind(command_buffer)

		self.push_constants.push(command_buffer)
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
		self.attributes.destroy()

