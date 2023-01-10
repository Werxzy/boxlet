# A majority of this code is from the channel GetIntoGameDev.
# https://www.youtube.com/watch?v=drregGzhgCA&list=PLn3eTxaOtL2M4qgHpHuxY821C_oX0GvM7
# Though now it has been heavily modified to suit the needs of this engine.
#	Also, to better match python's conventions.

DEBUG_MODE = False

from pathlib import Path

def get_path(file:str):
	return Path(__file__).parent / f'{file}'

import numpy as np

from ..util_3d import CameraBase, CameraController, Tmath, Transform

from .vk_instance import VulkanInstance 
from .vk_logging import DebugMessenger, Logging
from .vk_queue_families import QueueFamilyIndices
from .vk_device import PhysicalDevice, LogicalDevice
from .vk_sync import Semaphore, Fence
from .vk_commands import CommandPool, CommandBuffer

from .memory_structures.vk_buffer import Buffer, UniformBufferGroup
from .memory_structures.vk_instance_buffer import InstanceBufferSet
from .memory_structures.vk_mesh import Mesh, MultiMesh

from .images.vk_framebuffer import FrameBuffer
from .images.vk_image_view import ImageView
from .images.vk_swapchain_frame import SwapChainFrame
from .images.vk_texture import Texture

from .rendering.vk_shader_attribute_layout import ShaderAttributeLayout
from .rendering.vk_render_target import RenderTarget, SimpleRenderTarget
from .rendering.vk_swapchain import SwapChainBundle
from .rendering.vk_shaders import Shader
from .rendering.vk_rendering_step import RenderingStep, KeyedStep
from .rendering.vk_render_pass import RenderPass
from .rendering.vk_pipeline import PipelineLayout, GraphicsPipeline

from .rendering.renderer_classes import Renderer, IndirectRenderer, ScreenRenderer, PushConstantManager

from .rendering.vk_camera import Camera3D

from .boxlet_vk import BoxletVK

