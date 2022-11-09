from typing import Callable
from OpenGL.GL import *


UNIFORM_TYPE_DICT:dict[int, tuple[Callable, int, int, str]] = {
	GL_FLOAT : (glUniform1fv, GL_FLOAT, 1, 'f4'), 
	GL_FLOAT_VEC2 : (glUniform2fv, GL_FLOAT, 2, '(2,)f4'), 
	GL_FLOAT_VEC3 : (glUniform3fv, GL_FLOAT, 3, '(3,)f4'), 
	GL_FLOAT_VEC4 : (glUniform4fv, GL_FLOAT, 4, '(4,)f4'), 
	GL_INT : (glUniform1iv, GL_INT, 1, 'i4'), 
	GL_INT_VEC2 : (glUniform2iv, GL_INT, 2, '(2,)i4'), 
	GL_INT_VEC3 : (glUniform3iv, GL_INT, 3, '(3,)i4'), 
	GL_INT_VEC4 : (glUniform4iv, GL_INT, 4, '(4,)i4'), 
	GL_UNSIGNED_INT : (glUniform1uiv, GL_UNSIGNED_INT, 1, 'u4'), 
	GL_UNSIGNED_INT_VEC2 : (glUniform2uiv, GL_UNSIGNED_INT, 2, '(2,)u4'), 
	GL_UNSIGNED_INT_VEC3 : (glUniform3uiv, GL_UNSIGNED_INT, 3, '(3,)u4'), 
	GL_UNSIGNED_INT_VEC4 : (glUniform4uiv, GL_UNSIGNED_INT, 4, '(4,)u4'), 
	GL_BOOL : (glUniform1iv, GL_INT, 1, '?4'), 
	GL_BOOL_VEC2 : (glUniform2iv, GL_INT, 2, '(2,)?4'), 
	GL_BOOL_VEC3 : (glUniform3iv, GL_INT, 3, '(3,)?4'), 
	GL_BOOL_VEC4 : (glUniform4iv, GL_INT, 4, '(4,)?4'), 
	# unsure if bool is allowed as vertex attribute
	#	or if '(2,)?4' is even a valid dtype
	#	Though it's probably wasteful

	# GL_FLOAT_MAT2 : (glUniformMatrix2fv, GL_FLOAT, None), 
	# GL_FLOAT_MAT3 : (glUniformMatrix3fv, GL_FLOAT, None), 
	GL_FLOAT_MAT4 : (glUniformMatrix4fv, GL_FLOAT, 16, '(4,4)f4'), 
	# GL_FLOAT_MAT2x3 : (glUniformMatrix2x3fv, GL_FLOAT, None), 
	# GL_FLOAT_MAT2x4 : (glUniformMatrix2x4fv, GL_FLOAT, None), 
	# GL_FLOAT_MAT3x2 : (glUniformMatrix3x2fv, GL_FLOAT, None), 
	# GL_FLOAT_MAT3x4 : (glUniformMatrix3x4fv, GL_FLOAT, None), 
	# GL_FLOAT_MAT4x2 : (glUniformMatrix4x2fv, GL_FLOAT, None), 
	# GL_FLOAT_MAT4x3 : (glUniformMatrix4x3fv, GL_FLOAT, None),  
	# # unsure how the other matricies are implemented yet.

	# GL_DOUBLE : glUniform1dv, 
	# GL_DOUBLE_VEC2 : glUniform2dv, 
	# GL_DOUBLE_VEC3 : glUniform3dv, 
	# GL_DOUBLE_VEC4 : glUniform4dv, 

	# GL_DOUBLE_MAT2 : glUniformMatrix2fv, 
	# GL_DOUBLE_MAT3 : glUniformMatrix3fv, 
	# GL_DOUBLE_MAT4 : glUniformMatrix4fv, 
	# GL_DOUBLE_MAT2x3 : glUniformMatrix2x3fv, 
	# GL_DOUBLE_MAT2x4 : glUniformMatrix2x4fv, 
	# GL_DOUBLE_MAT3x2 : glUniformMatrix3x2fv, 
	# GL_DOUBLE_MAT3x4 : glUniformMatrix3x4fv, 
	# GL_DOUBLE_MAT4x2 : glUniformMatrix4x2fv, 
	# GL_DOUBLE_MAT4x3 : glUniformMatrix4x3fv, 
}
# There are more, but I don't know yet what else is needed
# https://registry.khronos.org/OpenGL-Refpages/gl4/html/glGetActiveUniform.xhtml

