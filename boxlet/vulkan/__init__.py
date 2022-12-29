# A majority of this code is from the channel GetIntoGameDev.
# https://www.youtube.com/watch?v=drregGzhgCA&list=PLn3eTxaOtL2M4qgHpHuxY821C_oX0GvM7
# Though now it has been heavily modified to suit the needs of this engine.

DEBUG_MODE = True

from pathlib import Path

def get_path(file:str):
	return Path(__file__).parent / f'{file}'

import numpy as np

from ..util_3d import CameraBase, CameraController, Tmath, Transform

from .rendering.vk_shader_attribute_layout import ShaderAttributeLayout
from . import vk_instance
from . import vk_logging
from . import vk_queue_families
from . import vk_device
from . import vk_sync
from .vk_commands import CommandPool, CommandBuffer

from .memory_structures.vk_buffer import Buffer, UniformBufferGroup
from .memory_structures.vk_instance_buffer import InstanceBufferSet
from .memory_structures.vk_mesh import Mesh, MultiMesh

from .images.vk_framebuffer import FrameBuffer
from .images.vk_image_view import ImageView
from .images.vk_swapchain_frame import SwapChainFrame
from .images.vk_texture import Texture

from .rendering.vk_render_target import RenderTarget, SimpleRenderTarget
from .rendering import vk_swapchain
from .rendering import vk_shaders
from .rendering.vk_rendering_step import RenderingStep, KeyedStep
from .rendering.vk_render_pass import RenderPass
from .rendering.vk_pipeline import PipelineLayout, GraphicsPipeline

from .rendering.vk_renderer import Renderer, IndirectRenderer, PushConstantManager, ScreenRenderer

from .rendering.vk_camera import Camera3D

from .boxlet_vk import BoxletVK

# TODO replace all of the 'from . import' calls
