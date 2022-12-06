import os

import pygame
import numpy as np

USE_OPENGL = os.environ.get('BOXLET_RENDER_MODE', 'sdl2') == 'opengl'
USE_VULKAN = os.environ.get('BOXLET_RENDER_MODE', 'sdl2') == 'vulkan'


from .math_extra import *
# if USE_OPENGL:
# 	from .opengl import transform_math as Tmath 

# 	from .opengl.boxlet_gl import BoxletGL
	
# 	from .opengl.render_bases.renderer import Renderer
# 	from .opengl.render_bases.render_pass import RenderPass
# 	from .opengl.render_bases.render_target import RenderTarget
# 	from .opengl.render_instance_metaclass import RenderInstance

# else:
# 	class BoxletGL:
# 		@staticmethod
# 		def render():
# 			if not USE_OPENGL:
# 				raise Exception('BoxletGL not imported properly')

# 		@staticmethod
# 		def add_render_call(pass_name, shader, call):
# 			if not USE_OPENGL:
# 				raise Exception('BoxletGL not imported properly')


from .entity import Entity
from .manager import Manager as __Manager
from .vary_floats import VaryFloats

manager = __Manager()

# anything using opengl when imported needs to be imported AFTER pygame is initialized
# if USE_OPENGL:
# 	from .opengl.transform import Transform
# 	from .opengl.model import Model
# 	from .opengl.texture import Texture, MultiTexture
# 	from .opengl.shader import Shader, VertFragShader, ComputeShader

# 	from .opengl.render_bases.render_pass import PassOpaque

# 	from .opengl.render_targets.render_target_frame_buffer import FrameBufferStep, ApplyShaderToFrame, ApplyDitherToFrame, SimpleClearStep
# 	from .opengl.render_targets.camera_3d import Camera3D
# 	from .opengl.render_targets.camera_2d import Camera2D
# 	from .opengl.renderers.terrain_renderer import TerrainRenderer
# 	from .opengl.renderers.instanced_renderer import InstancedRenderer

# 	from .opengl.camera_controller import CameraController

# if USE_VULKAN:
# 	from .vulkan import Mesh, MultiMesh
# 	from .vulkan import IndirectRenderer

# if build:
from .debug import Debug
