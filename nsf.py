import binascii
import math

class NsfFile:
	def __init__(self):
		self.chunks = []

	def add_chunk(self, chunk):
		self.chunks.append(chunk)

class Chunk:
	def __init__(self, raw_data):
		self.raw_data = raw_data
		self.entries = []

	def __repr__(self):
		return 'Chunk #{0}'.format(self.chunk_id)

	def process(self):
		self.magic_number = self.raw_data[:2]

		#Uncompressed chunk begins with 3412
		if(binascii.hexlify(self.magic_number) == b'3412'):
			self.chunk_type = int.from_bytes(self.raw_data[2:4], byteorder='little')
			self.chunk_id = int.from_bytes(self.raw_data[4:8], byteorder='little')
			self.entry_count = int.from_bytes(self.raw_data[8:12], byteorder='little')
			self.checksum = self.raw_data[12:16]
			self.entry_offsets = []
			for i in range(self.entry_count):
				self.entry_offsets.append(int.from_bytes(self.raw_data[16 + (i*4):20 + (i*4)], byteorder='little'))

			self.entry_offsets.append(65536)

			self.entries = []
			for i in range(1, len(self.entry_offsets)):
				entry = Entry(self.raw_data[self.entry_offsets[i-1]:self.entry_offsets[i]])
				entry.process()
				self.entries.append(entry)

class Entry:
	def __init__(self, raw_data):
		self.raw_data = raw_data

	def __repr__(self):
		return 'Entry #{0}'.format(self.entry_id)

	def process(self):
		self.magic_number = self.raw_data[:4]
		self.entry_id = int.from_bytes(self.raw_data[4:8], byteorder='little')
		self.entry_type = int.from_bytes(self.raw_data[8:12], byteorder='little')
		self.item_count = int.from_bytes(self.raw_data[12:16], byteorder='little')

		if(self.entry_type == 7):
			self.item_offsets = []

			for i in range(self.item_count):
				self.item_offsets.append(int.from_bytes(self.raw_data[16+(i*4):20+(i*4)], byteorder='little'))

			self.items = []
			for i in self.item_offsets:
				item_length = int.from_bytes(self.raw_data[i:i+4], byteorder='little')
				item = Item(self.raw_data[i:i+item_length])
				item.process()
				self.items.append(item)

class Item:
	def __init__(self, raw_data):
		self.raw_data = raw_data

	def __repr__(self):
		return 'Item "{0}" - id:{3} type:{1} sub_type:{2}'.format(self.name_string, self.item_type, self.sub_type, self.item_id)

	def process(self):
		self.item_length = int.from_bytes(self.raw_data[:4], byteorder='little')
		self.unused = self.raw_data[4:12]
		self.field_count = int.from_bytes(self.raw_data[12:16], byteorder='little')

		offset = (8*self.field_count)+16
		self.field_data = self.raw_data[16:offset]
		self.name_length = int.from_bytes(self.raw_data[offset:offset+4], byteorder='little')
		self.name_string = ''.join(chr(s) for s in self.raw_data[offset+4:offset+self.name_length+4])

		offset += 4 + (math.ceil(self.name_length / 4)) * 4
		self.position_length = int.from_bytes(self.raw_data[offset:offset+4], byteorder='little')

		pos_offset = offset + (((self.position_length * 6) // 4) + 1) * 4
		self.position_data = self.raw_data[offset+4:pos_offset+4]
		offset = pos_offset+8

		self.unused2 = self.raw_data[offset-4:offset]
		self.item_id = int.from_bytes(self.raw_data[offset:offset+4], byteorder='little')
		self.setting_length = int.from_bytes(self.raw_data[offset+4:offset+8], byteorder='little')
		self.setting_data = self.raw_data[offset+8:offset+(self.setting_length*4)+8]
		offset = offset+(self.setting_length*4)+12

		self.unused3 = self.raw_data[offset-4:offset]
		self.item_type = int.from_bytes(self.raw_data[offset:offset+4], byteorder='little')

		self.unused4 = self.raw_data[offset+4:offset+8]
		self.sub_type = int.from_bytes(self.raw_data[offset+8:offset+12], byteorder='little')

	def unprocess(self):
		binary_string = b''
		binary_string += self.item_length.to_bytes(4, byteorder='little')
		binary_string += self.unused
		binary_string += self.field_count.to_bytes(4, byteorder='little')
		binary_string += self.field_data
		binary_string += self.name_length.to_bytes(4, byteorder='little')
		binary_string += str.encode(self.name_string)
		binary_string += self.position_length.to_bytes(4, byteorder='little')
		binary_string += self.position_data
		binary_string += self.unused2
		binary_string += self.item_id.to_bytes(4, byteorder='little')
		binary_string += self.setting_length.to_bytes(4, byteorder='little')
		binary_string += self.setting_data
		binary_string += self.unused3
		binary_string += self.item_type.to_bytes(4, byteorder='little')
		binary_string += self.unused4
		binary_string += self.sub_type.to_bytes(4, byteorder='little')

		return binary_string
		
def load(file_name):
	with open(file_name, 'rb') as f:
		nsf_file = NsfFile()

		while True:
			data = f.read(65536)

			if not data:
				break

			chunk = Chunk(data)
			chunk.process()
			nsf_file.add_chunk(chunk)

		return nsf_file
