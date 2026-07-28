def red(text): return f"\033[31m{text}\033[0m"
def green(text): return f"\033[32m{text}\033[0m"
def yellow(text): return f"\033[33m{text}\033[0m"
def blue(text): return f"\033[34m{text}\033[0m"
def magenta(text): return f"\033[35m{text}\033[0m"
def cyan(text): return f"\033[36m{text}\033[0m"
def gray(text): return f"\033[37m{text}\033[0m"

def clear_empty_files(path):
    from pathlib import Path
    folder = Path(path)

    for file in folder.iterdir():
        if file.is_file() and file.stat().st_size == 0:
            file.unlink()
            print(yellow(f"deleted: {file}"))