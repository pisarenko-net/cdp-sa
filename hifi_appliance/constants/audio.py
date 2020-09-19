MEMORY_STREAM_GC_THRESHOLD = 200 * 1024 * 1024  # at most accrued until GC'ed
BUFFER_REFRESH_THRESHOLD = 8 * 1024 * 1024  # ask for more when <8MB left (~45sec)