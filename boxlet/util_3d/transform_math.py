import math

import numpy as np

# https://community.khronos.org/t/view-and-perspective-matrices/74154/2

def normalize_x0z(vec):
	vec[1] = 0
	return normalize(vec)

def magnitude(v): 
	return sum(v ** 2) ** 0.5

def square_magnitude(v): 
	return sum(v ** 2)

def normalize(v):
	m = magnitude(v)
	return v if m == 0 else v / m

def dot(a, b):
	return np.dot(a, b)

# dot2 and dot3 are usually faster, though only for single vector-pairs
def dot2(a, b):
	return a[0]*b[0] + a[1]*b[1]

def dot3(a, b):
	return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def project2(a, b):
	'2D Projects vector a onto vector b.'
	return b * (dot2(a, b) / dot2(b, b))

def project3(a, b):
	'3D Projects vector a onto vector b.'
	return b * (dot3(a, b) / dot3(b, b))

def clip_vector(v):
	'returns a vector with a max magnitude of 1'
	m = magnitude(v)
	return v if m <= 1 else v / m

def move_towards(a, b, amount):
	'''
	Moves from vector a to vector b by a given amount.
	
	Also returns a bool on if the target is reached.
	'''
	d = b - a
	m = magnitude(d)
	if m <= amount:
		return b, True
	return a + d * (amount / m), False

def translate(xyz):
	x, y, z = xyz
	return np.array([[1,0,0,0],
					[0,1,0,0],
					[0,0,1,0],
					[x,y,z,1]])

def scale(xyz):
	x, y, z = xyz
	return np.array([[x,0,0,0],
					[0,y,0,0],
					[0,0,z,0],
					[0,0,0,1]])

def rotate(a, xyz):
	x, y, z = normalize(xyz)
	a = math.radians(a)
	s = math.sin(a)
	c = math.cos(a)
	nc = 1 - c
	return np.array([[x*x*nc + c, x*y*nc - z*s, x*z*nc + y*s, 0],
					[y*x*nc + z*s, y*y*nc + c,   y*z*nc - x*s, 0],
					[x*z*nc - y*s, y*z*nc + x*s, z*z*nc + c,   0],
					[0, 0, 0, 1]])

def look_at(eye, target, up):
	f = normalize(target - eye)
	s = normalize(np.cross(f, normalize(up)))
	u = normalize(np.cross(s, f))
	m = np.identity(4)
	m[:3,:3] = np.vstack([-s,u,f])
	return np.matmul(m, translate(eye))

def look_at_forward(pos, forward, up):
	'like look_at(), but instead uses a forward vector and preserves the up vector'
	u = normalize(up)
	s = normalize(np.cross(up, normalize(forward)))
	f = normalize(np.cross(s, u))
	m = np.identity(4)
	m[:3,:3] = np.vstack([s,u,f])
	return np.matmul(m, translate(pos))

def fps_look(pos, x, y):
	matrix = rotate(x, np.array([0,1,0]))
	matrix = np.matmul(matrix, rotate(y, matrix[0,:3]))
	matrix[3,:3] = pos
	return matrix