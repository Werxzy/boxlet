from .. import BoxletGL


class RenderTarget:
	def __init__(self, queue = 0, pass_names:list[str] = None) -> None:
		self.queue = queue
		self.pass_names = pass_names or []
		BoxletGL.add_render_target(self)
	
	def prepare(self):
		...
	
	def post(self):
		...

	def rebuild(self, rebind = True):
		...
	
