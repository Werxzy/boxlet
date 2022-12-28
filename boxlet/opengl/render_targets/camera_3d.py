import numpy as np

from .. import FrameBufferStep, Shader, CameraBase


class Camera3D(CameraBase, FrameBufferStep):
	def __init__(self, width=0, height=0, width_mult=1, height_mult=1, depth=True, nearest=False, queue=0, pass_names: list[str] = None, horizontal_fov = False) -> None:
		super().__init__(width, height, width_mult, height_mult, depth, nearest, queue, pass_names, horizontal_fov = horizontal_fov)

		Shader.add_global_matrix_uniform('box_viewProj', np.identity(4, dtype=np.float32))
		Shader.add_global_matrix_uniform('box_view', np.identity(4, dtype=np.float32))

	def prepare(self):
		super().prepare()
		inv_mod = np.linalg.inv(self.model_matrix)
		Shader.set_global_uniform('box_viewProj', np.matmul(inv_mod, self.proj_matrix))
		Shader.set_global_uniform('box_view', inv_mod)

