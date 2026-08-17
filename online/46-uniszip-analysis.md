# Uniszip query analysis

get python script here: [uniszip.py](https://raw.githubusercontent.com/sparkuru/genshin/refs/heads/main/code/python/18-uniszip.py)

## Why renaming changes the result

The local rename does not change the archive bytes, so `fileSize` and `md5`
remain unchanged. However, the query request sends `fileName`, and the
`User-Client-Access` HMAC is also calculated from `fileName + fileSize`.
Therefore, changing the filename changes both the lookup value and the
request signature. The observed `404`/`200` difference shows that this service
does not behave as an MD5-only lookup; the renamed filename matches an existing
remote record.

The client cannot infer that remote filename from the local MD5. The script
now accepts a service filename without changing the local file:

```text
python uniszip.py query ./test.zip --file-name "archive-file-original-name.zip"
```

`fileSize` and `md5` still come from `./test.zip`, while `fileName` and the
HMAC use the value passed to `--file-name`.

## Required query data

The query requires the local archive path and the server record's original
`fileName`. The script computes `fileSize` and `md5` from the local archive;
they are not separate user inputs. Use `--file-name` when the local filename
differs from the server filename. If the original server filename is unknown,
the current endpoint cannot guarantee an MD5-only lookup.

When the response contains `pd`, the CLI prints the decrypted object and a
separate `[query] password = ...` line so the actual password is unambiguous.


# refer

1. source article: [一款可分享密码的解压缩 app 分析学习](https://bbs.kanxue.com/thread-291970.htm)；[微信公众号版](https://mp.weixin.qq.com/s/cp-XgQNy3S3ZfY65ImrPSA)