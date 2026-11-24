import base64, glob, os, re, sys

SRC, IMGDIR, OUT_PAGE, OUT_STANDALONE = sys.argv[1:5]
html = open(SRC, encoding="utf-8").read()

for path in glob.glob(os.path.join(IMGDIR, "*.jpg")):
    name = os.path.basename(path)[:-4]
    token = f"__IMG_{name}__"
    if token in html:
        data = base64.b64encode(open(path, "rb").read()).decode()
        html = html.replace(token, f"data:image/jpeg;base64,{data}")
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
