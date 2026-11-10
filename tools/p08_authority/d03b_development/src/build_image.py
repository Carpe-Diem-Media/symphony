"""Unprivileged deterministic image preparation. Never mounts or executes it."""
import json
import os
from pathlib import Path
import shutil
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract import D02_TREE, Refusal, canonical, digest, require

D02 = Path('/tmp/symphony-p08-r1b-d02')
FORBIDDEN = {'sudo','su','docker','virsh','libvirtd','systemctl','systemd-run','ssh','ssh-keygen','git','bash','sh'}


def image_inventory(root):
    root = Path(root);result = []
    for path in sorted(root.rglob('*')):
        relative = str(path.relative_to(root));s = path.lstat()
        require(path.name not in FORBIDDEN and not s.st_mode & 0o6000, 'IMAGE_ADMIN_PAYLOAD')
        value = {'path': relative, 'mode': stat.S_IMODE(s.st_mode), 'preparation_uid': s.st_uid}
        require(stat.S_ISLNK(s.st_mode) or not value['mode'] & 0o022, 'IMAGE_WRITABLE')
        if stat.S_ISLNK(s.st_mode):
            target = os.readlink(path)
            require(not target.startswith('/') and path.resolve(strict=True).is_relative_to(root.resolve()), 'IMAGE_LINK_ESCAPE')
            value.update(kind='symlink', target=target)
            # Symlink mode 0777 cannot grant write authority to its target.
        elif stat.S_ISDIR(s.st_mode):value.update(kind='directory')
        elif stat.S_ISREG(s.st_mode):
            require(s.st_nlink == 1, 'IMAGE_ALIAS')
            raw = path.read_bytes();value.update(kind='file', bytes=len(raw), sha256=digest(raw))
        else:raise Refusal('IMAGE_SPECIAL_FILE')
        result.append(value)
    return result


def normalized(entries):return [{key:value for key,value in entry.items() if key != 'preparation_uid'} for entry in entries]


def fixed_directory(path, mode=0o755):
    path=Path(path)
    require(mode in {0o700,0o755} and not path.is_symlink(), 'IMAGE_DIRECTORY_UNCERTAIN')
    if not path.exists():path.mkdir(mode=mode)
    require(path.is_dir() and not path.is_symlink(), 'IMAGE_DIRECTORY_UNCERTAIN')
    path.chmod(mode)


def image_parents(path,root):
    root=Path(root);path=Path(path)
    require(path.is_relative_to(root),'IMAGE_LINK_ESCAPE')
    for directory in reversed([path,*path.parents]):
        if directory.is_relative_to(root):fixed_directory(directory)


def build(destination):
    require(os.geteuid() == 1000, 'PREPARATION_ACCOUNT_REQUIRED')
    destination = Path(destination)
    require(not destination.exists() and not destination.is_symlink(), 'IMAGE_COLLISION')
    runtime_raw = (D02/'owner-handoff/runtime-inventory.json').read_bytes()
    require(digest(runtime_raw) == '876e7b34688d0c14c7d52a70db067118cb91c26db71818db38ebc000e7f017f6', 'RUNTIME_INPUT_CHANGED')
    runtime = json.loads(runtime_raw)
    source = json.loads((D02/'evidence/final-source-inventory.json').read_bytes())
    require(source['tree'] == D02_TREE, 'D02_INPUT_CHANGED')
    fixed_directory(destination)
    allowed = {}
    for entry in runtime['entries']:
        path = Path(entry['path']);raw = path.read_bytes();s = path.lstat()
        require(s.st_uid == 0 and not s.st_mode & 0o022 and len(raw) == entry['bytes'] and digest(raw) == entry['sha256'], 'RUNTIME_INPUT_CHANGED')
        if path.name in FORBIDDEN or str(path).startswith('/etc/'):continue
        target = destination/str(path).lstrip('/');image_parents(target.parent,destination)
        target.write_bytes(raw);target.chmod(entry['mode']);allowed[str(path)] = entry
    # Materialize only SONAME aliases resolving to an already pinned native file.
    directory = Path('/usr/lib/x86_64-linux-gnu')
    for path in sorted(directory.iterdir()):
        if path.is_symlink():
            resolved = str(path.resolve())
            if resolved in allowed:
                target = destination/str(path).lstrip('/')
                if not target.exists():target.symlink_to(os.path.relpath(destination/resolved.lstrip('/'),target.parent))
    (destination/'lib').symlink_to('usr/lib')
    fixed_directory(destination/'lib64')
    (destination/'lib64/ld-linux-x86-64.so.2').symlink_to('../usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2')
    for name in ['app','app/d02','etc','run','output','tmp','dev','proc','sys']:image_parents(destination/name,destination)
    for name in ['worker.py','finite_suite.py','contract.py']:
        (destination/'app'/name).write_bytes(Path(__file__).with_name(name).read_bytes())
        (destination/'app'/name).chmod(0o644)
    by_path = {entry['path']: entry for entry in source['entries']}
    for name in ['p08_qualification_runner.py','p08_development_release.py']:
        path = 'tools/tests/' + name;raw=(D02/'candidate'/path).read_bytes()
        require(digest(raw)==by_path[path]['sha256'],'D02_INPUT_CHANGED')
        (destination/'app/d02'/name).write_bytes(raw);(destination/'app/d02'/name).chmod(0o644)
    (destination/'app/fixture.json').write_bytes(canonical({'meaning':'D03 synthetic only','value':42}))
    (destination/'app/fixture.json').chmod(0o644)
    (destination/'etc/passwd').write_text('root:x:0:0:root:/:/nonexistent\n')
    (destination/'etc/group').write_text('root:x:0:\n')
    (destination/'etc/nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n')
    for path in (destination/'etc').iterdir():path.chmod(0o644)
    for path in [destination,*sorted((x for x in destination.rglob('*') if x.is_dir() and not x.is_symlink()),key=lambda x:len(x.parts))]:path.chmod(0o755)
    inventory=image_inventory(destination)
    return {'schema':'p08-d03-worker-image-1','source_tree':D02_TREE,
        'runtime_input_sha256':digest(runtime_raw),'entries':normalized(inventory)}






def verify_image(root, expected):
    require(type(expected) is list and normalized(image_inventory(root))==expected, 'IMAGE_IDENTITY_MISMATCH')


def safe_export(directory, name, limit):
    """Historical dirfd/no-follow/single-link bounded output recovery."""
    require(type(name) is str and name in {'result.json','worker-identity.json','finite-result.json'} and type(limit) is int and 0<limit<=8388608, 'EXPORT_UNREGISTERED')
    directory=Path(directory)
    require(not directory.is_symlink(), 'EXPORT_ALIAS')
    fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        try:
            handle=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=fd)
            try:
                st=os.fstat(handle)
                require(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and 0<=st.st_size<=limit,'EXPORT_UNSAFE')
                raw=os.read(handle,limit+1);after=os.fstat(handle);named=os.stat(name,dir_fd=fd,follow_symlinks=False)
                identity=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
                require(len(raw)==st.st_size and identity(st)==identity(after)==identity(named),'EXPORT_CHANGED')
                return raw
            finally:os.close(handle)
        except OSError:raise Refusal('EXPORT_UNSAFE') from None
    finally:os.close(fd)


if __name__ == '__main__':
    try:
        require(len(sys.argv)==2,'IMAGE_ARGUMENTS_INVALID')
        manifest=build(Path(sys.argv[1]));print(canonical(manifest).decode())
    except Refusal as error:print(error.code,file=sys.stderr);raise SystemExit(2)
