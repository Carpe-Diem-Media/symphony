import ast,base64,ctypes,hashlib,json,os,stat,subprocess,tarfile
from pathlib import Path
root=Path('/home/jcschoeman96/sdv02')
uid=os.getuid()
def need(ok,message):
    if not ok: raise RuntimeError(message)
def digest(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
s=root.lstat()
need(root.resolve()==root and s.st_uid==uid and stat.S_IMODE(s.st_mode)==0o700,'root identity')
e=root/'evidence'
inventory=json.loads((e/'inventory.json').read_text())
inventory_hash=digest(e/'inventory.json')
need((e/'inventory.sha256').read_text()==inventory_hash+'  inventory.json\n','inventory checksum')
recorded={r['path']:r for r in inventory}
actual={}
for base,dirs,files in os.walk(root,followlinks=False):
    for name in dirs+files:
        p=Path(base)/name;rel=str(p.relative_to(root));s=p.lstat()
        actual[rel]=p
        if rel in ('evidence/inventory.json','evidence/inventory.sha256'): continue
        need(rel in recorded,'unrecorded entry '+rel)
        row=recorded[rel]
        need(s.st_uid==uid==row['uid'],'ownership '+rel)
        need(oct(stat.S_IMODE(s.st_mode))==row['mode'],'mode '+rel)
        if row['type']=='file':
            need(stat.S_ISREG(s.st_mode) and s.st_size==row['size'] and digest(p)==row['sha256'],'file bytes '+rel)
        elif row['type']=='directory': need(stat.S_ISDIR(s.st_mode),'directory '+rel)
        elif row['type']=='symlink': need(stat.S_ISLNK(s.st_mode) and os.readlink(p)==row['target'],'link '+rel)
        else: raise RuntimeError('unsupported inventory kind')
need(set(actual)==set(recorded)|{'evidence/inventory.json','evidence/inventory.sha256'},'inventory coverage')
expected={
'devvm.SHA256SUMS':'9f703c06b2ab3a4b8c9e8963952e024f64964aa0ec9de09bfceefbf8b65df73a',
'devvm.SHA256SUMS.minisig':'329cafe0b6659f60d36e3ccb320388276ecf061a411162deddb713864d1a3246',
'devvm-0.1.0-linux-amd64.tar.gz':'fc939a651614917404766c8bf1c7f64aed8c136605e133e0602c55101a82284c',
'lima.SHA256SUMS':'4805ceeb791229ecaddcde32bf04b14742f4d036b343ad5d8c478ba5d220fff2',
'lima.SHA256SUMS.asc':'cc974212784876111d1a1d4ab2539e5c7fe2058de04e6c64c60d3887c8cabf2c',
'lima-2.2.1-Linux-x86_64.tar.gz':'b391ac7fcac2b2a5a1628107756463188ded4d18d3104a40a66a8bb6fec01bcb',
'lima-key.asc':'74d7c5d29b78a5967b0da91a2e9330b8a805fd1ea2c8a375dfae634ff85a6da0'}
hashes={name:digest(root/'downloads'/name) for name in expected}
need(hashes==expected,'download hashes')
public=base64.b64decode('RWSjzFsn7ETaijKJ2y7F4DtZobXmyv+LmdclJwZP/KmAkLUwOCzWF/2b')
lines=(root/'downloads/devvm.SHA256SUMS.minisig').read_bytes().splitlines()
packet=base64.b64decode(lines[1],validate=True);gs=base64.b64decode(lines[3],validate=True)
need(public[:2]==b'Ed' and len(public)==42,'public key')
need(packet[:2]==b'ED' and len(packet)==74 and len(gs)==64 and packet[2:10]==public[2:10],'Minisign envelope')
need(lines[2]==b'trusted comment: devvm 0.1.0','trusted comment')
sodium=ctypes.CDLL('libsodium.so.23');need(sodium.sodium_init()>=0,'sodium')
check=sodium.crypto_sign_verify_detached
check.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulonglong,ctypes.c_void_p]
manifest=(root/'downloads/devvm.SHA256SUMS').read_bytes()
for sig,message in [(packet[10:],hashlib.blake2b(manifest).digest()),(gs,packet[10:]+b'devvm 0.1.0')]:
    need(check(ctypes.create_string_buffer(sig),ctypes.create_string_buffer(message),len(message),ctypes.create_string_buffer(public[10:]))==0,'Minisign verification')
