import numpy as np

from .. import PushConstantManager, CameraBase, RenderingStep


class Camera3D(CameraBase, RenderingStep):
	def __init__(self, horizontal_fov = False, priority = 0) -> None:
		super().__init__(horizontal_fov = horizontal_fov, invert_y = -1, priority = priority)

		PushConstantManager.set_global('box_viewProj', np.identity(4, dtype=np.float32))
		PushConstantManager.set_global('box_view', np.identity(4, dtype=np.float32))

		self.attach_to_base()

	def begin(self, command_buffer):
		inv_mod = np.linalg.inv(self.model_matrix)
		PushConstantManager.set_global('box_viewProj', np.matmul(inv_mod, self.proj_matrix))
		PushConstantManager.set_global('box_view', inv_mod)

