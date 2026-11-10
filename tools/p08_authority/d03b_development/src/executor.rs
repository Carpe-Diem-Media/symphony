//! D03B adaptation of the retained fixed v3 executor. No generic execution API.
//! Live --session is root-only and requires a separate owner host-test grant.
use std::{env,ffi::{c_char,c_int,c_void,CStr,CString},fs,io::{self,BufRead,Read,Write},os::unix::fs::{MetadataExt,OpenOptionsExt},ptr,time::Instant};
const UNIT:&str="p08-d03-worker.service";
const DEPLOY:&str="/var/lib/software-factory/p08-r1b-host-dev/P08-R1B-HOST-DEV-01";
const ROOT:&str="/var/lib/software-factory/p08-r1b-host-dev/P08-R1B-HOST-DEV-01/image";
const RUNTIME:&str="p08-d03-worker";
const DEST:&str="org.freedesktop.systemd1";
const MANAGER:&str="org.freedesktop.systemd1.Manager";
#[repr(C)] struct BusError {name:*const c_char,message:*const c_char,need_free:c_int}
#[repr(C)] struct CapHeader {version:u32,pid:i32}
#[repr(C)] #[derive(Clone,Copy)] struct CapData {effective:u32,permitted:u32,inheritable:u32}
#[repr(C)] struct PollFd {fd:c_int,events:i16,revents:i16}
#[link(name="systemd")]
unsafe extern "C" {
 fn sd_bus_open_system(b:*mut *mut c_void)->c_int;
 fn sd_bus_unref(b:*mut c_void)->*mut c_void;
 fn sd_bus_message_new_method_call(b:*mut c_void,m:*mut *mut c_void,d:*const c_char,p:*const c_char,i:*const c_char,method:*const c_char)->c_int;
 fn sd_bus_message_open_container(m:*mut c_void,t:c_char,s:*const c_char)->c_int;
 fn sd_bus_message_close_container(m:*mut c_void)->c_int;
 fn sd_bus_message_enter_container(m:*mut c_void,t:c_char,s:*const c_char)->c_int;
 fn sd_bus_message_exit_container(m:*mut c_void)->c_int;
 fn sd_bus_message_read_basic(m:*mut c_void,t:c_char,v:*mut c_void)->c_int;
 fn sd_bus_message_read_array(m:*mut c_void,t:c_char,v:*mut *const c_void,n:*mut usize)->c_int;
 fn sd_bus_message_append_basic(m:*mut c_void,t:c_char,v:*const c_void)->c_int;
 fn sd_bus_message_unref(m:*mut c_void)->*mut c_void;
 fn sd_bus_call(b:*mut c_void,m:*mut c_void,timeout:u64,e:*mut BusError,reply:*mut *mut c_void)->c_int;
 fn sd_bus_get_property(b:*mut c_void,d:*const c_char,p:*const c_char,i:*const c_char,n:*const c_char,e:*mut BusError,r:*mut *mut c_void,t:*const c_char)->c_int;
 fn sd_bus_error_free(e:*mut BusError);
 fn prctl(option:c_int,...)->c_int;
 fn capset(h:*const CapHeader,d:*const CapData)->c_int;
 fn geteuid()->u32;
 fn poll(fds:*mut PollFd,n:usize,timeout:c_int)->c_int;
}
fn cs(s:&str)->CString {CString::new(s).expect("validated fixed input")}
fn check(r:c_int)->io::Result<()> {if r<0{Err(io::Error::from_raw_os_error(-r))}else{Ok(())}}
fn refuse(s:&str)->io::Error{io::Error::other(s.to_string())}
struct Bus(*mut c_void);
impl Drop for Bus {fn drop(&mut self){unsafe{sd_bus_unref(self.0);}}}
struct Message(*mut c_void);
impl Drop for Message {fn drop(&mut self){unsafe{sd_bus_message_unref(self.0);}}}
trait Wire {
 fn open(&self,t:u8,s:&str)->io::Result<()>;
 fn close(&self)->io::Result<()>;
 fn text(&self,s:&str)->io::Result<()>;
 fn number(&self,t:u8,n:u64)->io::Result<()>;
}
impl Wire for Message {
 fn open(&self,t:u8,s:&str)->io::Result<()>{check(unsafe{sd_bus_message_open_container(self.0,t as c_char,cs(s).as_ptr())})}
 fn close(&self)->io::Result<()>{check(unsafe{sd_bus_message_close_container(self.0)})}
 fn text(&self,s:&str)->io::Result<()>{check(unsafe{sd_bus_message_append_basic(self.0,b's' as c_char,cs(s).as_ptr().cast())})}
 fn number(&self,t:u8,n:u64)->io::Result<()>{unsafe{match t{b'u'=>check(sd_bus_message_append_basic(self.0,t as c_char,(&(n as u32) as *const u32).cast())),b'b'=>check(sd_bus_message_append_basic(self.0,t as c_char,(&(n as i32) as *const i32).cast())),b't'=>check(sd_bus_message_append_basic(self.0,t as c_char,(&n as *const u64).cast())),_=>Err(refuse("WIRE_TYPE_INVALID"))}}}
}
#[derive(Debug)] enum Value {Text(String),Bool(bool),U64(u64),Strings(Vec<String>)}
fn txt(s:&str)->Value{Value::Text(s.into())}
fn strs(v:&[&str])->Value{Value::Strings(v.iter().map(|s|s.to_string()).collect())}
fn properties(attempt:&str,token:&str)->Vec<(&'static str,Value)>{
 use Value::*;
 vec![
 ("Description",txt(&format!("p08-d03:{attempt}:{token}"))),("Type",txt("exec")),("DynamicUser",Bool(true)),("RootDirectory",txt(ROOT)),("MountAPIVFS",Bool(true)),
 ("RuntimeDirectory",strs(&[RUNTIME])),("PrivateTmp",Bool(true)),("PrivateNetwork",Bool(true)),("PrivateIPC",Bool(true)),("ProtectHome",txt("yes")),("ProtectSystem",txt("strict")),("NoNewPrivileges",Bool(true)),
 ("CapabilityBoundingSet",U64(0)),("AmbientCapabilities",U64(0)),("PrivateDevices",Bool(true)),("ProtectKernelTunables",Bool(true)),("ProtectKernelModules",Bool(true)),("ProtectKernelLogs",Bool(true)),("ProtectControlGroups",Bool(true)),
 ("RestrictSUIDSGID",Bool(true)),("RestrictRealtime",Bool(true)),("LockPersonality",Bool(true)),("KillMode",txt("control-group")),("SendSIGKILL",Bool(true)),("RemainAfterExit",Bool(true)),("Delegate",Bool(false)),
 ("TimeoutStopUSec",U64(2_000_000)),("RuntimeMaxUSec",U64(20_000_000)),("CPUQuotaPerSecUSec",U64(500_000)),("MemoryMax",U64(268_435_456)),("TasksMax",U64(16)),
 ("PassEnvironment",Strings(vec![])),("SupplementaryGroups",Strings(vec![])),("ProtectProc",txt("invisible")),("ProcSubset",txt("pid")),("KeyringMode",txt("private")),("LimitCORE",U64(0)),("LimitFSIZE",U64(8_388_608)),
 ("Environment",strs(&["HOME=/output/home","PATH=/nonexistent","LANG=C.UTF-8","LC_ALL=C.UTF-8"])),("ReadWritePaths",strs(&["/output"])),("StandardInput",txt("null")),
 ("StandardOutputFile",txt(&format!("{DEPLOY}/receipts/{attempt}.stdout"))),("StandardErrorFile",txt(&format!("{DEPLOY}/receipts/{attempt}.stderr")))]
}
fn prop(w:&impl Wire,name:&str,sig:&str,f:impl FnOnce()->io::Result<()>)->io::Result<()>{w.open(b'r',"sv")?;w.text(name)?;w.open(b'v',sig)?;f()?;w.close()?;w.close()}
fn encode(w:&impl Wire,attempt:&str,token:&str)->io::Result<()>{
 w.text(UNIT)?;w.text("fail")?;w.open(b'a',"(sv)")?;
 for (name,value) in properties(attempt,token){
  let sig=match &value{Value::Text(_)=>"s",Value::Bool(_)=>"b",Value::U64(_)=>"t",Value::Strings(_)=>"as"};
  prop(w,name,sig,||match value{Value::Text(s)=>w.text(&s),Value::Bool(v)=>w.number(b'b',u64::from(v)),Value::U64(v)=>w.number(b't',v),Value::Strings(v)=>{w.open(b'a',"s")?;for s in v{w.text(&s)?;}w.close()}})?;
 }
 prop(w,"RuntimeDirectoryMode","u",||w.number(b'u',0o700))?;prop(w,"UMask","u",||w.number(b'u',0o077))?;
 prop(w,"RestrictAddressFamilies","(bas)",||{w.open(b'r',"bas")?;w.number(b'b',1)?;w.open(b'a',"s")?;w.text("AF_UNIX")?;w.close()?;w.close()})?;
 prop(w,"RestrictNamespaces","t",||w.number(b't',0))?;
 prop(w,"BindPaths","a(ssbt)",||{w.open(b'a',"(ssbt)")?;w.open(b'r',"ssbt")?;w.text(&format!("/run/{RUNTIME}"))?;w.text("/output")?;w.number(b'b',0)?;w.number(b't',0)?;w.close()?;w.close()})?;
 prop(w,"LoadCredential","a(ss)",||{w.open(b'a',"(ss)")?;for (name,dir) in [("release.json","releases"),("context.json","context")]{w.open(b'r',"ss")?;w.text(name)?;w.text(&format!("{DEPLOY}/{dir}/{attempt}.json"))?;w.close()?;}w.close()})?;
 prop(w,"ExecStart","a(sasb)",||{w.open(b'a',"(sasb)")?;w.open(b'r',"sasb")?;w.text("/usr/bin/python3.14")?;w.open(b'a',"s")?;for s in ["/usr/bin/python3.14","-I","-S","-B","/app/worker.py","--attempt",attempt]{w.text(s)?;}w.close()?;w.number(b'b',0)?;w.close()?;w.close()})?;
 w.close()?;w.open(b'a',"(sa(sv))")?;w.close()
}
fn method(b:&Bus,name:&str)->io::Result<Message>{let mut m=ptr::null_mut();check(unsafe{sd_bus_message_new_method_call(b.0,&mut m,cs(DEST).as_ptr(),cs("/org/freedesktop/systemd1").as_ptr(),cs(MANAGER).as_ptr(),cs(name).as_ptr())})?;Ok(Message(m))}
fn call(b:&Bus,m:&Message)->io::Result<Message>{let mut r=ptr::null_mut();let mut e=BusError{name:ptr::null(),message:ptr::null(),need_free:0};let result=unsafe{sd_bus_call(b.0,m.0,2_000_000,&mut e,&mut r)};unsafe{sd_bus_error_free(&mut e)};if result<0{unsafe{sd_bus_message_unref(r)};check(result)?;}Ok(Message(r))}
fn unit_op(b:&Bus,op:&str)->io::Result<()>{let m=method(b,op)?;m.text(UNIT)?;if op=="StopUnit"{m.text("replace")?;}call(b,&m)?;Ok(())}
fn get(b:&Bus,path:&str,interface:&str,name:&str,sig:&str)->io::Result<Message>{let mut r=ptr::null_mut();let mut e=BusError{name:ptr::null(),message:ptr::null(),need_free:0};let result=unsafe{sd_bus_get_property(b.0,cs(DEST).as_ptr(),cs(path).as_ptr(),cs(interface).as_ptr(),cs(name).as_ptr(),&mut e,&mut r,cs(sig).as_ptr())};unsafe{sd_bus_error_free(&mut e)};if result<0{unsafe{sd_bus_message_unref(r)};check(result)?;}Ok(Message(r))}
fn basic<T:Default>(m:&Message,t:u8)->io::Result<T>{let mut v=T::default();let n=unsafe{sd_bus_message_read_basic(m.0,t as c_char,(&mut v as *mut T).cast())};check(n)?;if n==0{return Err(refuse("PID1_REPLY_MISSING"));}Ok(v)}
fn string(m:&Message,t:u8)->io::Result<String>{let p=basic::<*const c_char>(m,t)?;if p.is_null(){return Err(refuse("PID1_REPLY_MISSING"));}let s=unsafe{CStr::from_ptr(p)}.to_str().map_err(io::Error::other)?.to_string();if s.len()>8192||s.contains(['\n','\r']){return Err(refuse("PID1_REPLY_INVALID"));}Ok(s)}
fn array_strings(m:&Message)->io::Result<String>{check(unsafe{sd_bus_message_enter_container(m.0,b'a' as c_char,cs("s").as_ptr())})?;let mut out=vec![];loop{let mut p:*const c_char=ptr::null();let n=unsafe{sd_bus_message_read_basic(m.0,b's' as c_char,(&mut p as *mut *const c_char).cast())};check(n)?;if n==0{break;}if out.len()>=32{return Err(refuse("PID1_REPLY_INVALID"));}out.push(unsafe{CStr::from_ptr(p)}.to_str().map_err(io::Error::other)?.to_string());}check(unsafe{sd_bus_message_exit_container(m.0)})?;Ok(out.join(" "))}
fn path(b:&Bus)->io::Result<Option<String>>{let m=method(b,"GetUnit")?;m.text(UNIT)?;let mut r=ptr::null_mut();let mut e=BusError{name:ptr::null(),message:ptr::null(),need_free:0};let result=unsafe{sd_bus_call(b.0,m.0,2_000_000,&mut e,&mut r)};let absent=!e.name.is_null()&&unsafe{CStr::from_ptr(e.name)}.to_bytes()==b"org.freedesktop.systemd1.NoSuchUnit";unsafe{sd_bus_error_free(&mut e)};let reply=Message(r);if absent{return Ok(None);}check(result)?;Ok(Some(string(&reply,b'o')?))}
fn show(b:&Bus,held:&mut bool,acquire:bool)->io::Result<Vec<(String,String)>>{
 let Some(p)=path(b)? else{return Ok(vec![("LoadState".into(),"not-found".into())]);};
 if !*held&&acquire{unit_op(b,"RefUnit")?;*held=true;}
 let mut out=vec![];
 for (interface,keys) in [("org.freedesktop.systemd1.Unit",&["Id","LoadState","ActiveState","SubState","Description"] as &[&str]),("org.freedesktop.systemd1.Service",&["ControlGroup","RootDirectory","ProtectHome","ProtectSystem","KillMode","ProtectProc","ProcSubset"]) ]{
  for key in keys{out.push((key.to_string(),string(&get(b,&p,interface,key,"s")?,b's')?));}
 }
 let unit="org.freedesktop.systemd1.Unit";let svc="org.freedesktop.systemd1.Service";
 out.push(("Transient".into(),if basic::<i32>(&get(b,&p,unit,"Transient","b")?,b'b')?!=0{"yes"}else{"no"}.into()));
 for key in ["DynamicUser","NoNewPrivileges","PrivateNetwork","PrivateDevices","PrivateTmp","PrivateIPC","ProtectControlGroups","ProtectKernelTunables","ProtectKernelModules","ProtectKernelLogs","RestrictSUIDSGID","RestrictRealtime","LockPersonality","Delegate"]{out.push((key.into(),if basic::<i32>(&get(b,&p,svc,key,"b")?,b'b')?!=0{"yes"}else{"no"}.into()));}
 for key in ["RuntimeMaxUSec","TimeoutStopUSec","TasksMax","MemoryMax","CapabilityBoundingSet","AmbientCapabilities"]{let n=basic::<u64>(&get(b,&p,svc,key,"t")?,b't')?;out.push((key.into(),if key.ends_with("Capabilities")||key=="CapabilityBoundingSet"{if n==0{"".into()}else{format!("{n:x}")}}else{n.to_string()}));}
 for key in ["MainPID","ExecMainPID"]{out.push((key.into(),basic::<u32>(&get(b,&p,svc,key,"u")?,b'u')?.to_string()));}
 for key in ["ExecMainCode","ExecMainStatus"]{out.push((key.into(),basic::<i32>(&get(b,&p,svc,key,"i")?,b'i')?.to_string()));}
 out.push(("SupplementaryGroups".into(),array_strings(&get(b,&p,svc,"SupplementaryGroups","as")?)?));
 let raf=get(b,&p,svc,"RestrictAddressFamilies","(bas)")?;check(unsafe{sd_bus_message_enter_container(raf.0,b'r' as c_char,cs("bas").as_ptr())})?;if basic::<i32>(&raf,b'b')?!=1{return Err(refuse("PROFILE_UNPROVEN"));}out.push(("RestrictAddressFamilies".into(),array_strings(&raf)?));check(unsafe{sd_bus_message_exit_container(raf.0)})?;
 let m=get(b,&p,unit,"InvocationID","ay")?;let mut bytes:*const c_void=ptr::null();let mut n=0;check(unsafe{sd_bus_message_read_array(m.0,b'y' as c_char,&mut bytes,&mut n)})?;if n!=16||bytes.is_null(){return Err(refuse("INVOCATION_UNPROVEN"));}out.push(("InvocationID".into(),unsafe{std::slice::from_raw_parts(bytes.cast::<u8>(),n)}.iter().map(|v|format!("{v:02x}")).collect()));
 Ok(out)
}
fn trusted(path:&std::path::Path)->io::Result<()>{for p in path.ancestors(){let m=fs::symlink_metadata(p)?;if m.uid()!=0||m.mode()&0o022!=0||m.file_type().is_symlink(){return Err(refuse("ROOT_CUSTODY_UNPROVEN"));}}Ok(())}
fn fixed_input()->io::Result<(String,String)>{let path=std::path::Path::new(DEPLOY).join("state/active-attempt");trusted(&path)?;let mut f=fs::OpenOptions::new().read(true).custom_flags(0x20000|0x80000|0x800).open(&path)?;let before=f.metadata()?;if !before.is_file()||before.nlink()!=1||before.len()!=98{return Err(refuse("ACTIVE_INPUT_INVALID"));}let mut raw=String::new();std::io::Read::by_ref(&mut f).take(99).read_to_string(&mut raw)?;let after=f.metadata()?;if (before.ino(),before.mtime_nsec(),before.ctime_nsec(),before.len())!=(after.ino(),after.mtime_nsec(),after.ctime_nsec(),after.len()){return Err(refuse("ACTIVE_INPUT_CHANGED"));}let v:Vec<_>=raw.lines().collect();if v.len()!=2||!hex(v[0],32)||!hex(v[1],64){return Err(refuse("ACTIVE_INPUT_INVALID"));}Ok((v[0].into(),v[1].into()))}
fn output_guard(attempt:&str)->io::Result<()>{
 for suffix in ["stdout","stderr"]{
  let path=std::path::Path::new(DEPLOY).join(format!("receipts/{attempt}.{suffix}"));trusted(&path)?;
  let f=fs::OpenOptions::new().read(true).custom_flags(0x20000|0x80000|0x800).open(&path)?;let m=f.metadata()?;
  if !m.is_file()||m.nlink()!=1||m.mode()&0o777!=0o600||m.len()!=0{return Err(refuse("OUTPUT_NOT_RESERVED"));}
  let named=fs::symlink_metadata(&path)?;if (m.dev(),m.ino())!=(named.dev(),named.ino()){return Err(refuse("OUTPUT_CHANGED"));}
 }
 Ok(())
}
fn wait_terminal(b:&Bus)->io::Result<()>{
 let deadline=Instant::now();
 loop{
  let terminal=match path(b)?{None=>true,Some(p)=>["inactive","failed"].contains(&string(&get(b,&p,"org.freedesktop.systemd1.Unit","ActiveState","s")?,b's')?.as_str())};
  if terminal{return Ok(());}
  if deadline.elapsed().as_millis()>3000{return Err(refuse("STOP_UNCERTAIN"));}
  std::thread::sleep(std::time::Duration::from_millis(20));
 }
}
fn abort_owned(b:&Bus,owned:&Option<(String,String)>,held:&mut bool)->io::Result<()>{
 if let Some((a,t))=owned{
  if let Some(p)=path(b)?{
   let desc=string(&get(b,&p,"org.freedesktop.systemd1.Unit","Description","s")?,b's')?;
   if desc!=format!("p08-d03:{a}:{t}"){return Err(refuse("ABORT_IDENTITY_UNCERTAIN"));}
   unit_op(b,"StopUnit")?;
   let deadline=Instant::now();
   loop{
    let terminal=match path(b)?{None=>true,Some(p)=>["inactive","failed"].contains(&string(&get(b,&p,"org.freedesktop.systemd1.Unit","ActiveState","s")?,b's')?.as_str())};
    if terminal{break;}
    if deadline.elapsed().as_millis()>3000{return Err(refuse("ABORT_STOP_UNCERTAIN"));}
    std::thread::sleep(std::time::Duration::from_millis(20));
   }
  }
 }
 if *held{unit_op(b,"UnrefUnit")?;*held=false;}
 Ok(())
}
fn hex(s:&str,n:usize)->bool{s.len()==n&&s.bytes().all(|c|c.is_ascii_digit()||(b'a'..=b'f').contains(&c))&&s.bytes().any(|c|c!=b'0')}
fn reduce()->io::Result<()> {
 if unsafe{geteuid()}!=0 {return Err(io::Error::other("manual administrator execution required"));}
 // NOROOT+LOCKED, NO_SETUID_FIXUP+LOCKED, NO_CAP_AMBIENT_RAISE+LOCKED.
 if unsafe{prctl(28,207u64,0u64,0u64,0u64)}!=0{return Err(io::Error::last_os_error());}
 let last:u32=fs::read_to_string("/proc/sys/kernel/cap_last_cap")?.trim().parse().map_err(io::Error::other)?;
 if last>63 {return Err(io::Error::other("unexpected capability range"));}
 for cap in 0..=last {if unsafe{prctl(24,cap as u64,0u64,0u64,0u64)}!=0{return Err(io::Error::last_os_error());}}
 let h=CapHeader{version:0x20080522,pid:0};let d=[CapData{effective:0,permitted:0,inheritable:0};2];
 if unsafe{capset(&h,d.as_ptr())}!=0{return Err(io::Error::last_os_error());}
 if unsafe{prctl(38,1u64,0u64,0u64,0u64)}!=0{return Err(io::Error::last_os_error());}
 let status=fs::read_to_string("/proc/self/status")?;
 for line in status.lines().filter(|l|l.starts_with("Cap")||l.starts_with("Uid:")||l.starts_with("Gid:")||l.starts_with("NoNewPrivs:")){eprintln!("{line}");}
 for name in ["CapInh:","CapPrm:","CapEff:","CapBnd:","CapAmb:"] {
  let value=status.lines().find_map(|l|l.strip_prefix(name)).ok_or_else(||io::Error::other("missing cap field"))?;
  if u64::from_str_radix(value.trim(),16).map_err(io::Error::other)?!=0{return Err(io::Error::other("capability reduction failed"));}
 }
 let bits=unsafe{prctl(27,0u64,0u64,0u64,0u64)};eprintln!("Securebits={bits}");
 if bits!=207{return Err(io::Error::other("securebits reduction missing"));}
 if !status.lines().any(|l| l.strip_prefix("Uid:").is_some_and(|v|v.split_whitespace().all(|x|x=="0"))){return Err(io::Error::other("all UID fields must be zero"));}
 if !status.lines().any(|l|l.starts_with("NoNewPrivs:")&&l.ends_with('1')){return Err(io::Error::other("NNP missing"));}
 Ok(())
}
fn verb(s:&str)->io::Result<&str>{if ["CREATE","SHOW","STOP","UNREF","CLOSE"].contains(&s){Ok(s)}else{Err(refuse("COMMAND_INVALID"))}}
fn session()->io::Result<()>{
 if unsafe{geteuid()}!=0{return Err(refuse("HOST_ROOT_REQUIRED"));}
 trusted(std::path::Path::new(ROOT))?;trusted(std::path::Path::new(DEPLOY).join("executor").as_path())?;
 reduce()?;
 let mut raw=ptr::null_mut();check(unsafe{sd_bus_open_system(&mut raw)})?;let bus=Bus(raw);let mut held=false;let mut released=false;let started=Instant::now();let mut owned=None;
 let result=(||->io::Result<()>{loop{
  if started.elapsed().as_secs()>=60{return Err(refuse("SESSION_EXPIRED"));}
  let mut pollfd=PollFd{fd:0,events:1,revents:0};if unsafe{poll(&mut pollfd,1,25_000)}<=0{return Err(refuse("HOST_CHANNEL_LOST"));}
  // Bounded unbuffered line read prevents an unbounded worker-controlled request.
  let mut line=String::new();io::stdin().lock().take(33).read_line(&mut line)?;if line.len()>16||!line.ends_with('\n'){return Err(refuse("COMMAND_INVALID"));}
  let command=verb(line.trim_end_matches('\n'))?;
  match command{
   "CREATE"=>{let (a,t)=fixed_input()?;output_guard(&a)?;if path(&bus)?.is_some(){return Err(refuse("UNIT_COLLISION"));}owned=Some((a.clone(),t.clone()));let m=method(&bus,"StartTransientUnit")?;encode(&m,&a,&t)?;call(&bus,&m)?;unit_op(&bus,"RefUnit")?;held=true;released=false;println!("Created=yes");},
   "SHOW"=>{for (k,v) in show(&bus,&mut held,!released)?{println!("{k}={v}");}println!("ReferenceHeld={}",if held{"yes"}else{"no"});},
   "STOP"=>{let (a,t)=fixed_input()?;owned=Some((a.clone(),t.clone()));let props=show(&bus,&mut held,!released)?;if !props.iter().any(|(k,v)|k=="Description"&&v==&format!("p08-d03:{a}:{t}")){return Err(refuse("UNIT_IDENTITY_MISMATCH"));}unit_op(&bus,"StopUnit")?;wait_terminal(&bus)?;println!("Stopped=yes");},
   "UNREF"=>{let p=show(&bus,&mut held,!released)?;if !p.iter().any(|(k,v)|k=="LoadState"&&v=="not-found")&&!p.iter().any(|(k,v)|k=="ActiveState"&&["inactive","failed"].contains(&v.as_str())){return Err(refuse("UNIT_NOT_TERMINAL"));}if held{unit_op(&bus,"UnrefUnit")?;held=false;}released=true;println!("ReferenceReleased=yes");},
   "CLOSE"=>{if held{return Err(refuse("REFERENCE_NOT_RELEASED"));}println!("Closed=yes\nEND");io::stdout().flush()?;return Ok(());},_=>unreachable!()
  }
  println!("END");io::stdout().flush()?;
 }})();
 if result.is_err(){match abort_owned(&bus,&owned,&mut held){Ok(())=>eprintln!("ABORT_STOP_TERMINAL_REFERENCE_RELEASED"),Err(e)=>eprintln!("ABORT_QUARANTINE_REQUIRED={e}")}}
 result
}
fn main()->io::Result<()>{let args:Vec<_>=env::args().skip(1).collect();if args!=["--session"]{return Err(refuse("only --session is accepted"));}session()}
#[cfg(test)] mod tests{
 use super::*;use std::cell::RefCell;
 struct Recorder(RefCell<Vec<String>>);
 impl Wire for Recorder{
 fn open(&self,t:u8,s:&str)->io::Result<()>{self.0.borrow_mut().push(format!("open:{}:{s}",t as char));Ok(())}
 fn close(&self)->io::Result<()>{self.0.borrow_mut().push("close".into());Ok(())}
 fn text(&self,s:&str)->io::Result<()>{self.0.borrow_mut().push(format!("s:{s}"));Ok(())}
 fn number(&self,t:u8,n:u64)->io::Result<()>{self.0.borrow_mut().push(format!("{}:{n}",t as char));Ok(())}}
 #[test] fn no_generic_commands(){for x in ["systemctl","CREATE unit","CREATE\nSTOP","--self-test",""]{assert!(verb(x).is_err());}for x in ["CREATE","SHOW","STOP","UNREF","CLOSE"]{assert!(verb(x).is_ok());}}
 #[test] fn exact_identifier_validation(){assert!(hex(&"2".repeat(32),32));for s in ["../x".into(),"0".repeat(32),"Z".repeat(32)]{assert!(!hex(&s,32));}}
 fn trace()->Vec<String>{let w=Recorder(RefCell::new(vec![]));encode(&w,&"2".repeat(32),&"7".repeat(64)).unwrap();w.0.into_inner()}
 #[test] fn fixed_start_envelope(){let t=trace();assert_eq!(&t[..3],[format!("s:{UNIT}"),"s:fail".into(),"open:a:(sv)".into()]);assert!(t.contains(&"open:a:(sa(sv))".into()));}
 #[test] fn historical_wire_types(){let t=trace();for (key,sig) in [("RuntimeDirectoryMode","u"),("UMask","u"),("RestrictAddressFamilies","(bas)"),("RestrictNamespaces","t"),("LoadCredential","a(ss)"),("ExecStart","a(sasb)"),("BindPaths","a(ssbt)")]{let n=t.iter().position(|x|x==&format!("s:{key}")).unwrap();assert_eq!(t[n+1],format!("open:v:{sig}"));}}
 #[test] fn fixed_finite_workload(){let t=trace();for value in ["/usr/bin/python3.14","-I","-S","-B","/app/worker.py","--attempt"]{assert!(t.contains(&format!("s:{value}")));}for value in ["sudo","docker","virsh","bash"]{assert!(!t.contains(&format!("s:{value}")));}}
 #[test] fn retained_resource_bounds(){let p=properties(&"2".repeat(32),&"7".repeat(64));for (key,n) in [("RuntimeMaxUSec",20_000_000),("TimeoutStopUSec",2_000_000),("CPUQuotaPerSecUSec",500_000),("MemoryMax",268_435_456),("TasksMax",16)]{assert!(p.iter().any(|(k,v)|*k==key&&matches!(v,Value::U64(x) if *x==n)));}}
 #[test] fn encoder_containers_balanced(){let t=trace();let mut stack=vec![];for x in t{if x.starts_with("open:"){stack.push(x);}else if x=="close"{assert!(stack.pop().is_some());}}assert!(stack.is_empty());}
}