gpg_argv=['/usr/bin/gpgv','--homedir',str(root/'verify'),'--status-fd','1','--keyring',str(root/'verify/lima-release.gpg'),str(root/'downloads/lima.SHA256SUMS.asc'),str(root/'downloads/lima.SHA256SUMS')]
r=subprocess.run(gpg_argv,env={'PATH':'/usr/bin:/bin','HOME':str(root/'home'),'LANG':'C.UTF-8'},cwd=root,capture_output=True,timeout=30)
need(r.returncode==0,'OpenPGP exit')
valid=[x.split() for x in r.stdout.decode().splitlines() if x.startswith('[GNUPG:] VALIDSIG ')]
fingerprint='C020EA876CE4E06C7AB95AEF49524C6F9F638F1A'
need(len(valid)==1 and valid[0][2]==fingerprint,'OpenPGP signer')
status_names={x.split()[1] for x in r.stdout.decode().splitlines() if x.startswith('[GNUPG:] ')}
need(not status_names.intersection({'BADSIG','ERRSIG','EXPSIG','EXPKEYSIG','REVKEYSIG','NO_PUBKEY','FAILURE','ERROR','KEYEXPIRED','SIGEXPIRED'}),'OpenPGP status')
archives={};totals={}
for asset,flavor,destination in [
('devvm-0.1.0-linux-amd64.tar.gz','devvm',root/'software/devvm-0.1.0'),
('lima-2.2.1-Linux-x86_64.tar.gz','lima',root/'software/lima-2.2.1')]:
    rows=[];kinds={'file':0,'directory':0,'symlink':0};seen=set()
    plans=json.loads((e/(flavor+'-validated-members.json')).read_text())
    planmap={p['name']:p for p in plans}
    with tarfile.open(root/'downloads'/asset,'r:gz') as t:
        for member in t:
            name=member.name
            if name.startswith('./'): name=name[2:]
            if name in ('','.') and member.isdir(): name='.'
            if member.isdir(): name=name.rstrip('/')
            need(name not in seen,'duplicate archive name');seen.add(name)
            need(name in planmap,'unplanned member '+name)
            need(not member.pax_headers and member.type in (b'0',b'\0',b'5',b'2'),'tar metadata '+name)
            p=destination/name
            s=p.lstat()
            need(s.st_uid==uid,'extracted owner '+name)
            row={'archive_name':member.name,'canonical_name':name,
                 'tar_type':member.type.decode('ascii'),'archive_mode':oct(member.mode),
                 'archive_uid':member.uid,'archive_gid':member.gid,
                 'size':member.size,'linkname':member.linkname,
                 'pax_headers':member.pax_headers}
            if member.isfile():
                kinds['file']+=1
                with t.extractfile(member) as f: archive_sha=hashlib.file_digest(f,'sha256').hexdigest()
                need(stat.S_ISREG(s.st_mode) and s.st_size==member.size and digest(p)==archive_sha,'extracted bytes '+name)
                mode=0o700 if member.mode==0o755 else 0o600
                need(stat.S_IMODE(s.st_mode)==mode,'extracted file mode '+name)
                row['sha256']=archive_sha
            elif member.isdir():
                kinds['directory']+=1
                need(stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode)==0o700,'extracted directory '+name)
            elif member.issym():
                kinds['symlink']+=1
                need(name=='share/doc/lima/templates' and member.linkname=='../../lima/templates','expected link')
                need(stat.S_ISLNK(s.st_mode) and os.readlink(p)==member.linkname,'extracted link')
                need(p.resolve()==destination/'share/lima/templates' and p.resolve().is_dir(),'resolved link')
                row['resolved_destination']=str(p.resolve())
            else: raise RuntimeError('unexpected extracted type')
            rows.append(row)
    need(seen==set(planmap),'archive plan coverage')
    archives[flavor]=rows;totals[flavor]=kinds
commands=[]
for p in sorted(e.glob('*.command.json')):
    c=json.loads(p.read_text());need(c['exit']==0,'stage child exit '+p.name)
    need(c['argv'][0] in ('/usr/bin/curl','/usr/bin/gpg','/usr/bin/gpgv'),'unexpected executed program')
    commands.append({'record':p.name,'executable':c['argv'][0],'exit':c['exit']})
need(len(commands)==9,'stage command count')
need(json.loads((e/'status.json').read_text())['state']=='STAGING_COMPLETE_BINARIES_NOT_EXECUTED','final state')
audit=e/'independent-review';need(not audit.exists(),'audit directory exists');audit.mkdir(mode=0o700)
for flavor,rows in archives.items():
    (audit/(flavor+'-actual-archive-members.json')).write_text(json.dumps(rows,indent=2)+'\n')
(audit/'gpgv.stdout').write_bytes(r.stdout);(audit/'gpgv.stderr').write_bytes(r.stderr)
summary={'original_inventory_sha256':inventory_hash,'original_inventory_records':len(inventory),
'download_sha256':hashes,'minisign_manifest':'PASS','minisign_trusted_comment':'PASS',
'lima_openpgp_exit':r.returncode,'lima_signer':fingerprint,'archives':totals,
'payload_bytes_compared':True,'ownership_and_modes':'PASS','original_inventory_coverage':'PASS',
'stage_child_commands':commands,'downloaded_binary_invocations':0}
(audit/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
