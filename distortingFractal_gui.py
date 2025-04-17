import math
import numpy as np
import tkinter as tk
from tkinter import colorchooser, filedialog
from PIL import Image, ImageDraw, ImageTk
import tkinter.messagebox as messagebox

def create_l_system(iters, axiom, rules):
    s = axiom
    for _ in range(iters):
        s = "".join(rules.get(ch, ch) for ch in s)
    return s

def calc_length_height(instructions, angle, corr):
    ca = corr; x= y= 0; min_x=min_y= 0; max_x=max_y= 0
    for inst in instructions:
        if inst=='F':
            x += math.cos(math.radians(ca)); y += math.sin(math.radians(ca))
        elif inst=='B':
            x -= math.cos(math.radians(ca)); y -= math.sin(math.radians(ca))
        elif inst=='+':
            ca -= angle
        elif inst=='-':
            ca += angle
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)
    return max_x-min_x, max_y-min_y, -min_x, -min_y

def draw_l_system_on_overlay(draw, instr, angle, step, start, corr, color, width):
    x,y = start; a = corr
    for c in instr:
        if c=='F':
            nx = x + step*math.cos(math.radians(a))
            ny = y + step*math.sin(math.radians(a))
            draw.line([(x,y),(nx,ny)], fill=color, width=width)
            x,y = nx,ny
        elif c=='B':
            nx = x - step*math.cos(math.radians(a))
            ny = y - step*math.sin(math.radians(a))
            draw.line([(x,y),(nx,ny)], fill=color, width=width)
            x,y = nx,ny
        elif c=='+': a -= angle
        elif c=='-': a += angle

def distort_image_with_fractal(image, overlay, amplitude):
    img_arr = np.array(image)
    over = np.array(overlay)[:,:,0].astype(np.float32)/255.0
    dx = (over-0.5)*amplitude; dy = dx
    h,w = over.shape
    gx,gy = np.meshgrid(np.arange(w), np.arange(h))
    nx = np.clip(np.round(gx+dx),0,w-1).astype(int)
    ny = np.clip(np.round(gy+dy),0,h-1).astype(int)
    out = img_arr[ny,nx]
    return Image.fromarray(out)

class FractalGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fractal Distorter")
        self.state("zoomed")  # start maximized
        self.input_path = None
        self.base_args()
        self.make_widgets()
        self.bind_events()

    def base_args(self):
        self.axiom = "FX+FX+FX"
        self.rules = {"X":"X+YF+","Y":"-FX-Y"}
        self.image = None
        self.show_overlay = False

    def make_widgets(self):
        frm = tk.Frame(self); frm.pack(side="left", fill="y", padx=10, pady=10)
        # load image
        tk.Button(frm, text="Open Image", command=self.open_image).pack(fill="x")
        # save image
        tk.Button(frm, text="Save Image", command=self.save_image).pack(fill="x", pady=(5,10))
        # toggle overlay
        self.show_overlay_var = tk.BooleanVar(value=self.show_overlay)
        tk.Checkbutton(frm,
                       text="Show Fractal Overlay",
                       variable=self.show_overlay_var,
                       command=self.update_preview
        ).pack(fill="x", pady=(5,10))

        self.vars = {}
        for name, cfg in [
            ("iterations", ("Iterations", 0, 20, 1, 15)),       # default 15 (defaults are the values I used)
            ("base_angle", ("Angle",      0, 360, 1, 90)),      # default 90
            ("correction", ("Corr Angle", 0, 360, 1, 45*7)),    # default 45*7 = 315
            ("margin",     ("Margin",     0, 200, 1, 0)),       # default 0
            ("center_x",   ("Center X",   0, 2000,1,590)),      # default 590
            ("center_y",   ("Center Y",   0, 2000,1,590)),      # default 590
            ("line_width", ("Line W",     1, 20,  1, 2)),       # default 2
            ("amplitude",  ("Amplitude",  0, 500, 1,100)),      # default 100
        ]:
            v = tk.StringVar(value=str(cfg[4]))
            self.vars[name] = v
            tk.Label(frm, text=cfg[0]).pack(anchor="w")
            tk.Entry(frm, textvariable=v).pack(fill="x", pady=2)

        # color picker
        self.vars["color"] = "#ff0000"
        tk.Button(frm, text="Line Color", command=self.choose_color).pack(fill="x", pady=(10,0))

        # canvas for preview (resizes with window)
        self.canvas = tk.Canvas(self, bg="grey")
        self.canvas.pack(side="right", expand=True, fill="both")
        # update preview on resize
        self.canvas.bind("<Configure>", lambda e: self.update_preview())

    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", ("*.png", "*.jpg", "*.jpeg")), ("All files","*.*")]
        )
        if path:
            self.input_path = path
            try:
                self.image = Image.open(path).convert("RGBA")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open image:\n{e}")
                return
            self.update_preview()

    def choose_color(self):
        c = colorchooser.askcolor(title="Pick line color", initialcolor=self.vars["color"])
        if c[1]:
            self.vars["color"] = c[1]
            self.update_preview()

    def bind_events(self):
        for v in self.vars.values():
            if isinstance(v, tk.Variable):
                v.trace_add("write", lambda *a: self.update_preview())

    def update_preview(self):
        if not self.image:
            return

        # parse entry values
        try:
            it = int(self.vars["iterations"].get())
            ba = float(self.vars["base_angle"].get())
            ca = float(self.vars["correction"].get())
            m  = float(self.vars["margin"].get())
            cx = float(self.vars["center_x"].get())
            cy = float(self.vars["center_y"].get())
            lw = int(self.vars["line_width"].get())
            amp= float(self.vars["amplitude"].get())
        except ValueError:
            return  # invalid numeric input

        col = self.vars["color"]

        instr = create_l_system(it, self.axiom, self.rules)
        fw, fh, offx, offy = calc_length_height(instr, ba, ca)
        iw, ih = self.image.size
        sx = (iw - 2*m) / fw if fw else 1
        sy = (ih - 2*m) / fh if fh else 1
        step = min(sx, sy)

        overlay = Image.new("RGBA", self.image.size, (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        draw_l_system_on_overlay(draw, instr, ba, step, (cx, cy), ca, col, lw)

        out = distort_image_with_fractal(self.image, overlay, amp)
        self.result_image = out

        # choose preview: overlay on original vs distorted
        if self.show_overlay_var.get():
            preview = self.image.convert("RGBA")
            preview.paste(overlay, (0,0), overlay)
        else:
            preview = out

        # scale to fit canvas, preserving aspect ratio
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 2 or ch < 2:
            return
        iw, ih = preview.size
        scale = min(cw/iw, ch/ih)
        nw, nh = int(iw*scale), int(ih*scale)
        resized = preview.resize((nw, nh), resample=Image.LANCZOS)

        # center on canvas
        self.tkimg = ImageTk.PhotoImage(resized)
        self.canvas.delete("all")
        self.canvas.create_image(cw//2, ch//2, image=self.tkimg, anchor="center")

    def save_image(self):
        """Export the current full-quality image to disk."""
        if not hasattr(self, "result_image"):
            messagebox.showwarning("No Image", "Nothing to save yet.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image","*.png"),("JPEG","*.jpg;*.jpeg"),("All files","*.*")]
        )
        if path:
            try:
                self.result_image.save(path)
                messagebox.showinfo("Saved", f"Image saved as:\n{path}")
            except Exception as e:
                messagebox.showerror("Error Saving", str(e))

if __name__ == "__main__":
    app = FractalGUI()
    app.mainloop()