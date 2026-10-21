"""YouTube helper: python3 yt.py <channel> upload <video> <meta.json> [thumb.png] [captions_en.srt]
meta.json: {title, description, tags[], categoryId, defaultLanguage, privacyStatus, publishAt?}"""
import json, sys, os, urllib.request, urllib.parse
D='~/.channel-uploader'
def token(ch):
    # per-channel Google project (own daily quota) if set up, else the shared Trend Nazariya project
    if os.path.exists(f'{D}/token2_{ch}.json') and os.path.exists(f'{D}/client_{ch}.json'):
        c=json.load(open(f'{D}/client_{ch}.json'))['installed']; t=json.load(open(f'{D}/token2_{ch}.json'))
    else:
        c=json.load(open(f'{D}/client.json'))['installed']; t=json.load(open(f'{D}/token_{ch}.json'))
    data=urllib.parse.urlencode(dict(client_id=c['client_id'],client_secret=c['client_secret'],refresh_token=t['refresh_token'],grant_type='refresh_token')).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request(c['token_uri'],data=data)))['access_token']
def req(method,url,tok,body=None,ctype='application/json',headers=None):
    h={'Authorization':'Bearer '+tok,'Content-Type':ctype}; h.update(headers or {})
    r=urllib.request.Request(url,data=body,method=method,headers=h); return urllib.request.urlopen(r)
def upload(ch,video,meta,thumb=None,caps=None):
    tok=token(ch); m=json.load(open(meta))
    body={'snippet':{k:m[k] for k in ('title','description','tags','categoryId','defaultLanguage','defaultAudioLanguage') if k in m},
          'status':{'privacyStatus':m.get('privacyStatus','private'),'selfDeclaredMadeForKids':False,'containsSyntheticMedia':False}}
    if m.get('publishAt'): body['status']['publishAt']=m['publishAt']; body['status']['privacyStatus']='private'
    size=os.path.getsize(video)
    r=req('POST','https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',tok,json.dumps(body).encode(),
          headers={'X-Upload-Content-Type':'video/*','X-Upload-Content-Length':str(size)})
    loc=r.headers['Location']
    with open(video,'rb') as f: vid=json.load(req('PUT',loc,tok,f.read(),'video/*'))['id']
    print('video',vid)
    if thumb:
        req('POST',f'https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}',tok,open(thumb,'rb').read(),'image/png'); print('thumb ok')
    for lang,path in (caps or {}).items():
        import uuid; b='----'+uuid.uuid4().hex
        meta_c=json.dumps({'snippet':{'videoId':vid,'language':lang,'name':''}})
        payload=(f'--{b}\r\nContent-Type: application/json\r\n\r\n{meta_c}\r\n--{b}\r\nContent-Type: application/octet-stream\r\n\r\n').encode()+open(path,'rb').read()+f'\r\n--{b}--'.encode()
        req('POST','https://www.googleapis.com/upload/youtube/v3/captions?uploadType=multipart&part=snippet',tok,payload,f'multipart/related; boundary={b}'); print('captions',lang)
    return vid
if __name__=='__main__':
    ch,cmd=sys.argv[1],sys.argv[2]
    if cmd=='whoami':
        print(json.load(req('GET','https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true',token(ch)))['items'][0]['snippet']['title'])
