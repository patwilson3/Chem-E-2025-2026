import tkinter as tk
import threading
import queue


class Dashboard:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._queue = queue.Queue()
        self._root = tk.Tk()
        self._root.title("Dashboard")
        self._root.geometry("800x500")
        self._root.configure(bg="#1e1e1e")

        # --- Car Speed ---
        self._make_header(self._root, "Car Speed", row=0)
        self._speed_var = tk.StringVar(value="0 mph")
        self._make_label(self._root, self._speed_var, row=1)

        # --- ORP Data ---
        self._make_header(self._root, "ORP Data", row=2)
        self._orp_var = tk.StringVar(value="waiting for data...")
        self._make_label(self._root, self._orp_var, row=3)
        self._alg_var = tk.StringVar(value="Alg Status: IDLE")
        self._make_label(self._root, self._alg_var, row=4)

        # --- Battery Data ---
        self._make_header(self._root, "Battery Data", row=5)
        self._battery_var = tk.StringVar(value="waiting for data...")
        self._make_label(self._root, self._battery_var, row=6)

        # --- Button Status ---
        self._make_header(self._root, "Button Status", row=7)
        self._start_var = tk.StringVar(value="Start: READY")
        self._reset_var = tk.StringVar(value="Reset: IDLE")
        self._make_label(self._root, self._start_var, row=8)
        self._make_label(self._root, self._reset_var, row=9)

        self._poll()

    def _make_header(self, parent, text, row):
        lbl = tk.Label(parent, text=text, font=("Courier", 18, "bold"),
                       fg="#00ff99", bg="#1e1e1e")
        lbl.grid(row=row, column=0, sticky="w", padx=20, pady=(15, 0))

    def _make_label(self, parent, var, row):
        lbl = tk.Label(parent, textvariable=var, font=("Courier", 14),
                       fg="white", bg="#1e1e1e", justify="left", anchor="w")
        lbl.grid(row=row, column=0, sticky="w", padx=40, pady=(0, 5))

    def _poll(self):
        """Drain the queue on the main thread, then reschedule."""
        while not self._queue.empty():
            var, value = self._queue.get_nowait()
            var.set(value)
        self._root.after(50, self._poll)

    # ---- public update methods (thread-safe) ----

    def update_speed(self, speed):
        self._queue.put((self._speed_var, f"{speed} mph"))

    def update_orp(self, mvs, std, rot, time_s):
        text = (f"mvs: {float(mvs):.3f}   std: {float(std):.3f}\n"
                f"rot: {float(rot):.3f}   time: {float(time_s):.3f}s")
        self._queue.put((self._orp_var, text))

    def update_battery(self, volt, m_amp):
        text = f"{volt:.4f} volts   {m_amp:.4f} mA"
        self._queue.put((self._battery_var, text))

    def update_alg(self, status):
        self._queue.put((self._alg_var, f"Alg Status: {status}"))

    def update_start(self, status):
        self._queue.put((self._start_var, f"Start: {status}"))

    def update_reset(self, status):
        self._queue.put((self._reset_var, f"Reset: {status}"))

    def run(self):
        """Call from the main thread. Blocks until window is closed."""
        self._root.mainloop()


# ---- quick demo ----
if __name__ == "__main__":
    dash = Dashboard()

    def fake_hw():
        import time
        t = 0.0
        while True:
            dash.update_orp(mvs=123.456 + t, std=0.789, rot=1.234, time_s=t)
            dash.update_battery(volt=12.345, m_amp=450.678 + t)
            dash.update_speed(round(t, 1))
            time.sleep(0.2)
            t += 0.2

    threading.Thread(target=fake_hw, daemon=True).start()
    dash.run()
