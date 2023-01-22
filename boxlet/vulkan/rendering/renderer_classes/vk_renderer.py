from typing import Any, Self

from ... import RenderingStep, UniformBufferGroup, np
from ...vk_module import *

if TYPE_CHECKING:
	from ... import *


class Renderer(TrackedInstances, RenderingStep):
	def __init__(self, pipeline:'GraphicsPipeline|list[GraphicsPipeline]', mesh:'Mesh|MultiMesh', defaults:dict[int] = {}, priority = 0) -> None:
		super().__init__(priority)

		self.mesh:'Mesh|MultiMesh' = mesh
		if mesh:
			mesh.init_buffers()

		if isinstance(pipeline, list):
			self.pipeline = pipeline[0]
			self.child_renderers = [
				ChildRenderer(self, pipe, priority)
				for pipe in pipeline[1:]
			]
		else:
			self.pipeline = pipeline
			self.child_renderers = []

		self.pipeline.attach(self)
		self.attributes = RendererBindings(self.pipeline, defaults)
		self._push_constants = PushConstantManager(self.pipeline.pipeline_layout)
		self.buffer_set:'IndirectBufferSet|InstancedBufferSet' = None

	def set_constant(self, key, value):
		self._push_constants[key] = value
		for renderer in self.child_renderers:
			renderer._push_constants[key] = value
		
	def get_constant(self, key):
		if (value := self._push_constants[key]) is not None:
			return value
		
		for renderer in self.child_renderers:
			if (value := renderer._push_constants[key]) is not None:
				return value

		raise Exception(f'Constant {key} does not exist on this renderer')
	
	def begin(self, command_buffer):
		if not self.is_enabled():
			return

		if self.mesh:
			self.mesh.bind(command_buffer)

		if self._push_constants:
			self._push_constants.push(command_buffer)
		
		if self.buffer_set:
			self.buffer_set.update_memory()
			self.buffer_set.bind_to_vertex(command_buffer)
		
		if self.attributes:
			self.attributes.bind(command_buffer)

		self.draw_command(command_buffer)

	def is_enabled(self):
		return True

	def draw_command(self, command_buffer):
		...

	def on_destroy(self):
		if self.buffer_set:
			self.buffer_set.destroy()

		if self.attributes:
			self.attributes.destroy()


class ChildRenderer(RenderingStep):
	def __init__(self, parent_renderer:'Renderer', pipeline:'GraphicsPipeline', priority = 0) -> None:
		super().__init__(priority)

		self.parent_renderer = parent_renderer
		pipeline.attach(self)
		self.pipeline = pipeline
		self._push_constants = PushConstantManager(pipeline.pipeline_layout)

	def begin(self, command_buffer):
		parent = self.parent_renderer

		if not parent.is_enabled():
			return

		if parent.mesh:
			parent.mesh.bind(command_buffer)
			
		if self._push_constants: # push constants can be different between renderers
			self._push_constants.push(command_buffer)

		if parent.buffer_set:
			parent.buffer_set.update_memory()
			parent.buffer_set.bind_to_vertex(command_buffer)

		if parent.attributes:
			parent.attributes.bind(command_buffer)

		parent.draw_command(command_buffer)


class Descriptor:
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


class UniformBufferDescriptor(Descriptor):
	def set_descriptor(self, data:np.ndarray) -> None:
		self.destroy()

		for i in self.set_range:
			self.needs_update[i] = True

		self.buffer_group = UniformBufferGroup(data, len(self.needs_update))
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
		if hasattr(self, 'buffer_group'):
			self.buffer_group.destroy()


class ImageDescriptor(Descriptor):
	def set_descriptor(self, data:'Texture') -> None:
		for i in self.set_range:
			self.needs_update[i] = True

		self.texture = data
		self.orig_image_view = self.texture.image_view

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

	def get_update(self, set_number) -> list[Any]:
		if self.orig_image_view != self.texture.image_view:
			self.orig_image_view = self.texture.image_view
			for i in self.set_range:
				self.needs_update[i] = True
			
		return super().get_update(set_number)


class RendererBindings:
	
	# can also be considered a vulkan descriptor set

	def __new__(cls: type[Self], pipeline:'GraphicsPipeline', defaults) -> Self|None:
		# Checks if the arguments are valid.
		if len(pipeline.shader_layout['bindings']):
			return super().__new__(cls)
		return None

	def __init__(self, pipeline:'GraphicsPipeline', defaults:dict[int]) -> None:
		bindings = pipeline.shader_layout['bindings']
		self.descriptor_pool = pipeline.shader_attribute.create_descriptor_pool(bindings)

		alloc_info = VkDescriptorSetAllocateInfo(
			descriptorPool = self.descriptor_pool,
			descriptorSetCount = BVKC.swapchain.max_frames,
			pSetLayouts = pipeline.pipeline_layout.set_layouts * BVKC.swapchain.max_frames
		)

		self.descriptor_sets = vkAllocateDescriptorSets(BVKC.logical_device.device, alloc_info)
		self.pipeline_layout = pipeline.pipeline_layout

		self.descriptors:dict[str, Descriptor] = {}
		write = []
		for name, binding, _ in bindings:
			desc_type = pipeline.shader_attribute.descriptor_types[name]

			if desc_type == VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER:
				desc = UniformBufferDescriptor(self, binding)
			elif desc_type == VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER:
				desc = ImageDescriptor(self, binding)
			else:
				raise Exception('Unsupported descriptor type.')

			# TODO add more functionality for other possible types

			# if binding in defaults:
			# TODO get this to be fine
			# probably need to set the values initially to zero with the known data type

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


class PushConstantManager:

	global_values:dict[str,np.ndarray] = {}

	def __new__(cls: type[Self], pipeline_layout:'PipelineLayout') -> Self|None:
		# Checks if the arguments are valid.
		if pipeline_layout.push_constant_dtype is not None:
			return super().__new__(cls)
		return None

	def __init__(self, pipeline_layout:'PipelineLayout') -> None:
		self.pipeline_layout = pipeline_layout
		self.data = np.array([0], pipeline_layout.push_constant_dtype)
		self.itemsize = pipeline_layout.push_constant_dtype.itemsize
		self.names = pipeline_layout.push_constant_dtype.names
		self.globals_to_update = [
			n for n in self.names
			if n.lower().startswith('box_') 
		]

	def __setitem__(self, key, value):
		if key in self.names:
			self.data[0][key] = value

	def __getitem__(self, key):
		if key in self.names:
			return self.data[0][key]
		return None

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
