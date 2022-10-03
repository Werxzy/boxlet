import os
os.environ['BOXLET_RENDER_MODE'] = 'opengl'
os.environ['BOXLET_OPENGL_VSYNC'] = '1'
def true_path(file):
	return os.path.join(os.path.dirname(__file__), file)

from boxlet import *

# render assets/pipeline
# box_model = Model.load_obj("examples/opengl_example/cube.obj")
box_texture = Texture(pygame.image.load(true_path("examples/opengl_example/box.png")), nearest=False)

SimpleClearStep(queue = 0)
camera = Camera3D(queue = 50)
models = MultiModelRenderer(None, box_texture, queue = 100)


# world assets
cc = CameraController(camera)
cc.pos[:] = (0,0,-4)

manager.run()

