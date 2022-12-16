from .vk_module import *
import numpy as np


class ShaderAttributeLayout:
	'Used to determine the layout of data for instance attributes'
	# not actually a vulkan object

	

	def __init__(self, attributes = None, push_constants = None, bindings = None):

		self.attributes = attributes
		# data unique to each instance
		self.push_constants = push_constants
		# data for each group that will likely change each frame
		self.bindings = bindings
		# data mostly for each instance group


		# builds dtype for renderer attributes
		dtype_format = []
		self.attribute_format = {}
		offset = 0
		for t in attributes:
			name = t[0]
			attr_type = t[1]

			if attr_type == 'vec4':
				dtype_format.append((name, '(4,)f4'))
				self.attribute_format[name] = [
					(offset, VK_FORMAT_R32G32B32A32_SFLOAT)
				]
				offset += 16

			elif attr_type == 'mat4':
				dtype_format.append((name, '(4,4)f4'))
				self.attribute_format[name] = [
					(offset + o * 16, VK_FORMAT_R32G32B32A32_SFLOAT)
					for o in range(4)
				]
				offset += 64

			else:
				raise Exception('Unsupported type')

		self.data_type = np.dtype(dtype_format)
		self.data_stride = offset


		self.descriptor_types = {}
		for name in self.bindings:
			b = self.bindings[name]
			if isinstance(b, list):
				desc_type = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER
			elif b[0] == 'sampler2D':
				desc_type = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER
			# TODO fill this out

			self.descriptor_types[name] = desc_type 
			# potentially gather more info together

	def get_vertex_descriptions(self, attributes:list[tuple[str,int]], binding = 1):
		binding_desc = [
			VkVertexInputBindingDescription(
				binding = binding, stride = self.data_stride, inputRate = VK_VERTEX_INPUT_RATE_INSTANCE
			)	
		]

		attribute_desc = []
		for name, loc in attributes:
			for offset, format in self.attribute_format[name]:
				attribute_desc.append(
					VkVertexInputAttributeDescription(
						binding = binding, location = loc,
						format = format, offset = offset
					)
				)

		return binding_desc, attribute_desc

	def get_desc_set_layout_bindings(self, bindings:list[tuple[str, int, str]]):
		all_bindings = []
		
		for name, bind, stages in bindings:
			stage_flags = 0
			s = stages.split(',')
			if 'vertex' in s: 
				stage_flags |= VK_SHADER_STAGE_VERTEX_BIT
			if 'fragment' in s: 
				stage_flags |= VK_SHADER_STAGE_FRAGMENT_BIT
			# duplicate info in vk_shaders

			if stage_flags == 0:
				raise Exception('invalid stage value')

			all_bindings.append(
				VkDescriptorSetLayoutBinding(
					binding = bind, descriptorCount = 1,
					descriptorType = self.descriptor_types[name],
					stageFlags = stage_flags,
					pImmutableSamplers = VK_NULL_HANDLE 
				)
			)
			# TODO does descriptor count need to be updated here?

		# TODO? do I need to manage seperate sets?
		return all_bindings

	def get_push_constant_range(self, push:list[tuple[str,str]]):
		# constants = {'vertex' : 0, 'fragment' : 0}
		# for name, stages in push:
		# 	size = self.get_type_size(self.push_constants[name])
		# 	for s in stages.split(','):
		# 		if s in constants:
		# 			constants[s] += size
		# 		else:
		# 			raise Exception('Unsupported shader stage.')

		# return [
		# 	VkPushConstantRange(
		# 		stageFlags = flag, offset = 0,
		# 		size = constants[t]
		# 	)
		# 	for flag, t in [
		# 		(VK_SHADER_STAGE_VERTEX_BIT, 'vertex'),
		# 		(VK_SHADER_STAGE_FRAGMENT_BIT, 'fragment'),
		# 		VK_SHADER_STAGE_ALL_GRAPHICS
		# 	] # duplicate info in vk_shaders
		# ]
		# TODO test how a shader with push constants in multiple stages handles this
		# might just change how this is setup, 
		# requiring that everything in a push_constant is labeled at each shader stage

		size = 0
		pc_data_format = []
		for name in push:
			t = self.push_constants[name]
			size += self.get_type_size(t)
			pc_data_format.append((name, self.get_type_format(t)))

		pc_range = [
			VkPushConstantRange(
				stageFlags = VK_SHADER_STAGE_ALL_GRAPHICS, offset = 0,
				size = size
			)
		] 
		# potentially be more precise with what stages are used
		# may actually be required

		pc_dtype = np.dtype(pc_data_format) if pc_data_format else None

		return pc_range, pc_dtype


	@staticmethod
	def get_type_size(t):
		# this is a little silly
		return {
			'vec4': 16,
			'mat4': 64
		}[t]

	@staticmethod
	def get_type_format(t):
		# this is a little silly
		return {
			'vec4': '(4,)f4',
			'mat4': '(4,4)f4'
		}[t]
				

if __name__ == 'never':
	ShaderAttributeLayout(
		attributes = [
			('model', 'mat4'),
			('color', 'vec4'),
			('color2', 'vec4', 'VK_FORMAT_R32G32B32A32_SFLOAT'), # forces a format aside from the default
			('material_id', 'int'),
		],
		push_constants = {
			# doesn't specify how it's laid out in memory
			# just lists what push constants are needed to store
			# these will be the same between all render calls for the instance group
			#	unless a global constant

			'box_viewProj': 'mat4', 
			# names that start with 'box_' will be recognized as globals
		},
		bindings = {
			'material_data':[ # array as value implies unique data type
				(
					'data',
					[ # an array as the second element represents a struct
						('color', 'vec3'),
						('uv_size', 'vec2'),
						('uv_pos', 'vec2'), # not sure how much offsets are needed
						('texture_id', 'int'),
					],
					32 # an integer after the 2nd position represents an array and it's element count
					# can force a data type if not a struct, 
					# the array size and format can be any order after the 2nd
				)
			],

			# tuple as value implies built-in data type
			'texture_atlas': ('texture2D', 8), 
			'samp': ('sampler',),
			'texEffect': ('sampler2D',),
		},
	)
	
	# then in the pipeline layout, pass in a dict of used data
	# probably merge pipeline layout with graphics pipline
	# or turn pipeline layout into shader attributes layout
	# or just move functionality to pipeline layout
	
	class PipelineLayout: ... #just to ignore syntax
	PipelineLayout(
		{
			'attributes':[
				('model', 2), # string is the attribute used
				('color', 6), # integer is the location in the shader
				('material_id', 7), # location will eventually be automatic
			],
			'push constants':[
				'box_viewProj',
			],
			'bindings':[
				('material_data', 0, 'vertex,fragment'), # string is the ubo name or texture name
				('texture_atlas', 1, 'fragment'), # integer is the binding
				('samp', 2, 'fragment'), # last string is stage used, no whitespace allowed

				# uniforms and textures can be combined into bindings 
				# since their names can't overlap anyways
			]
		}
	)
	
	



