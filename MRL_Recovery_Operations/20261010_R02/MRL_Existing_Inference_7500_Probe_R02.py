import pathlib,json,hashlib,http.client,datetime,time,subprocess,ast,os,socket,ctypes
o={"origin_signature":"MrLiouWord","schema":"MRL_Existing_Inference_7500_Synthetic_Probe_R02","scope":"ONE_BOUNDED_LOCAL_SYNTHETIC_COMPLETION","started_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"process_starts":0,"process_stops":0}
source=pathlib.Path(r"D:\mrl\inference\MRL_Inference_API.worldrecall_v4.py")
receipt=pathlib.Path(r"D:\MRL_Mother\Recovery\_operations\LocalAI_20261010_R02_be2f1d63\inference_7500_synthetic_completion_20261010_R02.json")
expected="36a4a79997663cd0998e065afc8504d7c655627ee6dab3b1a7aab8f7fa8b6d24"
def owners():
 r=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command","@(Get-NetTCPConnection -LocalPort 7500 -State Listen | Select-Object -ExpandProperty OwningProcess -Unique) | ConvertTo-Json -Compress"],capture_output=True,timeout=12)
 x=json.loads(r.stdout.decode("utf-8-sig"));return x if isinstance(x,list) else [x]
def require(condition):
 if not condition: raise RuntimeError("PROBE_SAFETY_GATE_FAILED")
try:
 require(not receipt.exists())
 require(os.name=="nt" and socket.gethostname().upper()=="WIN-PBVUI7VK2A6")
 k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetDriveTypeW.argtypes=[ctypes.c_wchar_p];k.GetDriveTypeW.restype=ctypes.c_uint
 require(k.GetDriveTypeW("D:\\")==3)
 require(all(not q.is_symlink() and not q.is_junction() for q in (source,*source.parents)))
 data=source.read_bytes();require(hashlib.sha256(data).hexdigest()==expected)
 tree=ast.parse(data)
 bindings=[n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="MRL_API_KEY_HASH" for t in n.targets)]
 require(len(bindings)==1)
 n=bindings[0]
 require(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="hexdigest" and not n.args and not n.keywords)
 h=n.func.value
 require(isinstance(h,ast.Call) and isinstance(h.func,ast.Attribute) and isinstance(h.func.value,ast.Name) and h.func.value.id=="hashlib" and h.func.attr=="sha256" and len(h.args)==1 and not h.keywords)
 literal=h.args[0];require(isinstance(literal,ast.Constant) and isinstance(literal.value,bytes) and 1<=len(literal.value)<=4096)
 key=literal.value.decode("ascii");require(all(32<ord(c)<127 for c in key))
 o["credential_source"]="EXISTING_AUTH_CONSTANT_IN_PINNED_D_SOURCE"
 o["credential_value_exported"]=False
 before=owners();require(before==[20580])
 payload={"prompt":"What is 2 + 2? Reply with only the digit 4.","max_tokens":8,"temperature":0.0,"persist":False,"user_id":"MRL_RECOVERY_SYNTHETIC_20261010_R02"}
 c=http.client.HTTPConnection("127.0.0.1",7500,timeout=28);start=time.monotonic()
 try:
  c.request("POST","/MRL_complete",body=json.dumps(payload),headers={"Content-Type":"application/json","User-Agent":"MRL-Recovery-Validator/1.0","x-api-key":key})
  r=c.getresponse();b=r.read(65537);o.update(http_status=r.status,response_bytes=len(b),response_sha256=hashlib.sha256(b).hexdigest(),elapsed_seconds=round(time.monotonic()-start,3),requested_max_tokens=8,persist_requested=False)
  if len(b)<=65536:
   x=json.loads(b);o["response_json_type"]=type(x).__name__
   if isinstance(x,dict):
    y=x.get("response");o["response_top_level_keys"]=sorted(x)[:30];o["completion_present"]=isinstance(y,str) and len(y.strip())>0
    o["completion_chars"]=len(y) if isinstance(y,str) else None
    o["completion_sha256"]=hashlib.sha256(y.encode("utf-8")).hexdigest() if isinstance(y,str) else None
    o["expected_answer_exact"]=isinstance(y,str) and y.strip().strip(".!").strip()=="4"
    o["api_ok"]=x.get("ok") is True
  o["status"]="INFERENCE_RESPONSE_OBSERVED" if o.get("http_status")==200 and o.get("completion_present") else "INFERENCE_RESPONSE_NOT_VERIFIED"
 finally:c.close()
except Exception as e:o["status"]="PROBE_FAILED";o["error_type"]=type(e).__name__
try:
 o["source_preserved"]=hashlib.sha256(source.read_bytes()).hexdigest()==expected
 o["owner_after"]=owners();o["inference_owner_preserved"]=o["owner_after"]==[20580]
 o["finished_at_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
 b=(json.dumps(o,sort_keys=True,indent=2)+"\n").encode("utf-8")
 with receipt.open("xb") as f:f.write(b);f.flush();__import__("os").fsync(f.fileno())
 o["receipt"]={"path":str(receipt),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
except Exception as e:o["receipt_status"]="UNVERIFIED";o["receipt_error_type"]=type(e).__name__
print(json.dumps(o))