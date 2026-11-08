import math
import time
import tkinter as tk

DURATION, FPS = 3.2, 60
BG, BLUE, GREY, GREY_LIGHT, GREY_DARK, INK = "#f0f1ef", "#1f79ae", "#747a80", "#a9adb1", "#494f54", "#202323"


def play_intro(root, on_complete=None):
    """Play the Focused Up intro in a frame covering all of `root`.

    The frame destroys itself when finished, then calls `on_complete`.
    Returns the frame.
    """
    frame = tk.Frame(root, bg=BG)
    frame.place(x=0, y=0, relwidth=1, relheight=1)
    frame.lift()
    cv = tk.Canvas(frame, bg=BG, highlightthickness=0)
    cv.pack(fill="both", expand=True)

    clamp = lambda v, lo=0.0, hi=1.0: max(lo, min(hi, v))
    ease_out = lambda v: 1 - (1 - clamp(v)) ** 3
    ease_io = lambda v: clamp(v) ** 2 * (3 - 2 * clamp(v))
    phase = lambda e, a, b: clamp((e - a) / (b - a))

    def mix(c1, c2, t):
        return "#{:02x}{:02x}{:02x}".format(*(round(a + (b - a) * clamp(t)) for a, b in zip(c1, c2)))

    def arrow_color(y):
        n = clamp((y - 29) / 253)
        if n <= 0.48:
            return mix((228, 223, 105), (222, 138, 56), n / 0.48)
        return mix((222, 138, 56), (217, 72, 43), (n - 0.48) / 0.52)

    def rotate(p, o, deg):
        r, (x, y), (ox, oy) = math.radians(deg), p, o
        c, s = math.cos(r), math.sin(r)
        return ox + (x - ox) * c - (y - oy) * s, oy + (x - ox) * s + (y - oy) * c

    def lock_xf(p, t):
        tx, ty, ang = 128.0, -8.0, 0.0
        if t >= 0.22:
            ang = -45 * ease_io(phase(t, 0.22, 0.38))
        if t >= 0.38:
            k = ease_io(phase(t, 0.38, 0.58))
            tx, ty, ang = 128 * (1 - k), -8 * (1 - k), -45 * (1 - k)
        if t > 0.58:
            tx = ty = 0.0
            st = phase(t, 0.58, 1.0)
            ang = math.sin(st * math.pi * 5) * 8 * (1 - st)
        x, y = rotate(p, (240, 194), ang)
        return x + tx, y + ty

    def draw(elapsed):
        w, h = cv.winfo_width(), cv.winfo_height()
        s = min(w / 520, h / 430)
        ox, oy = (w - 420 * s) / 2, (h - 360 * s) / 2
        pt = lambda x, y: (ox + x * s, oy + y * s)
        flat = lambda pts: [c for p in pts for c in pt(*p)]
        poly = lambda pts, **kw: cv.create_polygon(flat(pts), **kw)
        n = elapsed / DURATION

        def band(x0, x1, y, off, height=1, **kw):
            poly([(x0, y + off), (x1, y + off), (x1, y + height + off), (x0, y + height + off)],
                 fill=arrow_color(y), outline="")

        def arrow(prog, layer):
            if prog <= 0:
                return
            off = (1 - ease_out(prog)) * 112
            if layer == "back":
                for y in range(94, 282):
                    band(130, 188, y, off)
                return
            for y in range(29, 93):
                hw = 57 * ((y - 29) / 64)
                poly([(159 - hw, y + off), (159 + hw, y + off),
                      (159 + hw + 1, y + 1 + off), (159 - hw - 1, y + 1 + off)],
                     fill=arrow_color(y), outline="")
            for a, b in ((93, 160), (215, 282)):
                for y in range(a, b):
                    band(130, 188, y, off)

        def f_upper(prog):
            r = (1 - ease_out(prog)) * 8
            top = [(94, 74 + r), (270, 74 + r), (270, 128 + r), (94, 128 + r)]
            spine = [(94, 74 + r), (163, 74 + r), (163, 282 + r), (94, 282 + r)]
            poly(top, fill=BLUE, outline=BLUE, width=0,
                 stipple="" if prog > 0.55 else "gray50")
            poly(spine, fill=BLUE, outline=BLUE, width=0,
                 stipple="" if prog > 0.55 else "gray50")

        def f_lower(prog):
            r = (1 - ease_out(prog)) * 8
            ledge = [(163, 160 + r), (244, 160 + r), (244, 215 + r), (163, 215 + r)]
            poly(ledge, fill=BLUE, outline=BLUE, width=0,
                 stipple="" if prog > 0.55 else "gray50")

        def lock(t):
            if t <= 0:
                return
            if t < 0.12:
                lift = 0
            elif t < 0.28:
                lift = 25 * ease_out(phase(t, 0.12, 0.28))
            elif t < 0.58:
                lift = 25
            else:
                lift = 25 * (1 - ease_out(phase(t, 0.58, 0.66)))
            arc = [(240 + 27 * math.cos(math.pi - math.pi * i / 18),
                    208 - 27 * math.sin(math.pi - math.pi * i / 18)) for i in range(19)]
            sh = [lock_xf((x, y - lift), t) for x, y in [(213, 228), *arc, (267, 228)]]
            cv.create_line(flat(sh), fill=GREY_LIGHT, width=max(4, round(14 * s)),
                           capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True)
            poly([(163, 160), (244, 160), (244, 215), (163, 215)], fill=BLUE, outline="")
            body = [lock_xf(p, t) for p in [(203, 221), (278, 221), (278, 287), (203, 287)]]
            poly(body, fill=GREY, outline=GREY_DARK, width=max(1, round(3 * s)))
            line = lambda a, b, col, wd: cv.create_line(
                *pt(*lock_xf(a, t)), *pt(*lock_xf(b, t)), fill=col, width=wd, capstyle=tk.ROUND)
            line((216, 235), (247, 235), "#aeb1b3", max(2, round(4 * s)))
            kx, ky = pt(*lock_xf((240.5, 250), t))
            r = 6 * s
            cv.create_oval(kx - r, ky - r, kx + r, ky + r, fill="#272b2e", outline="")
            line((240.5, 256), (240.5, 271), "#272b2e", max(2, round(5 * s)))

        def motto(prog):
            if prog <= 0:
                return
            a = ease_out(prog)
            x, y = pt(139, 326 + (1 - a) * 10)
            cv.create_text(x, y, text="FOCUSED UP AND LOCKED IN",
                           fill=INK if a > 0.45 else "#737775",
                           font=("Arial", max(9, round(12 * s)), "bold"), anchor="center")

        cv.delete("all")
        ap = phase(n, 0.15, 0.38)
        f_upper(phase(n, 0.0, 0.14))
        arrow(ap, "front")
        f_lower(phase(n, 0.0, 0.14))
        lock(phase(n, 0.38, 0.9))
        motto(phase(n, 0.82, 1.0))

    start = time.perf_counter()

    def tick():
        if not frame.winfo_exists():
            return
        elapsed = min(time.perf_counter() - start, DURATION)
        draw(elapsed)
        if elapsed >= DURATION:
            root.after(200, finish)
        else:
            root.after(round(1000 / FPS), tick)

    def finish():
        if frame.winfo_exists():
            frame.destroy()
        if on_complete:
            on_complete()

    root.after(250, tick)
    return frame


if __name__ == "__main__":
    r = tk.Tk()
    r.geometry("900x700")
    tk.Label(r, text="Main app").pack(expand=True)
    play_intro(r, on_complete=lambda: print("done"))
    r.mainloop()
