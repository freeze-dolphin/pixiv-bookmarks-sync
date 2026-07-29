import json, os
import subprocess
import time
import sys
import zipfile
from tempfile import NamedTemporaryFile

from PIL.ImageFile import ImageFile
from tqdm import tqdm
from PIL import Image

from pixivpy3 import AppPixivAPI

from config import *
from utils import *

api = AppPixivAPI()

data_bookmarks_local = {"id": [], "invisible": [], "last_pagination": 0}
if os.path.isfile('bookmarks.json'):
    with open("bookmarks.json", 'r') as _:
        data_bookmarks_local = json.loads(_.read())


def login(_refresh_token):
    # noinspection PyBroadException
    try:
        api.auth(refresh_token=_refresh_token)
        print(gray('api: login successfully'))
    except:
        print(red('api: login error'))
        return 0
    else:
        return 1


def download_illust(i, bar=None):
    def show_message(_m):
        if bar:
            bar.write(_m)
        else:
            print(_m)

    if not i["visible"]:
        show_message(yellow(f"download: {i['id']} invisible"))

    pid = i["id"]

    def perform_download():
        dst = generate_filename(pid, url)
        passed = not api.download(url, path='./download/imgs', name=dst)
        if passed:
            show_message(darkgray(f'download: {dst} / {i["user"]["name"]} - {i['title']} (passed)'))
        else:
            show_message(f'download: {dst} / {i["user"]["name"]} - {i['title']}')
            time.sleep(delay_download)

    if i['page_count'] == 1:
        url = i['meta_single_page']['original_image_url']
        perform_download()
    else:
        for k in i['meta_pages']:
            url = k['image_urls']['original']
            perform_download()


def download_ugoira(i, bar=None):
    def show_message(_m):
        if bar:
            bar.write(_m)
        else:
            print(_m)

    if not i["visible"]:
        show_message(yellow(f"download: {i['id']} invisible"))

    pid = i["id"]
    um = i["ugoira_metadata"]

    zip_url = um["zip_urls"]["medium"].replace("_ugoira600x600.zip", "_ugoira1920x1080.zip")
    gif_filename = generate_filename(pid, zip_url, _ext=".gif")
    gif_dst = os.path.join("./download/imgs", gif_filename)

    if os.path.exists(gif_dst):
        show_message(darkgray(f'download: {gif_filename} / {i["user"]["name"]} - {i['title']} (passed)'))
    else:
        with NamedTemporaryFile(suffix=".zip") as zip_dst_file:
            api.download(zip_url, path='./download/imgs', fname=zip_dst_file)

            frames: list[ImageFile] = []
            durations = []
            with zipfile.ZipFile(zip_dst_file) as z:
                for frame in um["frames"]:
                    frame_filename = frame["file"]
                    with z.open(frame_filename) as ff:
                        img = Image.open(ff).convert("RGBA")
                        frames.append(img.copy())
                    durations.append(frame["delay"])

            frames[0].save(
                gif_dst,
                save_all=True,
                append_images=frames[1:],
                durations=durations,
                loop=0,
                disposal=2
            )

        show_message(f'download: {gif_filename} / {i["user"]["name"]} - {i['title']}')
        time.sleep(delay_download)


def record(i, dst, pid=None, replace=False):
    if pid is None:
        pid = i["id"]

    if os.path.exists(dst) and not replace:
        return False

    with open(dst, 'w') as _:
        _.write(json.dumps(i))

    return True


def sync_bookmarks(max_pagination=None, source=None, should_dump=False):
    if max_pagination is None:
        max_pagination = data_bookmarks_local["last_pagination"]

    def extract_max_bookmark_id(_resp):
        return int(_resp['next_url'].split('max_bookmark_id=')[1])

    if source is not None:
        pagination = source["pagination"]
        illusts = source["illusts"]
        max_pagination = 0
    else:
        pagination = [None]
        illusts = []
        while True:
            resp = api.user_bookmarks_illust(userid, max_bookmark_id=pagination[-1])
            if "error" in resp:
                print(resp["error"])
                sys.exit(1)

            resp_illusts = resp['illusts']

            for idx in range(len(resp_illusts)):
                i = resp_illusts[idx]
                if i["type"] == "ugoira":
                    if not i["visible"]:
                        i["ugoira_metadata"] = None
                    else:
                        pid = i["id"]
                        print(gray(f"pagination: request metadata for ugoira {pid}"))
                        time.sleep(delay_ugoira_metadata)
                        um = api.ugoira_metadata(pid)
                        i["ugoira_metadata"] = um["ugoira_metadata"]

            # handle illusts in current page
            if len(resp_illusts) > 0:
                illusts.extend(resp_illusts)
            else:
                print(yellow(f"pagination: {pagination[-1]} has no illusts"))
                sys.exit(2)

            print(f"pagination: {pagination[-1]} with {len(resp_illusts)} illusts")

            # move to next page
            next_page = None if resp["next_url"] is None \
                else extract_max_bookmark_id(resp)

            if next_page is None or next_page < max_pagination:
                print(green("pagination: done"))
                break

            pagination.append(next_page)
            time.sleep(delay_pagination)

        if should_dump:
            with open("pagination_data.json", 'w') as _:
                _.write(json.dumps({
                    "pagination": pagination,
                    "illusts": illusts
                }))

    return pagination, illusts


def fetch_bookmarks(pagination, illusts):
    new_illusts = []
    new_ugoiras = []

    bar_record = tqdm(illusts[::-1])
    for i in bar_record:
        pid = i["id"]

        dst = generate_filename(pid, _ext=".json")
        full_dst = os.path.join('./download/info/', dst)

        if record(i, full_dst, pid):  # record bookmark data
            bar_record.write(f'record: {dst} / {i["user"]["name"]} - {i['title']}')

        if pid not in data_bookmarks_local["id"]:
            if i["visible"]:
                if i["type"] == "ugoira":
                    new_ugoiras.append(i)
                else:
                    new_illusts.append(i)
                data_bookmarks_local['id'].insert(0, pid)  # preserve the order (newest -> oldest)
            else:
                data_bookmarks_local['invisible'].insert(0, pid)
    print(green("record: done"))

    # download new illusts
    if len(new_illusts) > 0:
        bar_download = tqdm(new_illusts)
        for i in bar_download:
            download_illust(i, bar_download)
        print(green("download: illust done"))

    # download new ugoiras
    if len(new_ugoiras) > 0:
        bar_download = tqdm(new_ugoiras)
        for i in bar_download:
            download_ugoira(i, bar_download)
        print(green("download: ugoira done"))

    with open("bookmarks.json", 'w') as _:
        data_bookmarks_local["last_pagination"] = pagination[1]
        print(green(f"pagination: recorded {len(new_illusts)} new illusts"))
        _.write(json.dumps(data_bookmarks_local))


def ensure_directories():
    if not os.path.exists('download'):
        os.makedirs('download')
    if not os.path.exists('download/imgs'):
        os.makedirs('download/imgs')
    if not os.path.exists('download/info'):
        os.makedirs('download/info')


def clear_invalid_files():
    clear_empty_files("download/imgs")
    clear_empty_files("download/info")


def preparation():
    ensure_directories()
    clear_invalid_files()

    if login(refresh_token) != 1:
        sys.exit(-1)


if __name__ == '__main__':
    ensure_directories()
    clear_invalid_files()

    if login(refresh_token) == 1:
        # load_pagination_data("pagination_data.json")

        _pagination, _illusts = sync_bookmarks()
        fetch_bookmarks(_pagination, _illusts)

        if len(sys.argv) > 1:
            subprocess.run(sys.argv[1:])
