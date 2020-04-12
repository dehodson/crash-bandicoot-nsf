import binascii
import textwrap
import math

ENTRY_ENTITY = 7

ENTRY_TYPES = {
    0: 'Unknown',
    1: 'Unknown',
    2: 'Model Entry',
    3: 'Scenery Entry',
    4: 'Unknown',
    5: 'Texture Chunk',
    6: 'Unknown',
    7: 'Entity Entry',
    8: 'Not Used',
    9: 'Not Used',
    10: 'Not Used',
    11: 'Code Entry',
    12: 'Sound Entry',
    13: 'Music Entry',
    14: 'Wavebank Entry',
    15: 'Unknown',
    16: 'Unused',
    17: 'Unused',
    18: 'Unused',
    19: 'Demo Entry',
    20: 'Speech Entry',
    21: 'Unknown',
}

UNCOMPRESSED_CHUNK = b'3412'

CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_!";

def eid_string(eid):
    """Converts an integer EID to string"""
    result = ""

    if (eid & 0x80000000):
        # If the high bit is set, this EID is not legitimate and cannot be
        # converted to a 5-char string. Instead, we will prefix it with an
        # equal sign. This symbol will be used when converting back from
        # string to EID to indicate that the high bit is flipped.
        result += '=';

    result += CHARSET[(eid >> 25) & 0x3F];
    result += CHARSET[(eid >> 19) & 0x3F];
    result += CHARSET[(eid >> 13) & 0x3F];
    result += CHARSET[(eid >> 7) & 0x3F];
    result += CHARSET[(eid >> 1) & 0x3F];

    if (~eid & 1):
        # If the low bit is NOT set, this EID is not legitimate and cannot
        # be converted to a 5-char string. Instead, we will append an equal
        # sign to it. This symbol will be used when converting back from
        # string to EID to indicate that the low bit is flipped.
        result += '=';

    return result


class NsfFile:
    def __init__(self):
        self.chunks = []

    def add_chunk(self, chunk):
        self.chunks.append(chunk)

class Chunk:
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.process()

    def __repr__(self):
        string = 'Chunk #{}\n'.format(self.chunk_id)
        for e in self.entries:
            string += textwrap.indent(repr(e), '  ')
        return string

    def process(self):
        self.entries = []

        self.magic_number = self.raw_data[:2]

        #Uncompressed chunk begins with 3412
        if(binascii.hexlify(self.magic_number) == UNCOMPRESSED_CHUNK):
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
                self.entries.append(entry)

class Entry:
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.items = []
        self.process()

    def __repr__(self):
        string = 'Entry {} - {}\n'.format(self.entry_id_string, ENTRY_TYPES[self.entry_type])
        for i in self.items:
            string += textwrap.indent(repr(i), '  ')
        return string

    def process(self):
        self.magic_number = self.raw_data[:4]
        self.entry_id = int.from_bytes(self.raw_data[4:8], byteorder='little')
        self.entry_id_string = eid_string(self.entry_id)
        self.entry_type = int.from_bytes(self.raw_data[8:12], byteorder='little')
        self.item_count = int.from_bytes(self.raw_data[12:16], byteorder='little')

        if(self.entry_type == ENTRY_ENTITY):
            self.item_offsets = []

            for i in range(self.item_count):
                self.item_offsets.append(int.from_bytes(self.raw_data[16+(i*4):20+(i*4)], byteorder='little', signed=False))

            self.items = []
            for (i, v) in enumerate(self.item_offsets[:-1]):
                if i < 2:
                    continue # The format of the first two items is unknown. Not an entity
                item_length = int.from_bytes(self.raw_data[v:v+4], byteorder='little', signed=True)
                item = Item(self.raw_data[v:self.item_offsets[i+1]])
                items_match = self.raw_data[v:self.item_offsets[i+1]] == item.serialize()
                if not items_match:
                    print('DEBUG: Non-matching item for entry:{}'.format(self.entry_id_string))
                    print('DEBUG:', binascii.hexlify(self.raw_data[v:self.item_offsets[i+1]]))
                    print('DEBUG:', binascii.hexlify(item.serialize()))
                    print('DEBUG:---------------------------------------------------------------------- ')
                self.items.append(item)


FIELD_TYPES = {
    0x2C: 'Name',
    0x4B: 'Position',
    0x9F: 'ID',
    0xA4: 'General Settings',
    0xA9: 'Type',
    0xAA: 'Subtype',
    0x103: 'SLST EID',
    0x109: 'Neighbor camera rails (untested)',
    0x118: 'Misc Settings 1',
    0x13B: 'Draw List A',
    0x13C: 'Draw List B',
    0x208: 'Load List A',
    0x209: 'Load List B',
    0x277: 'Misc Settings 2',
    0x287: 'Victim',
    0x288: 'Section ID',
    0x28B: 'Box count',
    0x30E: 'Scale',
    0x336: 'Time Trial crate type',
    0x337: 'Bonus box count',
}


class Field:
    def __init__(self, raw_field_info, raw_field_data):
        self.raw_field_info = raw_field_info
        self.raw_field_data = raw_field_data
        self.process()

    def __repr__(self):
        return "Field of type: {}\n".format(FIELD_TYPES.get(self.field_type, 'Unknown ({})'.format(self.field_type)))

    def process(self):
        self.field_type = int.from_bytes(self.raw_field_info[:2], byteorder='little')


class Item:
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.fields = []
        self.process()

    def __repr__(self):
        string = 'Item "{}" - size:{} id:{} type:{} sub_type:{}\n'.format(self.name_string, self.item_length, self.item_id, self.item_type, self.sub_type)
        for f in self.fields:
            string += textwrap.indent(repr(f), '  ')
        return string

    def process(self):
        self.item_length = int.from_bytes(self.raw_data[:4], byteorder='little', signed=True)
        self.unused = self.raw_data[4:12]
        self.field_count = int.from_bytes(self.raw_data[12:16], byteorder='little', signed=True)
        offset = 16

        for i in range(self.field_count):
            new_field = Field(self.raw_data[offset:offset+8], b'')
            self.fields.append(new_field)
            offset += 8

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
        self.victims = self.raw_data[offset+12:]

    def serialize(self):
        binary_string = b''
        binary_string += self.item_length.to_bytes(4, byteorder='little', signed=True)
        binary_string += self.unused
        binary_string += self.field_count.to_bytes(4, byteorder='little', signed=True)
        binary_string += self.field_data
        binary_string += self.name_length.to_bytes(4, byteorder='little')

        size = (math.ceil(self.name_length / 4)) * 4
        padding = (size - self.name_length) * b'\x00'

        binary_string += str.encode(self.name_string) + padding
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
        binary_string += self.victims

        return binary_string

def load(file_name):
    with open(file_name, 'rb') as f:
        nsf_file = NsfFile()

        while True:
            data = f.read(65536)

            if not data:
                break

            chunk = Chunk(data)
            nsf_file.add_chunk(chunk)

        return nsf_file
