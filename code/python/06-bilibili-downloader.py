# -*- coding: utf-8 -*-

import json
import time
import os

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

basic_meta = {"id": "", "raw_url": "", "storage": ""}


def download_video(video_stream_list, mp4_storage_path, referer_source):
    import urllib.request

    for video in video_stream_list:
        opener = urllib.request.build_opener()
        opener.addheaders = [
            (
                "User-Agent",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0",
            ),
            ("Accept", "*/*"),
            ("Accept-Language", "en-US,en;q=0.5"),
            ("Accept-Encoding", "gzip, deflate, br"),
            ("Range", "bytes=0-"),  # Range 的值要为 bytes=0- 才能下载完整视频
            ("Referer", referer_source),
            ("Origin", "https://www.bilibili.com"),
            ("Connection", "keep-alive"),
        ]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url=video["url"], filename=mp4_storage_path)


def get_html_content(url: str, params=None, cookies=None, headers=headers) -> object:
    import requests

    response = requests.get(url, params=params, cookies=cookies, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        return None


def get_meta(basic_meta, cookies) -> dict:
    url = "https://api.bilibili.com/x/web-interface/view"
    params = {"bvid": basic_meta["id"]}
    cookies = {"SESSDATA": cookies}
    raw_bilibili_meta = get_html_content(url, params=params, cookies=cookies)
    if not raw_bilibili_meta:
        print("Error: failed to get html content")
        return {}
    raw_bilibili_meta = json.loads(raw_bilibili_meta)

    bilibili_meta = {}
    bilibili_meta.update(
        {
            "id": basic_meta["id"],
            "aid": raw_bilibili_meta["data"]["aid"],
            "cid": raw_bilibili_meta["data"]["cid"],
            "title": raw_bilibili_meta["data"]["title"],
            "raw_url": basic_meta["raw_url"],
            "desc": raw_bilibili_meta["data"]["desc"],
            "owner": raw_bilibili_meta["data"]["owner"]["name"],
            "time": {
                "work_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "upload_date": time.strftime(
                    "%Y-%m-%d %H:%M:%S",
                    time.localtime(int(raw_bilibili_meta["data"]["pubdate"])),
                ),
            },
            "storage": basic_meta["storage"],
            "stat": {
                "view": raw_bilibili_meta["data"]["stat"]["view"],
                "like": raw_bilibili_meta["data"]["stat"]["like"],
                "reply": raw_bilibili_meta["data"]["stat"]["reply"],
            },
        }
    )

    return bilibili_meta


def bypass_wbi(params, cookies):
    """
    传入需要请求的参数, 使用 wbi 算法对其进行签名
    ```python
    params={
        'foo': '114',
        'bar': '514',
        'baz': 1919810
    },
    ```
    """
    from functools import reduce
    from hashlib import md5
    import urllib.parse
    import time
    import requests

    mixinKeyEncTab = [
        46,
        47,
        18,
        2,
        53,
        8,
        23,
        32,
        15,
        50,
        10,
        31,
        58,
        3,
        45,
        35,
        27,
        43,
        5,
        49,
        33,
        9,
        42,
        19,
        29,
        28,
        14,
        39,
        12,
        38,
        41,
        13,
        37,
        48,
        7,
        16,
        24,
        55,
        40,
        61,
        26,
        17,
        0,
        1,
        60,
        51,
        30,
        4,
        22,
        25,
        54,
        21,
        56,
        59,
        6,
        63,
        57,
        62,
        11,
        36,
        20,
        34,
        44,
        52,
    ]

    def getMixinKey(orig: str):
        "对 imgKey 和 subKey 进行字符顺序打乱编码"
        return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, "")[:32]

    def encWbi(params: dict, img_key: str, sub_key: str):
        "为请求参数进行 wbi 签名"
        mixin_key = getMixinKey(img_key + sub_key)
        curr_time = round(time.time())
        params["wts"] = curr_time  # 添加 wts 字段
        params = dict(sorted(params.items()))  # 按照 key 重排参数
        # 过滤 value 中的 "!'()*" 字符
        params = {
            k: "".join(filter(lambda chr: chr not in "!'()*", str(v)))
            for k, v in params.items()
        }
        query = urllib.parse.urlencode(params)  # 序列化参数
        wbi_sign = md5((query + mixin_key).encode()).hexdigest()  # 计算 w_rid
        params["w_rid"] = wbi_sign
        return params

    def getWbiKeys():
        "获取最新的 img_key 和 sub_key"
        resp = requests.get(
            url="https://api.bilibili.com/x/web-interface/nav",
            headers=headers,
            cookies=cookies,
        )
        resp.raise_for_status()
        json_content = resp.json()
        img_url: str = json_content["data"]["wbi_img"]["img_url"]
        sub_url: str = json_content["data"]["wbi_img"]["sub_url"]
        img_key = img_url.rsplit("/", 1)[1].split(".")[0]
        sub_key = sub_url.rsplit("/", 1)[1].split(".")[0]
        return img_key, sub_key

    img_key, sub_key = getWbiKeys()

    signed_params = encWbi(params=params, img_key=img_key, sub_key=sub_key)

    return signed_params


def main(id, cookies, storage_dir):
    meta = {
        "id": id,
        "raw_url": f"https://www.bilibili.com/video/{id}",
        "storage": os.path.join(storage_dir, f"{id}.mp4"),
    }
    meta = get_meta(meta, cookies)

    base_url = "https://api.bilibili.com/x/player/wbi/playurl"
    referer_source = f"https://api.bilibili.com/x/web-interface/view?bvid={meta['id']}"

    cookies = {"SESSDATA": cookies}
    params = bypass_wbi({"bvid": meta["id"], "cid": meta["cid"], "qn": 64}, cookies)
    video_stream_info = get_html_content(base_url, params=params, cookies=cookies)
    video_stream_info_obj = json.loads(video_stream_info)
    video_stream_list = video_stream_info_obj["data"]["durl"]
    download_video(video_stream_list, meta["storage"], referer_source)


if __name__ == "__main__":
    bv = "BV15E421N7nL"
    # f12, cookies.SESSDATA
    cookies = ""
    storage_dir = "e:/tmp/"
    main(bv, cookies, storage_dir)
