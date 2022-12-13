from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from . import *

class BVKC:
	# use to hold and share variables that are almost always constants
	# meant to be part of BoxletVK, but due to how things are laid out,
	#	There needs to be a seperate point of reference

	logical_device:'vk_device.LogicalDevice' = None
	physical_device = None
	swapchain:'vk_swapchain.SwapChainBundle' = None
	command_pool:'CommandPool' = None
	graphics_queue = None
	present_queue = None

	# currently, we will assume that there will only ever be ...
	# one logical device 
	# one physical device

	# potentially move instance and surface here

