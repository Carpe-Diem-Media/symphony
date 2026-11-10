"""Root-only fixed native session. No caller commands, unit or property API."""
from enum import Enum
import os,select,subprocess,time
from pathlib import Path
from contract import ROOT,Refusal,require

EXECUTOR=Path(ROOT)/'executor'
class NativeOperation(Enum):
 CREATE='CREATE'
 SHOW='SHOW'
 STOP='STOP'
 UNREF='UNREF'
 CLOSE='CLOSE'

def parse_frame(raw):
 require(type(raw) is bytes and 0<len(raw)<=32768 and raw.endswith(b'END\n') and b'\r' not in raw,'NATIVE_REPLY_INVALID')
 result={}
 try:
  for line in raw[:-4].decode('ascii').splitlines():
   key,sep,value=line.partition('=')
   require(sep and key and key not in result and '\r' not in value,'NATIVE_REPLY_INVALID');result[key]=value
 except UnicodeError:raise Refusal('NATIVE_REPLY_INVALID') from None
 require(result,'NATIVE_REPLY_INVALID');return result

class NativeExecutor:
 def __init__(self):
  require(os.geteuid()==0,'HOST_ROOT_REQUIRED')
  # Caller verifies exact root-owned tool/runtime identities before construction.
  self.process=subprocess.Popen([str(EXECUTOR),'--session'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
   env={'PATH':'/nonexistent','HOME':'/nonexistent','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'},close_fds=True,start_new_session=True)
 def exchange(self,operation):
  require(type(operation) is NativeOperation,'HOST_COMMAND_INVALID')
  require(self.process.poll() is None,'NATIVE_EXECUTOR_LOST')
  try:
   self.process.stdin.write(operation.value.encode('ascii')+b'\n');self.process.stdin.flush()
   deadline=time.monotonic()+5;raw=bytearray()
   while len(raw)<=32768 and time.monotonic()<deadline:
    if not select.select([self.process.stdout],[],[],max(0,deadline-time.monotonic()))[0]:break
    chunk=os.read(self.process.stdout.fileno(),1)
    if not chunk:break
    raw.extend(chunk)
    if raw.endswith(b'END\n'):return parse_frame(bytes(raw))
   raise Refusal('NATIVE_EXECUTOR_UNCERTAIN')
  except (BrokenPipeError,OSError):raise Refusal('NATIVE_EXECUTOR_LOST') from None
 def close(self):
  error=None
  try:
   if self.process.poll() is None:self.exchange(NativeOperation.CLOSE)
  except BaseException as caught:error=caught
  finally:
   self.process.stdin.close()
   try:out,err=self.process.communicate(timeout=3)
   except ValueError:
    # communicate cannot flush a deliberately closed stdin.
    self.process.stdin=None
    try:out,err=self.process.communicate(timeout=3)
    except subprocess.TimeoutExpired:
     self.process.kill();out,err=self.process.communicate(timeout=3);error=Refusal('NATIVE_EXECUTOR_UNCERTAIN')
   except subprocess.TimeoutExpired:
    self.process.kill();out,err=self.process.communicate(timeout=3);error=Refusal('NATIVE_EXECUTOR_UNCERTAIN')
   self.terminal={'exit_code':self.process.returncode,'remaining_stdout':out.decode('ascii',errors='replace'),'stderr':err.decode('ascii',errors='replace'),'reaped':self.process.poll() is not None}
  if error:raise error
  require(self.process.returncode==0,'NATIVE_EXECUTOR_UNCERTAIN')
