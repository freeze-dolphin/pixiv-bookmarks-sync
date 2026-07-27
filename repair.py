import json, re, os
import time

from tqdm import tqdm

from config import refresh_token

from main import download, login, api

# Hard-code the list of illust ids you want to repair (fill this before running).
# IDS_TO_REPAIR = []
from validator_result import IDS_TO_REPAIR


def main():
    if not os.path.exists('download'):
        os.makedirs('download')
    if not os.path.exists('download/imgs'):
        os.makedirs('download/imgs')
    if not os.path.exists('download/info'):
        os.makedirs('download/info')

    if not login(refresh_token):
        return

    bar = tqdm(IDS_TO_REPAIR)
    for illust_id in bar:
        try:
            resp = api.illust_detail(illust_id=illust_id)
            illust = resp.get('illust') if isinstance(resp, dict) else None
            if not illust:
                print('cannot fetch illust', illust_id, '- response:', resp)
                continue
        except Exception as e:
            print('api error for', illust_id, ':', e)
            continue

        try:
            download(illust, True)
            bar.write(f"{illust["title"]} {illust["id"]}")
        except Exception as e:
            print('download failed for', illust_id, ':', e)
        # small pause to be polite to the API
        time.sleep(0.5)


if __name__ == '__main__':
    main()
