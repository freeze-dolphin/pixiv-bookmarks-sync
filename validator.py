import json
import re
from pathlib import Path

import log
import orjson
from tqdm import tqdm

# ==========================
# 配置
# ==========================

JSON_DIR = Path(r"download/info")
IMAGE_DIR = Path(r"download/imgs")
RESULT_JSON = Path(r"result.json")

# ==========================
# 第一步：扫描JSON目录
# ==========================

print("Scanning JSON files...")

id_to_json: dict[int, Path] = {}

for file in JSON_DIR.glob("*.json"):
    try:
        with file.open("rb") as f:
            obj = orjson.loads(f.read())

        id_to_json[obj["id"]] = file

    except Exception as e:
        print(f"Failed to parse {file}: {e}")

print(f"  Found {len(id_to_json)} JSON records.")

# ==========================
# 第二步：扫描图片目录
# ==========================

print("Scanning image files...")

image_names = {p.name for p in IMAGE_DIR.iterdir() if p.is_file()}

print(f"  Found {len(image_names)} image files.")

known_ids = set(map(str, id_to_json.keys()))

image_index: set[tuple[int, int]] = set()

page_pattern = re.compile(
    r"_(?:ugoira|p)(\d+)\.",
    re.IGNORECASE
)

id_pattern = re.compile(
    r"(\d+)(?:-[a-z0-9]+)?$",
    re.IGNORECASE
)

for name in tqdm(image_names):
    page_match = page_pattern.search(name)
    if not page_match:
        continue

    page = int(page_match.group(1))
    before_page = name[:page_match.start()]

    # 去掉文件名末尾可能存在的 -hash，比如 "...144887662-944d44dfe..." -> "...144887662"
    sanitized_before_page = re.sub(r"-[a-z0-9]+$", "", before_page, flags=re.IGNORECASE)

    # 从右往左寻找数字起点
    for kid in known_ids:
        if str(kid) in before_page:
            # 优先尝试不带hash的JSON文件名，其次回退到原始的 before_page
            sanitized_path = JSON_DIR / f"{sanitized_before_page}.json"
            original_path = JSON_DIR / f"{before_page}.json"

            if sanitized_path.exists():
                json_path = sanitized_path
            elif original_path.exists():
                json_path = original_path
            else:
                # 如果两个都不存在，跳过该文件（避免抛出 FileNotFoundError）
                # 也可以在此处记录日志以便日后检查
                # print(f"JSON not found for {before_page} (sanitized: {sanitized_before_page})")
                break

            with json_path.open("r", encoding="utf-8") as m:
                mj = json.load(m)
                image_index.add((int(mj["id"]), page))
            break

print(f"  Indexed {len(image_index)} image records.")

# ==========================
# 第三步：检查result.json
# ==========================

print("Checking result.json...")

with RESULT_JSON.open("rb") as f:
    result = orjson.loads(f.read())

missing_json: list[int] = []

for item in result:
    if item["id"] not in id_to_json:
        missing_json.append(item["id"])

if len(missing_json) > 0:
    print(log.red(f"  Missing JSON records: {len(missing_json)}"))
else:
    print(log.green(f"  Missing JSON records: {len(missing_json)}"))

# ==========================
# 第四步：检查图片
# ==========================

print("Checking image files...")

missing_images = []

# 预编译所有图片名，避免循环中重复处理
image_names = list(image_names)

for json_file in tqdm(id_to_json.values(), unit="file"):

    with json_file.open("rb") as f:
        obj = orjson.loads(f.read())

    pid = obj["id"]
    page_count = obj["page_count"]

    for page in range(page_count):
        if (pid, page) not in image_index:
            missing_images.append(
                {
                    "id": pid,
                    "page": page,
                }
            )

if len(missing_images) > 0:
    print(log.red(f"  Missing image files: {len(missing_images)}"))
else:
    print(log.green(f"  Missing image files: {len(missing_images)}"))

# ==========================
# 保存结果
# ==========================

with open("validator.md", "w", encoding="utf-8") as f:
    f.write("## missing json\n\n")

    for i in sorted(missing_json):
        f.write(f"- {i}\n")

    f.write("---\n\n")

    f.write("## missing images\n\n")

    f.write(f"|id|page|\n")
    f.write("|-|-|\n")

    for x in missing_images:
        f.write(
            f"|{x['id']}|{x['page']}|\n"
        )

with open("validator_result.py", "w", encoding="utf-8") as f:
    f.write(f"IDS_TO_REPAIR={sorted({x["id"] for x in missing_images})}\n")
