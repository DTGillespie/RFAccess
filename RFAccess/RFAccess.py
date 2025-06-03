import ctypes
import os
import sys
from ctypes import c_char_p, c_int, c_void_p

if sys.platform.startswith('win'):
  lib_filename = "RFAccess.dll"
elif sys.platform.startswith('linux'):
  lib_filename = "libRFAccess.so"
elif sys.platform.startswith('darwin'):
  lib_filename = "libRFAccess.dylib"
else:
  raise OSError("Unsupported operating system")

_callback_refs = []
def protect_cb_gc(cb):
  _callback_refs.append(cb)
  return cb

lib_path = os.path.join(os.path.dirname(__file__), "bin", lib_filename)
RFAccess = ctypes.CDLL(lib_path)

__version__="1.0.1"

RFAccess.initialize_client.argtypes = [c_char_p]
RFAccess.initialize_client.restype = c_void_p

RFAccess.client_set_reader_capabilities_callback.argtypes = [c_void_p, ctypes.CFUNCTYPE(None, c_char_p)]
RFAccess.client_set_reader_capabilities_callback.restype = c_int

RFAccess.client_set_reader_config_callback.argtypes = [c_void_p, ctypes.CFUNCTYPE(None, c_char_p)]
RFAccess.client_set_reader_config_callback.restype = c_int

RFAccess.client_set_ro_access_report_callback.argtypes = [c_void_p, ctypes.CFUNCTYPE(None, c_char_p)]
RFAccess.client_set_ro_access_report_callback.restype = c_int

RFAccess.send_keep_alive.argtypes = [c_void_p]
RFAccess.send_keep_alive.restype = c_int

RFAccess.send_enable_events_and_reports.argtypes = [c_void_p]
RFAccess.send_enable_events_and_reports.restype = c_int

RFAccess.send_get_reader_capabilities.argtypes = [c_void_p]
RFAccess.send_get_reader_capabilities.restype = c_int

RFAccess.send_get_reader_config.argtypes = [c_void_p]
RFAccess.send_get_reader_config.restype = c_int

RFAccess.send_set_reader_config.argtypes = [c_void_p]
RFAccess.send_set_reader_config.restype = c_int

RFAccess.send_add_rospec.argtypes = [c_void_p]
RFAccess.send_add_rospec.restype = c_int

RFAccess.send_enable_rospec.argtypes = [c_void_p]
RFAccess.send_enable_rospec.restype = c_int

RFAccess.send_start_rospec.argtypes = [c_void_p]
RFAccess.send_start_rospec.restype = c_int

RFAccess.send_stop_rospec.argtypes = [c_void_p]
RFAccess.send_stop_rospec.restype = c_int

RFAccess.send_delete_rospec.argtypes = [c_void_p, c_int]
RFAccess.send_delete_rospec.restype = c_int

RFAccess.read_ro_access_report.argtypes = [c_void_p]
RFAccess.read_ro_access_report.restype = c_int

RFAccess.send_close_connection.argtypes = [c_void_p]
RFAccess.send_close_connection.restype = c_int

RFAccess.free_client.argtypes = [c_void_p]
RFAccess.free_client.restype = c_int

RFAccess.free_string.argtypes = [c_char_p]
RFAccess.free_string.restype = c_int

RFAccess.get_last_error.argtypes = []
RFAccess.get_last_error.restype = c_char_p

def get_dll_version():
  RFAccess.get_library_version.restype = ctypes.c_char_p
  return RFAccess.get_library_version().decode("utf-8")

def check_versions():

  dll_version = get_dll_version()

  repo_major_version = __version__.split('.')[0]
  dll_major_version  = dll_version.split('.')[0]

  if repo_major_version != dll_major_version:
    
    error_message = (
      "Incompatible version detected between RFAccess FFI & DLL:\n"
      f"  - RFAccess: {__version__}\n"
      f"  - DLL: {dll_version}\n"
      "Please ensure that the RFAccess Python package and DLL are compatible."
    )

    raise Exception(error_message)

