
def lerp(a, b, t):
	'Interpolate between two values.'
	return a + (b - a) * t

def smoothlerp(a, b, t):
	'Smoothly interpolate between two values.'
	return a + (b - a) * t * t * (3 - 2 * t)

def invlerp(a, b, c):
	return (c - a) / (b - a)

def clamp(value, low, high):
	return min(max(value, low), high)
