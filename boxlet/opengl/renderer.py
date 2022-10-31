from OpenGL.GL import *


# it's HIGHLY recommended to put uniform data into numpy arrays for decent performance boosts

class Renderer:
			
	def destroy(self):
		pass

	def render(self):
		pass

	def rebuild(self, rebind = True):
		pass


# I think the real performance booster is an instance renderer which sends an array of matricies and other data all at once
# https://learnopengl.com/Advanced-OpenGL/Instancing




if __name__ == '__main__':

	# a future idea for a full renderer that manages inputs based on the shader is to compile a function instead of using if statements
	# this will allow the removal of if statments or any other checks that would always be False or True

	# probably limit to a few things, like expecting a single normal model
	# though there can be multiple buildable renderers, like for particles

	# !!! WARNING, be very careful of what is allowed to be input, as they could contain malicious code. !!!
		# example: 
			# test = '1\n\texit()'
			# exec('def func():\n\ta = 1 + ' + test + '\n\treturn a)

		# would result in:

			# def func():
			#	a = 1 + 1
			#	exit()
			# 	return a
		
		# causing the function to call exit(), though this is a very simple and mostly harmless case
		# probably restrict custom input to strings without whitespace

	# though it's a bit silly to optimize this sort of thing in python
	# there is some potential in building a function in a different language or library, like c++ or cython

	def create_function(param_count, *details):
		HELLO = 'print hello' in details
		WORLD = 'print world' in details
		FIRST = 'extra first' in details

		# append directly to string
		# func = 'def funcy():' if param_count == 0 else 'def funcy(extra):'
		# if FIRST and param_count == 1: func += '\tprint(extra)\n'
		# if HELLO: func += '\tprint("hello")\n'
		# if WORLD: func += '\tprint("world")\n'
		# if not FIRST and param_count == 1: func += '\tprint(extra)\n'

		# append to array, then join with '\n'
		func = []
		func.append('def funcy():' if param_count == 0 else 'def funcy(extra):')
		if FIRST and param_count == 1: func.append('\tprint(extra)')
		if HELLO: func.append('\tprint("hello")')
		if WORLD: func.append('\tprint("world")')
		if not FIRST and param_count == 1: func.append('\tprint(extra)')
		func = '\n'.join(func)

		# func += 'global asdf\nasdf = funcy'
		# compile(func, 'function creation', 'exec')
		# global asdf

		loc = {}
		exec(func, globals(), loc)
		asdf = loc['funcy']

		return asdf

	f1 = create_function(0, 'print hello', 'print world')
	f2 = create_function(0, 'print hello')
	f3 = create_function(1, 'print world', 'extra first')
	f4 = create_function(1, 'print hello', 'print world')

	def simple():
		print('hello')
		print('world')
	def simple2():
		print('hello')

	from dis import dis

	for f in [simple, f1, simple2, f2]: # each pair results in the exact same code, even though they were compiled during different steps
		print('-------------')
		f()
		print('- - - - - - -')
		dis(f)
		print('-------------')
	for f in [f3, f4]:
		print('-------------')
		f('asdf')
		print('- - - - - - -')
		dis(f)
		print('-------------')

