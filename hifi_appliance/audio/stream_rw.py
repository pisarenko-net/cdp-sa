import io


class StreamRW(io.BufferedRandom):
    def __init__(self, raw):
        super().__init__(raw)
        self.seek(0)

    def read(self, size=1):
        super().seek(self.read_offset)
        data = super().read(size)
        self.read_offset = self.tell()
        return data

    def write(self, data):
        super().seek(self.write_offset)
        written = super().write(data)
        self.write_offset = self.tell()
        return written

    def seek(self, offset):
        super().seek(offset)
        self.read_offset = self.write_offset = self.tell()

    def size(self):
        return self.raw.getbuffer().nbytes
