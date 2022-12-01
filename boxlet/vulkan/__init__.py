# a majority of this is from 
# https://www.youtube.com/watch?v=drregGzhgCA&list=PLn3eTxaOtL2M4qgHpHuxY821C_oX0GvM7&index=3


#statically load vulkan library
from vulkan import *
import numpy as np
import pyrr

"""
 Statically linking the prebuilt header from the lunarg sdk will load
 most functions, but not all.
 
 Functions can also be dynamically loaded, using the call
 
 PFN_vkVoidFunction vkGetInstanceProcAddr(
    VkInstance                                  instance,
    string                                      pName);
 or
 PFN_vkVoidFunction vkGetDeviceProcAddr(
	VkDevice                                    device,
	string                                      pName);
	We will look at this later, once we've created an instance and device.
"""

DEBUG_MODE = False

from pathlib import Path

def get_path(file:str):
	return Path(__file__).parent / f'{file}'

from . import vk_instance
from . import vk_logging
from . import vk_queue_families
from . import vk_device
from . import vk_sync
from . import vk_frame
from . import vk_swapchain
from . import vk_shaders
from . import vk_memory
from . import vk_mesh
from . import vk_pipeline
from . import vk_framebuffer
from . import vk_commands

from . import vk_renderer

from .engine import Engine

from . import app
