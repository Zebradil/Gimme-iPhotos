import os
import shutil


# The code is taken from https://stackoverflow.com/a/29967714/2227895
class Copy:
    # differs from shutil.COPY_BUFSIZE on platforms != Windows
    READINTO_BUFSIZE = 1024 * 1024

    @classmethod
    def fileobj(cls, fsrc, fdst, callback, length=0):
        try:
            # check for optimisation opportunity
            if "b" in fsrc.mode and "b" in fdst.mode and fsrc.readinto:
                return cls._fileobj_readinto(fsrc, fdst, callback, length)
        except AttributeError:
            # one or both file objects do not support a .mode or .readinto attribute
            pass

        if not length:
            length = shutil.COPY_BUFSIZE

        fsrc_read = fsrc.read
        fdst_write = fdst.write

        while True:
            buf = fsrc_read(length)
            if not buf:
                break
            fdst_write(buf)
            callback(len(buf))

    @classmethod
    def _fileobj_readinto(cls, fsrc, fdst, callback, length=0):
        """readinto()/memoryview() based variant of copyfileobj().
        *fsrc* must support readinto() method and both files must be
        open in binary mode.
        """
        fsrc_readinto = fsrc.readinto
        fdst_write = fdst.write

        if not length:
            try:
                file_size = os.stat(fsrc.fileno()).st_size
            except OSError:
                file_size = cls.READINTO_BUFSIZE
            length = min(file_size, cls.READINTO_BUFSIZE)

        with memoryview(bytearray(length)) as mv:
            while True:
                n = fsrc_readinto(mv)
                if not n:
                    break
                if n < length:
                    with mv[:n] as smv:
                        fdst.write(smv)
                else:
                    fdst_write(mv)
                callback(n)
