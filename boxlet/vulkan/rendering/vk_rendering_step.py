

class RenderingStep:
	'''
	Manages a tree of render steps, such as 
	beginning and ending render passes,
	binding piplines, or making render calls.

	After a RenderingStep begins, 
	it will loop through all its attachments to begin,
	afterwhich the original RenderingStep will call its end function.
	'''
	base_attachments:list['RenderingStep'] = []

	keyed_attachments:dict[str, list['RenderingStep']] = {}

	def __init__(self, priority = 0, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.attached_steps:list['RenderingStep'] = []
		self.priority = priority

	def attach(self, step:'RenderingStep'):
		RenderingStep._attach_to_list(self.attached_steps, step)

	def attach_to_key(self, key:str):
		att = RenderingStep.keyed_attachments.setdefault(key, list())
		RenderingStep._attach_to_list(att, self)

	def attach_to_base(self):
		RenderingStep._attach_to_list(RenderingStep.base_attachments, self)

	def full_begin(self, command_buffer):
		'''
		Calls the begin and end functions while looping through any attached render steps.
		'''
		self.begin(command_buffer)

		for att in self.attached_steps:
			att.full_begin(command_buffer)
			
		self.end(command_buffer)

	def begin(self, command_buffer): ...

	def end(self, command_buffer): ...

	@staticmethod
	def _attach_to_list(attach_list:list['RenderingStep'], step):
		attach_list.append(step)
		attach_list.sort(key = lambda r : r.priority)

	@staticmethod
	def begin_from_base(command_buffer):
		'Loops through all rendering steps attached to the base class'
		for att in RenderingStep.base_attachments:
			att.full_begin(command_buffer)


class KeyedStep(RenderingStep):
	'''
	Loops through a list of rendering steps that are attached to a key instead of ones that are attached to this object.
	'''
	def __init__(self, key, priority):
		self.key = key
		self.priority = priority

	def full_begin(self, command_buffer):
		for att in RenderingStep.keyed_attachments[self.key]:
			att.full_begin(command_buffer)
