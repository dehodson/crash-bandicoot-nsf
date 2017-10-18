import binascii

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
		string = 'Chunk #{0}'.format(self.chunk_id)
		
		for e in self.entries:
			string += '\n    '+repr(e)

		return string

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
		string = 'Entry #{0}'.format(self.entry_id)
		return string

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

	def process(self):
		self.item_length = int.from_bytes(self.raw_data[:4], byteorder='little')
		self.field_count = int.from_bytes(self.raw_data[12:16], byteorder='little')

		offset = (8*self.field_count)+16
		self.field_data = self.raw_data[16:offset]
		self.name_length = int.from_bytes(self.raw_data[offset:offset+4], byteorder='little')
		self.name_string = ''.join(chr(s) for s in self.raw_data[offset+4:offset+self.name_length+4])

		offset += 4 + ((self.name_length // 4) + 1) * 4
		
def load(file_name):
	with open(file_name, 'rb') as f:
		nsf_file = NsfFile()

		while True:
			data = f.read(65536)

			if not data:
				break

			chunk = Chunk(data)
			chunk.process()

			print(chunk)

			nsf_file.add_chunk(chunk)

			# items = []
			# for j in itemOffsets:
			# 	itemLength = int.from_bytes(data[i+j:i+j+1], byteorder='little')
			# 	item = data[i+j:i+j+itemLength]
			# 	itemLength = item[0:4]
			# 	unused = item[4:12]
			# 	fieldLength = int.from_bytes(item[12:16], byteorder='little')
			# 	o = (8*fieldLength)+16
			# 	fields = item[16:o]
			# 	stringLen = int.from_bytes(item[o:o+4], byteorder='little')
			# 	string = item[o+4:o+(stringLen)+4]
			# 	a = ""
			# 	for s in string:
			# 		a += chr(s)
			# 	print(a)
			# 	o += stringLen+4
			# 	posLen = int.from_bytes(item[o:o+4], byteorder='little')
			# 	if posLen == 1:
			# 		o += 20
			# 		settingLen = int.from_bytes(item[o:o+4], byteorder='little') + 2
			# 		o += (4 * settingLen)
			# 		itemType = int.from_bytes(item[o:o+4], byteorder='little')
			# 		if itemType == 34:
			# 			print("Box found!")