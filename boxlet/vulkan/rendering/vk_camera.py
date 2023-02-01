import numpy as np

from .. import CameraBase, PushConstantManager, RenderingStep


class Camera3D(CameraBase, RenderingStep):
	def __init__(self, horizontal_fov = False, priority = 0) -> None:
		super().__init__(horizontal_fov = horizontal_fov, invert_y = -1, priority = priority)

		PushConstantManager.set_global('box_viewProj', np.identity(4, dtype=np.float32))
		PushConstantManager.set_global('box_view', np.identity(4, dtype=np.float32))

		self.attach_to_base()

	def begin(self, command_buffer):
		view_mat, _, view_proj_mat = self.get_matricies()
		PushConstantManager.set_global('box_viewProj', view_proj_mat)
		PushConstantManager.set_global('box_view', view_mat)

	def get_matricies(self):
		'Returns the view, projection, and view*proj matricies.'
		inv_mod = np.linalg.inv(self.model_matrix)
		return inv_mod, self.proj_matrix, np.matmul(inv_mod, self.proj_matrix)


