import re
from pathlib import Path


# @formatter:off
def red(text): return f"\033[31m{text}\033[0m"
def green(text): return f"\033[32m{text}\033[0m"
def yellow(text): return f"\033[33m{text}\033[0m"
def blue(text): return f"\033[34m{text}\033[0m"
def magenta(text): return f"\033[35m{text}\033[0m"
def cyan(text): return f"\033[36m{text}\033[0m"
def gray(text): return f"\033[37m{text}\033[0m"
def darkgray(text): return f"\033[90m{text}\033[0m"
# @formatter:on


def sanitize(_name):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', _name).rstrip('. ').lstrip(".")


def generate_filename(_pid, _url=None, _ext=None):
    if _url is None:
        if _ext is None:
            return str(_pid)
        return f"{_pid}{_ext}"
    else:
        paging = _url.rsplit('_', 1)[1]  # _p0.jpg
        if _ext is not None:
            paging = Path(paging).with_suffix(_ext)
    return f"{_pid}_{paging}"


def clear_empty_files(_path):
    folder = Path(_path)

    for file in folder.iterdir():
        if file.is_file() and file.stat().st_size == 0:
            file.unlink()
            print(yellow(f"deleted: {file}"))
