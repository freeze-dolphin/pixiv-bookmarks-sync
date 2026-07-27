from pathlib import Path

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

print(f"Found {len(id_to_json)} JSON records.")

# ==========================
# 第二步：扫描图片目录
# ==========================

print("Scanning image files...")

image_names = {p.name for p in IMAGE_DIR.iterdir() if p.is_file()}

print(f"Found {len(image_names)} image files.")

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

print(f"Missing JSON records: {len(missing_json)}")

# ==========================
# 第四步：检查图片
# ==========================

print("Checking image files...")

missing_images = []

for json_file in tqdm(id_to_json.values(), unit="file"):

    with json_file.open("rb") as f:
        obj = orjson.loads(f.read())

    title = obj["title"]
    user = obj["user"]["name"]
    pid = obj["id"]
    page_count = obj["page_count"]

    prefix = f"{title}{user}{pid}"

    for page in range(page_count):

        target = f"{prefix}_p{page}."

        found = False

        for name in image_names:
            if name.startswith(target):
                found = True
                break

        if not found:
            missing_images.append(
                {
                    "id": pid,
                    "page": page,
                    "expected": f"{prefix}_p{page}.*",
                }
            )

print(f"Missing image files: {len(missing_images)}")

# ==========================
# 保存结果
# ==========================

with open("validator.txt", "w", encoding="utf-8") as f:
    f.write("## missing json\n\n")

    for i in sorted(missing_json):
        f.write(f"- {i}\n")

    f.write("---\n\n")

    f.write("## missing images\n\n")

    for x in missing_images:
        f.write(
            f"- id={x['id']} page={x['page']} expected={x['expected']}\n"
        )

missing_image_ids = sorted({x["id"] for x in missing_images})

print(f"\nIDs with missing images: {missing_image_ids}")