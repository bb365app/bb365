import json,sys
page=open(sys.argv[1] if len(sys.argv)>1 else "/tmp/bb365_page.html",encoding="utf-8").read()
head='''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Bodybuilding news, results, events and predictions for Kuwait and the Gulf.">
<meta name="theme-color" content="#09090A">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="BB365">
<script>window.BB_HOSTED=true</script>
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<style>html{padding-top:env(safe-area-inset-top,0px);background:#09090A}@supports (height:100dvh){html,body{height:100dvh}}</style>
</head>
<body>
'''
open(sys.argv[2] if len(sys.argv)>2 else "index.html","w",encoding="utf-8").write(head+page+"\n</body>\n</html>\n")
print("index.html KB",len(page.encode())//1024)
