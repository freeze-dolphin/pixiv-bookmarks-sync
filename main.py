import json, re, os
import time

import sys
from pixivpy3 import AppPixivAPI
from tqdm import tqdm

from config import *
from utils import *

api = AppPixivAPI()

data_bookmarks_local = {"id": [], "last_pagination": 0}
if os.path.isfile('bookmarks.json'):
    with open("bookmarks.json", 'r') as f:
        data_bookmarks_local = json.loads(f.read())


def login(refresh_token):
    try:
        api.auth(refresh_token=refresh_token)
        print(gray('api: login successfully'))
    except:
        print(red('api: login error'))
        return 0
    else:
        return 1


def download(i, silent=False):
    should_delay = False
    message = None

    artname = re.sub(r'[\/\\:*?"<>|]', '', (i['title'] + i['user']['name']))
    if artname[0] == '.':
        artname = '_' + artname
    if i['page_count'] == 1:
        url = i['meta_single_page']['original_image_url']
        should_delay = should_delay or api.download(url, path='./download/imgs', name=artname + os.path.basename(url))
    else:
        for k in i['meta_pages']:
            url = k['image_urls']['original']
            should_delay = should_delay or api.download(url, path='./download/imgs',
                                                        name=artname + os.path.basename(url))
    with open(os.path.join('./download/info/', artname + str(i['id']) + '.json'), 'w') as f:
        f.write(json.dumps(i))

    if not should_delay:
        message = gray(f'download: passed {i["id"]} / {i["user"]["name"]} - {i['title']}')
    else:
        message = f'download: {i["id"]} / {i["user"]["name"]} - {i['title']}'

    if not silent:
        print(message)
        return should_delay
    else:
        return should_delay, message


def fetchBookmarks(max_pagination=data_bookmarks_local["last_pagination"]):
    def extractMaxBookmarkId(_resp):
        return int(_resp['next_url'].split('max_bookmark_id=')[1])

    pagination = [None]
    data_illusts = []
    while True:
        resp = api.user_bookmarks_illust(userid, max_bookmark_id=pagination[-1])
        if "error" in resp:
            print(resp["error"])
            sys.exit(1)

        resp_illusts = resp['illusts']

        # handle illusts in current page
        if len(resp_illusts) > 0:
            data_illusts.extend(resp_illusts)
        else:
            print(yellow(f"pagination: {pagination[-1]} has no illusts"))
            sys.exit(2)

        print(f"pagination: {pagination[-1]} with {len(resp_illusts)} illusts")

        # move to next page
        next_page = None if resp["next_url"] is None \
            else extractMaxBookmarkId(resp)

        if next_page is None or next_page < max_pagination:
            print(green("pagination: done"))
            break

        pagination.append(next_page)

        time.sleep(delay_pagination)

    new_illusts = []
    for i in data_illusts:
        if i["id"] not in data_bookmarks_local["id"]:
            new_illusts.append(i)

    # download new illusts
    bar_download = tqdm(new_illusts)
    for i in bar_download:
        should_delay, msg = download(i, silent=True)
        bar_download.write(msg)
        if should_delay:
            time.sleep(delay_download)

    with open("bookmarks.json", 'w') as f:
        data_bookmarks_local["last_pagination"] = pagination[1]
        print(green(f"pagination: recorded {len(new_illusts)} new illusts"))
        f.write(json.dumps(data_bookmarks_local))


def main():
    if not os.path.exists('download'):
        os.makedirs('download')
    if not os.path.exists('download/imgs'):
        os.makedirs('download/imgs')
    if not os.path.exists('download/info'):
        os.makedirs('download/info')

    clear_empty_files("download/imgs")
    clear_empty_files("download/info")

    if login(refresh_token) == 1:
        fetchBookmarks(38078895879)


if __name__ == '__main__':
    main()
