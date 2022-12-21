from typing import Any
from .vk_module import *
from . import *


class Renderer(TrackedInstances):

	def prepare(self, command_buffer):
		...


class DescriptorSet:
	def __init__(self, binder:'RendererBindings', binding:int) -> None:
		self.binder = binder
		self.binding = binding
		self.needs_update = [False] * len(binder.descriptor_sets)
		self.set_range = range(len(self.needs_update))

	def get_update(self, set_number) -> list[Any]:
		if self.needs_update[set_number]:
			self.needs_update[set_number] = False
			return [self.get_write(set_number)]
		return []

	def force_update_all(self):
		for i in self.set_range:
			self.needs_update[i] = False
		
		return [self.get_write(i) for i in self.set_range]

	def set_descriptor(self, data) -> None: 
		'''
		Sets the vulkan object that the descriptor is linked to.

		It is recommended to use this as little as possible and instead update the buffer/image themselves.
		'''

	def get_write(self, set_number) -> Any: ...

	def destroy(self): ...


class UniformBufferDescriptorSet(DescriptorSet):
	def __init__(self, binder:'RendererBindings', binding:int) -> None:
		super().__init__(binder, binding)
		self.buffer_group:vk_memory.UniformBufferGroup = None

	def set_descriptor(self, data:np.ndarray) -> None:
		self.destroy()

		for i in self.set_range:
			self.needs_update[i] = True

		self.buffer_group = vk_memory.UniformBufferGroup(data, len(self.needs_update))
		# TODO parameter to keep memory map?

	def get_update(self, set_number) -> list[Any]:
		self.buffer_group.update_memory(set_number)
		return super().get_update(set_number)

	def get_write(self, set_number):
		b = self.buffer_group.buffers[set_number]
		buffer_info = VkDescriptorBufferInfo(
			buffer = b.buffer,
			offset = 0,
			range = b.size
		)

		return VkWriteDescriptorSet(
			dstSet = self.binder.descriptor_sets[set_number],
			dstBinding = self.binding,
			dstArrayElement = 0,
			descriptorCount = 1,
			descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,
			pBufferInfo = buffer_info,
		)

	def destroy(self):
		if self.buffer_group:
			self.buffer_group.destroy()


class ImageDescriptorSet(DescriptorSet):
	def set_descriptor(self, data:Texture) -> None:
		for i in self.set_range:
			self.needs_update[i] = True

		self.texture = data

	def get_write(self, set_number):
		image_info = VkDescriptorImageInfo(
			sampler = self.texture.sampler,
			imageView = self.texture.image_view.vk_addr,
			imageLayout = self.texture.image_layout
		)

		return VkWriteDescriptorSet(
			dstSet = self.binder.descriptor_sets[set_number],
			dstBinding = self.binding,
			dstArrayElement = 0,
			descriptorCount = 1,
			descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
			pImageInfo = image_info,
		)


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

		self.descriptors:dict[str, DescriptorSet] = {}
		write = []
		for name, binding, _ in bindings:
			desc_type = pipeline.shader_attribute.descriptor_types[name]

			if desc_type == VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER:
				desc = UniformBufferDescriptorSet(self, binding)
			elif desc_type == VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER:
				desc = ImageDescriptorSet(self, binding)
			else:
				raise Exception('Unsupported descriptor type.')

			# TODO add more functionality for other possible types

			desc.set_descriptor(defaults[binding])
			self.descriptors[name] = desc

			write.extend(desc.force_update_all())

		vkUpdateDescriptorSets(BVKC.logical_device.device, len(write), write, 0, None)

	def _update_descriptors(self, set_number):
		write = []
		for desc in self.descriptors.values():
			write.extend(desc.get_update(set_number))
		if write:
			vkUpdateDescriptorSets(BVKC.logical_device.device, len(write), write, 0, None)

	def bind(self, command_buffer):
		self._update_descriptors(BVKC.swapchain.current_frame)

		vkCmdBindDescriptorSets(
			command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, 
			self.pipeline_layout.layout,
			0, 1, [self.descriptor_sets[BVKC.swapchain.current_frame]],
			0, None
		)

	def destroy(self):
		for desc in self.descriptors.values():
			desc.destroy()

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

