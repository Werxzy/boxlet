# import urllib.request as req
# url = 'https://raw.githubusercontent.com/KhronosGroup/SPIRV-Headers/master/include/spirv/unified1/spirv.py'
# src = req.urlopen(url).read().decode('utf-8')

from spirv import spv
import spirv_expanded as se

reverse_spv = {
	fk:{
		v:k for k, v in fv.items()
		} 
	for fk, fv in spv.items() 
	if isinstance(fv, dict)
	}

from pathlib import Path

def get_path(file:str):
	return Path(__file__).parent / f'{file}'

def open_shader(filename):
	with open(get_path(filename), 'rb') as file:
		return file.read()

bytes = open_shader('frag.spv')
_gen = (b for b in bytes)
def next_byte():
	return next(_gen)

def next_word():
	try:
		return sum(next_byte() << (i*8) for i in range(4))
	except:
		raise StopIteration()

def process_words(word_count, opcode, words):
	if opcode not in se.opcode_layouts or not isinstance(se.opcode_layouts[opcode], tuple):
		return words

	word_count -= 1
	new_data = {}
	current_word = 0
	current_layout = 0
	layout = se.opcode_layouts[opcode]

	def next_word():
		nonlocal current_word
		w = words[current_word]
		current_word += 1
		return w

	while current_word < word_count:
		match layout[current_layout]:
			case se.RESULT_TYPE:
				new_data['result type'] = next_word()

			case se.RESULT_ID:
				new_data['result id'] = next_word()

			case se.OPERAND_ID | se.LITERAL_NUMBER:
				new_data[current_layout] = next_word()

			case se.OPERAND_ID_EXHAUSTIVE | se.LITERAL_NUMBER_EXHAUSTIVE:
				while current_word < word_count:
					new_data[current_layout] = next_word()

			case se.LITERAL_STRING:
				string = ''
				reading = True

				while reading:
					w = next_word()

					for _ in range(4):
						if not(reading := w): 
							break
						string += chr(w & 0xff)
						w >>= 8

				new_data[current_layout] = string

			case _:
				if isinstance(layout[current_layout], str):
					new_data[current_layout] = reverse_spv[layout[current_layout]][next_word()]

		current_layout += 1

	return new_data



magic_number = next_word()
print(hex(magic_number))

if magic_number != 0x07230203:
	raise Exception('different endianness or incorrect magic number found')

version_number = next_word()
gen_magic_number = next_word()
bound = next_word()
reserved_0 = next_word()

print(bound)
i = 0
while True:
	try:
		w = next_word()
		word_count = w >> spv['WordCountShift']
		opcode = w & spv['OpCodeMask']

		words = [next_word() for _ in range(word_count - 1)]

		opcode_str = reverse_spv['Op'][opcode]
		print('count:', word_count, 'opcode:', opcode, opcode_str)
		print('words:', process_words(word_count, opcode_str, words))
		print('- - - - -')
		i += 1

	except StopIteration:
		print('done')
		break





