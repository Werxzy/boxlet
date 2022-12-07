from vulkan import *
from .vk_tracked_instances import TrackedInstances
# imports vulkan module ONCE
# This is a big module that usually shouldn't be imported

# non-boxlet projects can import vulkan using 
# 'from boxlet.vulkan._vk_module import *'
# and can replace * with used variables/functions