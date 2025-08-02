import tkinter as tk
from tkinter import filedialog, ttk
import os
import hashlib
from PIL import Image, ImageTk
from math import ceil
from collections import Counter
import math

class BinaryVisualizer:
    def __init__(self, root):
        self.root = root
        self.entropy_map = {}
        self.current_img = None
        self.colorscheme = {"bg": "#121212", "fg": "#eeeeee"}
        self.root.title("Binary Visualizer")
        self.root.geometry("860x720")
        self.build_ui()

    def build_ui(self):
        self.root.configure(bg=self.colorscheme["bg"])
        self.frame = ttk.Frame(self.root)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)

        top_frame = tk.Frame(self.frame, bg=self.colorscheme["bg"])
        top_frame.pack(fill="x")
        ttk.Button(top_frame, text="Open", command=self.open_file).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Export Image", command=self.export_image).pack(side="left", padx=5)

        self.canvas = tk.Canvas(self.frame, width=512, height=512, bg="black")
        self.canvas.pack(pady=10)
        self.canvas.bind("<Motion>", self.show_tooltip)

        self.meta = tk.Text(self.frame, height=6, wrap="word", bg=self.colorscheme["bg"], fg=self.colorscheme["fg"])
        self.meta.pack(fill="x", pady=(10, 0))

        self.tooltip = tk.Label(self.root, text="", bg="yellow", fg="black")
        self.tooltip.place_forget()

        self.root.bind("<Control-o>", lambda e: self.open_file())

    def open_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        with open(file_path, "rb") as f:
            data = f.read()

        img, entropy_map = self.create_bitmap(data)
        self.entropy_map = entropy_map
        self.display_image(img)
        self.display_metadata(file_path, data, entropy_map)
        self.current_img = img

    def create_bitmap(self, data, width=256, block_size=64):
        size = len(data)
        height = ceil(size / width)
        img = Image.new("RGB", (width, height))
        entropy_map = {}

        for i in range(size):
            byte = data[i]
            x = i % width
            y = i // width
            block = (x // (block_size // 2), y // (block_size // 2))
            img.putpixel((x, y), self.byte_to_color(byte))
            entropy_map.setdefault(block, []).append(byte)

        for key in entropy_map:
            entropy_map[key] = self.calculate_entropy(entropy_map[key])

        return img, entropy_map

    def byte_to_color(self, b):
        return ((b * 5) % 256, (b * 7) % 256, (b * 11) % 256)

    def calculate_entropy(self, data):
        if not data:
            return 0.0
        counter = Counter(data)
        total = len(data)
        entropy = -sum((count / total) * math.log2(count / total) for count in counter.values())
        return round(entropy, 4)

    def display_image(self, img):
        img = img.resize((512, 512), Image.NEAREST)
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    def display_metadata(self, path, data, entropy_map):
        sha256 = hashlib.sha256(data).hexdigest()
        avg_entropy = round(sum(entropy_map.values()) / len(entropy_map), 4)
        info = (
            f"📁 File: {os.path.basename(path)}\n"
            f"📏 Size: {len(data):,} Bytes\n"
            f"🔒 SHA256: {sha256[:32]}...\n"
            f"🧪 Entropy: {avg_entropy} bits/byte\n"
        )
        self.meta.delete("1.0", tk.END)
        self.meta.insert("1.0", info)

    def export_image(self):
        if self.current_img:
            export_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if export_path:
                self.current_img.save(export_path)

    def show_tooltip(self, event):
        x, y = event.x, event.y
        block_x = x // (512 // 64)
        block_y = y // (512 // 64)
        entropy = self.entropy_map.get((block_x, block_y)) if self.entropy_map else None
        if entropy:
            self.tooltip.config(text=f"Entropy: {entropy}")
            self.tooltip.place(x=event.x_root + 10, y=event.y_root + 10)
        else:
            self.tooltip.place_forget()

if __name__ == "__main__":
    root = tk.Tk()
    app = BinaryVisualizer(root)
    root.mainloop()
