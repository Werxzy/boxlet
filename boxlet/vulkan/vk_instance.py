from . import DEBUG_MODE
from .vk_module import *


class VulkanInstance:
	def __init__(self, application_name, driver):

		self.driver = driver

		if DEBUG_MODE:
			print('Making an instance...')

		version = vkEnumerateInstanceVersion()

		if DEBUG_MODE:
			print(f'''System can support vulkan Variant: {version >> 29}
			Major: {VK_VERSION_MAJOR(version)}
			Minor: {VK_VERSION_MINOR(version)}
			Patch: {VK_VERSION_PATCH(version)}'''.replace('\t',''))

		#vulkan version
		version = VK_MAKE_VERSION(1, 0, 0)

		appInfo = VkApplicationInfo(
			pApplicationName = application_name,
			applicationVersion = version,
			pEngineName = "Boxlet",
			engineVersion = version,
			apiVersion = version
		)

		"""
			Everything with Vulkan is "opt-in", so we need to query which extensions glfw needs
			in order to interface with vulkan.
		"""

		match driver:
			case 'windows':
				extensions = [
					VK_KHR_SURFACE_EXTENSION_NAME, 
					VK_KHR_WIN32_SURFACE_EXTENSION_NAME
				]
			case 'x11':
				extensions = [
					VK_KHR_SURFACE_EXTENSION_NAME, 
					VK_KHR_XLIB_SURFACE_EXTENSION_NAME, 
					VK_KHR_DISPLAY_EXTENSION_NAME
				]
			case 'cocoa':
				extensions = [
					VK_KHR_SURFACE_EXTENSION_NAME, 
					VK_MVK_MACOS_SURFACE_EXTENSION_NAME,
					VK_MVK_MOLTENVK_EXTENSION_NAME
				]
			case _:
				raise Exception(f'driver {driver} not supported yet.')
		# TODO !!! this will need to be updated based on platform
		# OR find a function that gets a list of these automatically.
		# not sure if pygame has this easily available

		layers = []

		if DEBUG_MODE:
			extensions.append(VK_EXT_DEBUG_REPORT_EXTENSION_NAME)

			print(f"extensions to be requested:")

			for extensionName in extensions:
				print(f"\t\" {extensionName}\"")

			layers.append('VK_LAYER_KHRONOS_validation')

		VulkanInstance.supported(extensions, layers)

		createInfo = VkInstanceCreateInfo(
			pApplicationInfo = appInfo,
			enabledLayerCount = len(layers), ppEnabledLayerNames = layers,
			enabledExtensionCount = len(extensions), ppEnabledExtensionNames = extensions
		)

		try:
			self.vk_addr = vkCreateInstance(createInfo, None)
		except:
			if DEBUG_MODE:
				print("Failed to create Instance!")
			return None

	@staticmethod
	def supported(extensions, layers):

		supported_extensions = [extension.extensionName for extension in vkEnumerateInstanceExtensionProperties(None)]

		if DEBUG_MODE:
			print("Device can support the following extensions:")
			for supportedExtension in supported_extensions:
				print(f"\t\"{supportedExtension}\"")

		for extension in extensions:
			
			if extension in supported_extensions:
				if DEBUG_MODE:
					print(f"Extension \"{extension}\" is supported!")
			else:
				if DEBUG_MODE:
					print(f"Extension \"{extension}\" is not supported!")
				return False

		#check layer support
		supported_layers = [layer.layerName for layer in vkEnumerateInstanceLayerProperties()]

		if DEBUG_MODE:
			print("Device can support the following layers:")
			for layer in supported_layers:
				print(f"\t\"{layer}\"")

		for layer in layers:
			if layer in supported_layers:
				if DEBUG_MODE:
					print(f"Layer \"{layer}\" is supported!")
			else:
				if DEBUG_MODE:
					print(f"Layer \"{layer}\" is not supported!")
				return False

		return True

	def destroy(self):
		vkDestroyInstance(self.vk_addr, None)