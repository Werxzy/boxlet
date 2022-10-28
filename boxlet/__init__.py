import pygame
import numpy as np

import os
USE_OPENGL = os.environ.get('BOXLET_RENDER_MODE', 'sdl2') == 'opengl'

from boxlet.math_extra import *
if USE_OPENGL:
	import boxlet.opengl.transform_math as Tmath 

	from boxlet.opengl.renderer import Renderer
	from boxlet.opengl.render_instance_metaclass import RenderInstance

from boxlet.entity import Entity
from boxlet.manager import instance as manager
from boxlet.vary_floats import VaryFloats

if USE_OPENGL:
	from boxlet.opengl.transform import Transform
	from boxlet.opengl.model import Model
	from boxlet.opengl.shader import Shader, VertFragShader, ComputeShader
	from boxlet.opengl.texture import Texture, MultiTexture

	# anything using opengl when imported needs to be imported AFTER pygame is initialized
	# from boxlet.opengl.sprite_renderer import SpriteRenderer
	# from boxlet.opengl.sprite_instanced_renderer import SpriteInstancedRenderer
	from boxlet.opengl.sprite_palette_instanced_renderer import SpritePaletteInstancedRenderer
	from boxlet.opengl.camera_3d import Camera3D
	from boxlet.opengl.camera_2d import Camera2D
	from boxlet.opengl.model_instanced_renderer import ModelInstancedRenderer
	from boxlet.opengl.render_steps import FrameBufferStep, ApplyShaderToFrame, ApplyDitherToFrame, SimpleClearStep
	from boxlet.opengl.terrain_renderer import TerrainRenderer

	from boxlet.opengl.camera_controller import CameraController

# if build:
from boxlet.debug import Debug

del USE_OPENGL