VECTOR_TYPES = {
	'f' : [
		GL_FLOAT, 
		GL_FLOAT_VEC2, 
		GL_FLOAT_VEC3, 
		GL_FLOAT_VEC4
	],
	'i' : [
		GL_INT, 
		GL_INT_VEC2, 
		GL_INT_VEC3, 
		GL_INT_VEC4
	],
	'u' : [
		GL_UNSIGNED_INT, 
		GL_UNSIGNED_INT_VEC2, 
		GL_UNSIGNED_INT_VEC3, 
		GL_UNSIGNED_INT_VEC4
	],
	'b' : [
		GL_BOOL, 
		GL_BOOL_VEC2, 
		GL_BOOL_VEC3, 
		GL_BOOL_VEC4
	],
}

UNIFORM_TEXTURE_DICT = {
	GL_SAMPLER_1D : (GL_TEXTURE_1D,),
	GL_SAMPLER_2D : (GL_TEXTURE_2D,),
	GL_SAMPLER_3D : (GL_TEXTURE_3D,),
	GL_SAMPLER_CUBE : (GL_TEXTURE_CUBE_MAP,),
	GL_SAMPLER_1D_ARRAY : (GL_TEXTURE_1D_ARRAY,),
	GL_SAMPLER_2D_ARRAY : (GL_TEXTURE_2D_ARRAY,),
	GL_SAMPLER_2D_MULTISAMPLE : (GL_TEXTURE_2D_MULTISAMPLE ,),
	GL_SAMPLER_2D_MULTISAMPLE_ARRAY : (GL_TEXTURE_2D_MULTISAMPLE_ARRAY,),
	GL_SAMPLER_BUFFER : (GL_TEXTURE_BUFFER,),
	GL_SAMPLER_2D_RECT : (GL_TEXTURE_2D,),

	GL_SAMPLER_1D_SHADOW : (GL_TEXTURE_1D,),
	GL_SAMPLER_2D_SHADOW : (GL_TEXTURE_2D,),
	GL_SAMPLER_1D_ARRAY_SHADOW : (GL_TEXTURE_1D_ARRAY,),
	GL_SAMPLER_2D_ARRAY_SHADOW : (GL_TEXTURE_2D_ARRAY,),
	GL_SAMPLER_CUBE_SHADOW : (GL_TEXTURE_CUBE_MAP,),
	GL_SAMPLER_2D_RECT_SHADOW : (GL_TEXTURE_2D,),

	GL_INT_SAMPLER_1D : (GL_TEXTURE_1D,),
	GL_INT_SAMPLER_2D : (GL_TEXTURE_2D,),
	GL_INT_SAMPLER_3D : (GL_TEXTURE_3D,),
	GL_INT_SAMPLER_CUBE : (GL_TEXTURE_CUBE_MAP,),
	GL_INT_SAMPLER_1D_ARRAY : (GL_TEXTURE_1D_ARRAY,),
	GL_INT_SAMPLER_2D_ARRAY : (GL_TEXTURE_2D_ARRAY,),
	GL_INT_SAMPLER_2D_MULTISAMPLE : (GL_TEXTURE_2D_MULTISAMPLE,),
	GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY : (GL_TEXTURE_2D_MULTISAMPLE_ARRAY,),
	GL_INT_SAMPLER_BUFFER : (GL_TEXTURE_BUFFER,),
	GL_INT_SAMPLER_2D_RECT : (GL_TEXTURE_2D,),
	
	GL_UNSIGNED_INT_SAMPLER_1D : (GL_TEXTURE_1D,),
	GL_UNSIGNED_INT_SAMPLER_2D : (GL_TEXTURE_2D,),
	GL_UNSIGNED_INT_SAMPLER_3D : (GL_TEXTURE_3D,),
	GL_UNSIGNED_INT_SAMPLER_CUBE : (GL_TEXTURE_CUBE_MAP,),
	GL_UNSIGNED_INT_SAMPLER_1D_ARRAY : (GL_TEXTURE_1D_ARRAY,),
	GL_UNSIGNED_INT_SAMPLER_2D_ARRAY : (GL_TEXTURE_2D_ARRAY,),
	GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE : (GL_TEXTURE_2D_MULTISAMPLE,),
	GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY : (GL_TEXTURE_2D_MULTISAMPLE_ARRAY,),
	GL_UNSIGNED_INT_SAMPLER_BUFFER : (GL_TEXTURE_BUFFER,),
	GL_UNSIGNED_INT_SAMPLER_2D_RECT : (GL_TEXTURE_2D,),
}

