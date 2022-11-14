from typing import Callable, TypeVar, final


class Entity:

	watched_callables = ['render', 'vary_update', 'fixed_update']
	watched_events:list[int] = []
	entity_callables:dict[str, list[tuple[type, Callable]]] = {s: [] for s in watched_callables}
	'''Dictionary of each function name and Entity types that have it, along with their callable.\n
	Event functions are event by event's id. `f'event_{id}'`'''

	entity_dict:dict[type, list['Entity']] = {} 
	'''Dictionary of existing entities, organized by type.'''

	entities_to_add:dict[type, list] = {} 
	'''Dictionary of entities recently created, organized by type.'''

	new_created:set[type] = set() 
	'''Set of types of entities recently created.'''

	entities_to_destroy:list['Entity'] = []
	'''Dictionary of entities that need to be destroyed'''

	E = TypeVar('E', bound='Entity')
	
	def __init_subclass__(cls):

		def append_sort(c, f, name):
			Entity.entity_callables[name].append((c, f))
			Entity.entity_callables[name].sort(key = lambda ef: ef[1]._priority if hasattr(ef[1], '_priority') else 0)
			# would prefer to insert the function without sorting the list every single time

		for func in Entity.watched_callables:
			if hasattr(cls, func):
				append_sort(cls, getattr(cls, func), func)

		for attr in dir(cls):
			func = getattr(cls, attr)
			if callable(func) and hasattr(func, '_watched_events'):
				for w in func._watched_events:
					ev = f'event_{w}'
					if w not in Entity.watched_events:
						Entity.watched_events.append(w)
						Entity.entity_callables[ev] = []

					append_sort(cls, func, ev)

		Entity.entity_dict[cls] = []
		Entity.entities_to_add[cls] = []

	def __new__(cls, *args, **kwargs):
		ob = super(Entity, cls).__new__(cls)
		
		Entity.__append_entity__(cls, ob)
		
		return ob

	@classmethod
	def __append_entity__(cls, sub_cls, ob):
		ob.is_destroyed = False
		
		Entity.entities_to_add[sub_cls].append(ob)
		Entity.new_created.add(sub_cls)

	@staticmethod
	def __add_new_entities__():
		''' Adds all recently created entities to their list.'''
		for t in Entity.new_created:
			Entity.entity_dict[t].extend(Entity.entities_to_add[t])
			Entity.entities_to_add[t].clear()

		Entity.new_created.clear()

	@staticmethod
	def __destroy_entities__():
		while Entity.entities_to_destroy:
			e = Entity.entities_to_destroy.pop()
			t = type(e)
			for d in (Entity.entity_dict, Entity.entities_to_add):
				if e in d[t]:
					d[t].remove(e)
					e.is_destroyed = True
					break

	@staticmethod
	def __call_function__(name:str, *param):
		'''Calls all related functions based on priority.'''
		for t, f in Entity.entity_callables[name]:
			for e in Entity.entity_dict[t]:
				f(e, *param)

	@staticmethod
	def __call_event_function__(event_type:int, event):
		'''Calls all related functions based on priority. \n\n If the function returns true than it considers the event used'''
		for t, f in Entity.entity_callables[f'event_{event_type}']:
			for e in Entity.entity_dict[t]:
				if f(e, event):
					return

	@final
	def destroy(self):
		'''Removes entity from the list and memory.'''
		if self not in Entity.entities_to_destroy:
			Entity.entities_to_destroy.append(self)
			self.on_destroy()

	def on_destroy(self):
		'''Called when the object is destroyed by calling `Entity.destroy()`.\n\nThis function is meant to be overloaded.'''
		pass

	@staticmethod
	def priority(value):
		'''Decorator to give a function a priority value.  The higher the number, the later it is called.'''
		def wrap(func):
			assert isinstance(func, Callable)
			func._priority = value
			return func
		return wrap
	
	@staticmethod
	def watch_event(*events):
		'''Decorator to note that the function should be called during the specified events.'''
		def wrap(func):
			assert isinstance(func, Callable)
			func._watched_events = events
			return func
		return wrap

	@staticmethod
	def all_of_parent_class(s_class:type[E]) -> list[E]:
		'''Returns all object that are the given class or a subclass of the given class.'''
		entities = []
		for t, l in Entity.entity_dict.items():
			if issubclass(t, s_class):
				entities.extend(l)
		# entities = [e for t, l in Entity.entity_dict.items() if issubclass(t, s_class) for e in l]
		# TODO test performance
		return entities