import base64, glob, io, os, re, sys

try:  # WebP pictures are about half the size of JPEG; falls back to JPEG if Pillow is missing
    from PIL import Image
except ImportError:
    Image = None


def encode(path):
    raw = open(path, "rb").read()
    if Image is None:
        return "image/jpeg", raw
    buf = io.BytesIO()
    Image.open(path).convert("RGB").save(buf, "WEBP", quality=72, method=6)
    webp = buf.getvalue()
    return ("image/webp", webp) if len(webp) < len(raw) else ("image/jpeg", raw)

SRC, IMGDIR, OUT_PAGE, OUT_STANDALONE = sys.argv[1:5]
html = open(SRC, encoding="utf-8").read()

for path in glob.glob(os.path.join(IMGDIR, "*.jpg")):
    name = os.path.basename(path)[:-4]
    token = f"__IMG_{name}__"
    if token in html:
        mime, raw = encode(path)
        html = html.replace(token, f"data:{mime};base64,{base64.b64encode(raw).decode()}")
left = re.findall(r"__IMG_[a-z0-9_]+__", html)
assert not left, left

open(OUT_PAGE, "w", encoding="utf-8").write(html)

head = (
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
    '<style>html{padding-top:env(safe-area-inset-top,0px)}'
    '@supports (height:100dvh){html,body{height:100dvh}}</style>\n</head>\n<body>\n'
)
open(OUT_STANDALONE, "w", encoding="utf-8").write(head + html + "\n</body>\n</html>\n")
print("page KB:", len(html.encode()) // 1024)
