import json, re, os
import time

from pixivpy3 import AppPixivAPI
from config import refresh_token, userid

api = AppPixivAPI()


def login(refresh_token):
    try:
        api.auth(refresh_token=refresh_token)
        print('login successfully')
    except:
        print('login error!')
        return 0
    else:
        return 1


def getMaxBookmarkIdFromResponse(json_result):
    return int(json_result['next_url'].split('max_bookmark_id=')[1])


def fetchAllBookmarks():
    json_result = api.user_bookmarks_illust(userid)
    result = [json_result['illusts']]
    last_max_bookmark_id = getMaxBookmarkIdFromResponse(json_result)
    while 1:
        try:
            max_bookmark_id = getMaxBookmarkIdFromResponse(json_result)
            print(max_bookmark_id)
            json_result = api.user_bookmarks_illust(userid, max_bookmark_id=max_bookmark_id)
            tmp_result = []
            for i in json_result['illusts']:
                tmp_result.append(i)
            result.append([x for x in tmp_result])
            time.sleep(0.1)
        except:
            break
    result = [j for i in result for j in i]
    return (result, last_max_bookmark_id)


def fetchBookmarksUntil(lastMaxBookmarkId):
    json_result = api.user_bookmarks_illust(userid, max_bookmark_id=lastMaxBookmarkId)

    result = [json_result['illusts']]
    last_max_bookmark_id = getMaxBookmarkIdFromResponse(json_result)
    max_bookmark_id = last_max_bookmark_id
    while max_bookmark_id > lastMaxBookmarkId and len(result[0]) > 0:
        try:
            max_bookmark_id = getMaxBookmarkIdFromResponse(json_result)
            print(max_bookmark_id)
            json_result = api.user_bookmarks_illust(userid, max_bookmark_id=max_bookmark_id)
            tmp_result = []
            for i in json_result['illusts']:
                tmp_result.append(i)
            result.append([x for x in tmp_result])
            time.sleep(0.1)
        except:
            break
    result = [j for i in result for j in i]
    return (result, last_max_bookmark_id)


def saveAllBookmarks():
    result, last_max_bookmark_id = fetchAllBookmarks()
    final_result = []
    for i in result:
        final_result.append(i["id"])
    with open('result.json', 'w') as f:
        f.write(json.dumps({'id': final_result,
                            "last_max_bookmark_id": last_max_bookmark_id}))


def appendDown():
    with open('result.json', 'r') as f:
        result = json.loads(f.read())

    bm, last = fetchBookmarksUntil(result["last_max_bookmark_id"])

    for i in bm:
        if i['id'] not in result["id"]:
            try:
                download(i)
                time.sleep(1.5)
            except:
                print('error ' + str(i['id']))
            else:
                result["id"].append(i)
                # pass

    with open('result.json', 'w') as f:
        f.write(json.dumps({'id': result["id"],
                            "last_max_bookmark_id": last}))


def download(i, silent=False):
    # download result
    artname = re.sub(r'[\/\\:*?"<>|]', '', (i['title'] + i['user']['name']))
    if artname[0] == '.':
        artname = '_' + artname
    if i['page_count'] == 1:
        url = i['meta_single_page']['original_image_url']
        api.download(url, path='./download/imgs', name=artname + os.path.basename(url))
    else:
        for k in i['meta_pages']:
            url = k['image_urls']['original']
            api.download(url, path='./download/imgs', name=artname + os.path.basename(url))
    with open(os.path.join('./download/info/', artname + str(i['id']) + '.json'), 'w') as f:
        f.write(json.dumps(i))
    if not silent:
        print('done: ' + i['title'])


def main():
    if not os.path.exists('download'):
        os.makedirs('download')
    if not os.path.exists('download/imgs'):
        os.makedirs('download/imgs')
    if not os.path.exists('download/info'):
        os.makedirs('download/info')
    if login(refresh_token) == 1:

        if not os.path.exists('./result.json'):
            saveAllBookmarks()

        # appendDown()


if __name__ == '__main__':
    main()
