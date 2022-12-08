# a majority of this is from 
# https://www.youtube.com/watch?v=drregGzhgCA&list=PLn3eTxaOtL2M4qgHpHuxY821C_oX0GvM7&index=3

DEBUG_MODE = False

from pathlib import Path

def get_path(file:str):
	return Path(__file__).parent / f'{file}'

import numpy as np

from . import vk_instance
from . import vk_logging
from . import vk_queue_families
from . import vk_device
from . import vk_sync
from .vk_framebuffer import FrameBuffer
from . import vk_frame
from . import vk_swapchain
from . import vk_shaders
from . import vk_memory
from .vk_mesh import Mesh, MultiMesh
from .vk_pipeline import RenderPass, PipelineLayout, GraphicsPipeline
from .vk_commands import CommandPool, CommandBuffer

from .vk_renderer import Renderer, IndirectRenderer

from .boxlet_vk import BoxletVK
