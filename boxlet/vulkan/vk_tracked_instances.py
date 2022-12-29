from typing import Self, TypeVar, final


I = TypeVar('I')

class TrackedInstances:
	'''
	This class holds all instances of a subclass in the first layer of it's inheritance.

	Any subclasses of the same class, which itself is a subclass of TrackedInstances, will share the same instance list.

	NOT related to a vulkan instance.
	'''

	def __init_subclass__(cls) -> None:
		if cls.__base__ is TrackedInstances:
			cls._all_instances = []

	def __new__(cls: type[Self], *args, **kwargs) -> Self:
		ob = super().__new__(cls)
		cls._all_instances.append(ob)
		return ob

	@final
	def destroy(self):
		self.on_destroy()
		self._all_instances.remove(self)

	def on_destroy(self):
		...

	@classmethod
	def _destroy_all(cls):
		for inst in cls.get_all_instances():
			inst.on_destroy()
		cls._all_instances.clear()
		
	@classmethod
	def get_all_instances(cls:type[I]) -> list[I]:
		'''
		Returns a list of the class that inherits from classes whose first base class is TrackedInstances.
		
		Will not return all instances of TrackedInstances or specifically of the selected subclass.

		This function is more for syntax highlighting.
		'''
		return cls._all_instances