def get_bin_path():
  cwd = os.path.dirname(os.path.abspath(__file__))
  return os.path.join(cwd, "bin", "win")

def get_last_error():
  error_ptr = RFAccess.get_last_error()
  if error_ptr:
    error = error_ptr.decode('utf-8')
    free_string(error_ptr)
    return error
  return None

def free_string(string_ptr):
  result = RFAccess.free_string(string_ptr)
  if result != 0:
    error = get_last_error()
    raise Exception(f"Error deallocating string pointer: {error}")

ReaderCapabilitiesCallback = ctypes.CFUNCTYPE(None, c_char_p)
ReaderConfigCallback       = ctypes.CFUNCTYPE(None, c_char_p)
ROAccessReportCallback     = ctypes.CFUNCTYPE(None, c_char_p)

class LLRPClient:

  def __init__(self, config_path: str):
    
    check_versions()

    if not os.path.isfile(config_path):
      raise FileNotFoundError(f"Configuration file not found: {config_path}")

    self._handle = RFAccess.initialize_client(config_path.encode("utf-8"))
    if not self._handle:
      error = get_last_error()
      raise Exception(f"Error initializing client: {error}")

  def set_reader_capabilities_callback(self, callback):
    self.reader_capabilities_callback = protect_cb_gc(ReaderCapabilitiesCallback(callback))
    result = RFAccess.client_set_reader_capabilities_callback(self._handle, self.reader_capabilities_callback)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error setting reader capabilities callback: {error}")

  def set_reader_config_callback(self, callback):
    self.reader_config_callback = protect_cb_gc(ReaderConfigCallback(callback))
    result = RFAccess.client_set_reader_config_callback(self._handle, self.reader_config_callback)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error setting reader config callback: {error}")

  def set_ro_access_report_callback(self, callback):
    self.ro_access_report_callback = protect_cb_gc(ROAccessReportCallback(callback))
    result = RFAccess.client_set_ro_access_report_callback(self._handle, self.ro_access_report_callback)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error setting RO access report callback: {error}")

  def send_keep_alive(self):
    result = RFAccess.send_keep_alive(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error sending KEEP_ALIVE: {error}")

  def send_enable_events_and_reports(self):
    result = RFAccess.send_enable_events_and_reports(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error sending ENABLE_EVENTS_AND_REPORTS: {error}")

  def send_get_reader_capabilities(self):
    result = RFAccess.send_get_reader_capabilities(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error sending GET_READER_CAPABILITIES: {error}")

  def send_get_reader_config(self):
    result = RFAccess.send_get_reader_config(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error sending GET_READER_CONFIG: {error}")

  def send_set_reader_config(self):
    result = RFAccess.send_set_reader_config(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error sending SET_READER_CONFIG: {error}")

  def send_add_rospec(self):
    result = RFAccess.send_add_rospec(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error sending ADD_RO_SPEC: {error}")

  def send_enable_rospec(self):
    result = RFAccess.send_enable_rospec(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error sending ENABLE_RO_SPEC: {error}")

  def send_start_rospec(self):
    result = RFAccess.send_start_rospec(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error sending START_RO_SPEC: {error}")

  def send_stop_rospec(self):
    result = RFAccess.send_stop_rospec(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error sending STOP_RO_SPEC: {error}")

  def send_delete_rospec(self, rospec_id: int):
    result = RFAccess.send_delete_rospec(self._handle, rospec_id)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error sending DELETE_RO_SPEC: {error}")

  def read_ro_access_report(self):
    result = RFAccess.read_ro_access_report(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error reading ROAccessReport: {error}")

  def send_close_connection(self):
    result = RFAccess.send_close_connection(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error sending CLOSE_CONNECTION: {error}")

  def free(self):
    result = RFAccess.free_client(self._handle)
    if result != 0:
      error = get_last_error()
      raise Exception(f"Error deallocating client pointer: {error}")
    self._handle = None