UNIFORM_SYMBOL_DICT = {
	'float' : GL_FLOAT,
	'vec2' : GL_FLOAT_VEC2,
	'vec3' : GL_FLOAT_VEC3,
	'vec4' : GL_FLOAT_VEC4,
	'int' : GL_INT,
	'ivec2' : GL_INT_VEC2,
	'ivec3' : GL_INT_VEC3,
	'ivec4' : GL_INT_VEC4,
	'uint' : GL_UNSIGNED_INT,
	'uvec2' : GL_UNSIGNED_INT_VEC2,
	'uvec3' : GL_UNSIGNED_INT_VEC3,
	'uvec4' : GL_UNSIGNED_INT_VEC4,
	'bool' : GL_BOOL,
	'bvec2' : GL_BOOL_VEC2,
	'bvec3' : GL_BOOL_VEC3,
	'bvec4' : GL_BOOL_VEC4,
	# 'mat2' : GL_FLOAT_MAT2,
	# 'mat3' : GL_FLOAT_MAT3,
	'mat4' : GL_FLOAT_MAT4,
	# 'mat2x3' : GL_FLOAT_MAT2x3,
	# 'mat2x4' : GL_FLOAT_MAT2x4,
	# 'mat3x2' : GL_FLOAT_MAT3x2,
	# 'mat3x4' : GL_FLOAT_MAT3x4,
	# 'mat4x2' : GL_FLOAT_MAT4x2,
	# 'mat4x3' : GL_FLOAT_MAT4x3,

	'sampler1D' : GL_SAMPLER_1D,
	'sampler2D' : GL_SAMPLER_2D,
	'sampler3D' : GL_SAMPLER_3D,
	'samplerCube' : GL_SAMPLER_CUBE,
	'sampler1DShadow' : GL_SAMPLER_1D_SHADOW,
	'sampler2DShadow' : GL_SAMPLER_2D_SHADOW,
	'sampler1DArray' : GL_SAMPLER_1D_ARRAY,
	'sampler2DArray' : GL_SAMPLER_2D_ARRAY,
	'sampler1DArrayShadow' : GL_SAMPLER_1D_ARRAY_SHADOW,
	'sampler2DArrayShadow' : GL_SAMPLER_2D_ARRAY_SHADOW,
	'sampler2DMS' : GL_SAMPLER_2D_MULTISAMPLE,
	'sampler2DMSArray' : GL_SAMPLER_2D_MULTISAMPLE_ARRAY,
	'samplerCubeShadow' : GL_SAMPLER_CUBE_SHADOW,
	'samplerBuffer' : GL_SAMPLER_BUFFER,
	'sampler2DRect' : GL_SAMPLER_2D_RECT,
	'sampler2DRectShadow' : GL_SAMPLER_2D_RECT_SHADOW,
	'isampler1D' : GL_INT_SAMPLER_1D,
	'isampler2D' : GL_INT_SAMPLER_2D,
	'isampler3D' : GL_INT_SAMPLER_3D,
	'isamplerCube' : GL_INT_SAMPLER_CUBE,
	'isampler1DArray' : GL_INT_SAMPLER_1D_ARRAY,
	'isampler2DArray' : GL_INT_SAMPLER_2D_ARRAY,
	'isampler2DMS' : GL_INT_SAMPLER_2D_MULTISAMPLE,
	'isampler2DMSArray' : GL_INT_SAMPLER_2D_MULTISAMPLE_ARRAY,
	'isamplerBuffer' : GL_INT_SAMPLER_BUFFER,
	'isampler2DRect' : GL_INT_SAMPLER_2D_RECT,
	'usampler1D' : GL_UNSIGNED_INT_SAMPLER_1D,
	'usampler2D' : GL_UNSIGNED_INT_SAMPLER_2D,
	'usampler3D' : GL_UNSIGNED_INT_SAMPLER_3D,
	'usamplerCube' : GL_UNSIGNED_INT_SAMPLER_CUBE,
	'usampler2DArray' : GL_UNSIGNED_INT_SAMPLER_1D_ARRAY,
	'usampler2DArray' : GL_UNSIGNED_INT_SAMPLER_2D_ARRAY,
	'usampler2DMS' : GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE,
	'usampler2DMSArray' : GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE_ARRAY,
	'usamplerBuffer' : GL_UNSIGNED_INT_SAMPLER_BUFFER,
	'usampler2DRect' : GL_UNSIGNED_INT_SAMPLER_2D_RECT,

	# Currently unsupported due currently being restricted to version 3.3.

	# 'double' : GL_DOUBLE,
	# 'dvec2' : GL_DOUBLE_VEC2,
	# 'dvec3' : GL_DOUBLE_VEC3,
	# 'dvec4' : GL_DOUBLE_VEC4,

	# 'dmat2' : GL_DOUBLE_MAT2,
	# 'dmat3' : GL_DOUBLE_MAT3,
	# 'dmat4' : GL_DOUBLE_MAT4,
	# 'dmat2x3' : GL_DOUBLE_MAT2x3,
	# 'dmat2x4' : GL_DOUBLE_MAT2x4,
	# 'dmat3x2' : GL_DOUBLE_MAT3x2,
	# 'dmat3x4' : GL_DOUBLE_MAT3x4,
	# 'dmat4x2' : GL_DOUBLE_MAT4x2,
	# 'dmat4x3' : GL_DOUBLE_MAT4x3,

	# 'image1D' : GL_IMAGE_1D,
	# 'image2D' : GL_IMAGE_2D,
	# 'image3D' : GL_IMAGE_3D,
	# 'image2DRect' : GL_IMAGE_2D_RECT,
	# 'imageCube' : GL_IMAGE_CUBE,
	# 'imageBuffer' : GL_IMAGE_BUFFER,
	# 'image1DArray' : GL_IMAGE_1D_ARRAY,
	# 'image2DArray' : GL_IMAGE_2D_ARRAY,
	# 'image2DMS' : GL_IMAGE_2D_MULTISAMPLE,
	# 'image2DMSArray' : GL_IMAGE_2D_MULTISAMPLE_ARRAY,
	# 'iimage1D' : GL_INT_IMAGE_1D,
	# 'iimage2D' : GL_INT_IMAGE_2D,
	# 'iimage3D' : GL_INT_IMAGE_3D,
	# 'iimage2DRect' : GL_INT_IMAGE_2D_RECT,
	# 'iimageCube' : GL_INT_IMAGE_CUBE,
	# 'iimageBuffer' : GL_INT_IMAGE_BUFFER,
	# 'iimage1DArray' : GL_INT_IMAGE_1D_ARRAY,
	# 'iimage2DArray' : GL_INT_IMAGE_2D_ARRAY,
	# 'iimage2DMS' : GL_INT_IMAGE_2D_MULTISAMPLE,
	# 'iimage2DMSArray' : GL_INT_IMAGE_2D_MULTISAMPLE_ARRAY,
	# 'uimage1D' : GL_UNSIGNED_INT_IMAGE_1D,
	# 'uimage2D' : GL_UNSIGNED_INT_IMAGE_2D,
	# 'uimage3D' : GL_UNSIGNED_INT_IMAGE_3D,
	# 'uimage2DRect' : GL_UNSIGNED_INT_IMAGE_2D_RECT,
	# 'uimageCube' : GL_UNSIGNED_INT_IMAGE_CUBE,
	# 'uimageBuffer' : GL_UNSIGNED_INT_IMAGE_BUFFER,
	# 'uimage1DArray' : GL_UNSIGNED_INT_IMAGE_1D_ARRAY,
	# 'uimage2DArray' : GL_UNSIGNED_INT_IMAGE_2D_ARRAY,
	# 'uimage2DMS' : GL_UNSIGNED_INT_IMAGE_2D_MULTISAMPLE,
	# 'uimage2DMSArray' : GL_UNSIGNED_INT_IMAGE_2D_MULTISAMPLE_ARRAY,
	# 'atomic_uint' : GL_UNSIGNED_INT_ATOMIC_COUNTER,
}