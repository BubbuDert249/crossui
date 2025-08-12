import sys
sys.dont_write_bytecode = True

# Platform detection
def _detect_platform():
    if "ANDROID_ARGUMENT" in sys.argv or "ANDROID_DATA" in sys.argv or "ANDROID_BOOTLOGO" in sys.argv:
        return "android"
    import platform
    pf = platform.system().lower()
    if pf == "darwin":
        # Could be macOS or iOS - check ios
        try:
            import ui
            return "ios"
        except ImportError:
            return "macos"
    elif pf == "windows":
        return "windows"
    elif pf == "linux":
        # Check for pyodide or brython by globals
        try:
            import js
            return "pyodide"
        except ImportError:
            pass
        try:
            import browser
            return "brython"
        except ImportError:
            return "linux"
    return "unknown"

platform = _detect_platform()

# For storing widget refs and states
_widgets = {}
_textbox_value = ""
_checkbox_state = False
_dropdown_value = ""
_slider_value = 0
_timers = []
_interval = None

# --- Platform-specific UI init ---

if platform == "windows" or platform == "linux" or platform == "macos":
    import tkinter as tk
    from tkinter import messagebox, simpledialog

    _root = None
    _canvas = None

    def _init():
        global _root, _canvas
        if _root is None:
            _root = tk.Tk()
            _canvas = tk.Canvas(_root)
            _canvas.pack(fill="both", expand=True)
            _root.geometry("800x600")

    def drawtext(text, x, y, z, hexcolor):
        _init()
        _canvas.create_text(x, y, text=text, fill=hexcolor)

    def setbg(hexcolor):
        _init()
        _canvas.configure(bg=hexcolor)

    def drawimg(filename, x, y, z, width, height):
        from tkinter import PhotoImage
        _init()
        img = PhotoImage(file=filename)
        img = img.subsample(max(img.width()//width, 1), max(img.height()//height, 1))
        _canvas.create_image(x, y, image=img, anchor="nw")
        _widgets[f"img_{filename}"] = img  # keep ref

    def setwindowname(title):
        _init()
        _root.title(title)

    def setwindowicon(filename):
        _init()
        try:
            _root.iconbitmap(filename)
        except Exception:
            pass

    def setwindowsize(width, height):
        _init()
        _root.geometry(f"{width}x{height}")

    def setfullscreen(value):
        _init()
        _root.attributes("-fullscreen", value)

    def showmsgbox(title, message):
        _init()
        messagebox.showinfo(title, message)

    def addbutton(text, action, x, y, z):
        _init()
        btn = tk.Button(_root, text=text, command=action)
        btn.place(x=x, y=y)
        _widgets[f"button_{text}_{x}_{y}"] = btn

    def addtxtbox(x, y, z, width, height):
        global _textbox_value
        _init()
        entry = tk.Entry(_root, width=width)
        entry.place(x=x, y=y, width=width*10, height=height*20)
        _widgets["textbox"] = entry

    def txtinput():
        e = _widgets.get("textbox")
        if e:
            return e.get()
        return ""

    # New General UI commands:

    def addcheckbox(label, x, y, z):
        global _checkbox_state
        _init()
        var = tk.BooleanVar()
        chk = tk.Checkbutton(_root, text=label, variable=var)
        chk.var = var
        chk.place(x=x, y=y)
        _widgets["checkbox"] = chk

    def checkboxvalue():
        chk = _widgets.get("checkbox")
        if chk and hasattr(chk, "var"):
            return chk.var.get()
        return False

    def adddropdown(options, x, y, z):
        global _dropdown_value
        _init()
        opts = options.split(".%")
        var = tk.StringVar(_root)
        var.set(opts[0])
        dropdown = tk.OptionMenu(_root, var, *opts)
        dropdown.var = var
        dropdown.place(x=x, y=y)
        _widgets["dropdown"] = dropdown

    def dropdownvalue():
        dd = _widgets.get("dropdown")
        if dd and hasattr(dd, "var"):
            return dd.var.get()
        return ""

    def addslider(minimum, maximum, x, y, z):
        global _slider_value
        _init()
        var = tk.DoubleVar()
        slider = tk.Scale(_root, variable=var, from_=minimum, to=maximum, orient="horizontal", length=150)
        slider.var = var
        slider.place(x=x, y=y)
        _widgets["slider"] = slider

    def slidervalue():
        slider = _widgets.get("slider")
        if slider and hasattr(slider, "var"):
            return slider.var.get()
        return 0

    import threading
    import time

    def settimeout(seconds, action):
        def timer_func():
            time.sleep(seconds)
            action()
        threading.Thread(target=timer_func, daemon=True).start()

elif platform == "android":
    from kivy.app import App
    from kivy.uix.widget import Widget
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.image import Image
    from kivy.uix.textinput import TextInput
    from kivy.uix.checkbox import CheckBox
    from kivy.uix.spinner import Spinner
    from kivy.uix.slider import Slider
    from kivy.uix.popup import Popup
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.graphics import Color, Rectangle

    class CrossUIApp(App):
        def build(self):
            self.root = Widget()
            self.widgets = {}
            return self.root

        def drawtext(self, text, x, y, z, hexcolor):
            color = [int(hexcolor[i:i+2], 16)/255 for i in (1,3,5)] if hexcolor.startswith("#") else [1,1,1]
            lbl = Label(text=text, color=color, pos=(x, y), size_hint=(None,None))
            self.root.add_widget(lbl)
            self.widgets[f"text_{len(self.widgets)}"] = lbl

        def setbg(self, hexcolor):
            Window.clearcolor = tuple(int(hexcolor[i:i+2], 16)/255 for i in (1,3,5)) + (1,)

        def drawimg(self, filename, x, y, z, width, height):
            img = Image(source=filename, pos=(x, y), size=(width, height), size_hint=(None,None))
            self.root.add_widget(img)
            self.widgets[f"img_{filename}"] = img

        def setwindowname(self, title):
            pass  # Not supported on Android

        def setwindowicon(self, filename):
            pass  # Not supported on Android

        def setwindowsize(self, width, height):
            pass  # Not supported on Android

        def setfullscreen(self, value):
            Window.fullscreen = 'auto' if value else False

        def showmsgbox(self, title, message):
            popup = Popup(title=title, content=Label(text=message), size_hint=(.5, .5))
            popup.open()

        def addbutton(self, text, action, x, y, z):
            btn = Button(text=text, pos=(x, y), size_hint=(None,None))
            btn.bind(on_press=lambda instance: action())
            self.root.add_widget(btn)
            self.widgets[f"button_{text}"] = btn

        def addtxtbox(self, x, y, z, width, height):
            txt = TextInput(pos=(x, y), size=(width, height), size_hint=(None,None))
            self.root.add_widget(txt)
            self.widgets["textbox"] = txt

        def txtinput(self):
            txt = self.widgets.get("textbox")
            if txt:
                return txt.text
            return ""

        # New general UI commands for Android (Kivy):

        def addcheckbox(self, label, x, y, z):
            container = Widget(pos=(x,y), size_hint=(None,None))
            checkbox = CheckBox()
            checkbox.pos = (0, 0)
            lbl = Label(text=label, pos=(30, 0), size_hint=(None,None))
            container.add_widget(checkbox)
            container.add_widget(lbl)
            self.root.add_widget(container)
            self.widgets["checkbox"] = checkbox

        def checkboxvalue(self):
            chk = self.widgets.get("checkbox")
            if chk:
                return chk.active
            return False

        def adddropdown(self, options, x, y, z):
            opts = options.split(".%")
            spinner = Spinner(text=opts[0], values=opts, pos=(x, y), size_hint=(None,None))
            self.root.add_widget(spinner)
            self.widgets["dropdown"] = spinner

        def dropdownvalue(self):
            dd = self.widgets.get("dropdown")
            if dd:
                return dd.text
            return ""

        def addslider(self, minimum, maximum, x, y, z):
            slider = Slider(min=minimum, max=maximum, pos=(x, y), size_hint=(None,None), value=minimum)
            self.root.add_widget(slider)
            self.widgets["slider"] = slider

        def slidervalue(self):
            s = self.widgets.get("slider")
            if s:
                return s.value
            return 0

        def settimeout(self, seconds, action):
            Clock.schedule_once(lambda dt: action(), seconds)

    _app = None
    def _init():
        global _app
        if _app is None:
            _app = CrossUIApp()
            from threading import Thread
            Thread(target=_app.run, daemon=True).start()

    # proxy functions for Android

    def drawtext(text, x, y, z, hexcolor):
        _init()
        Clock.schedule_once(lambda dt: _app.drawtext(text, x, y, z, hexcolor))

    def setbg(hexcolor):
        _init()
        Clock.schedule_once(lambda dt: _app.setbg(hexcolor))

    def drawimg(filename, x, y, z, width, height):
        _init()
        Clock.schedule_once(lambda dt: _app.drawimg(filename, x, y, z, width, height))

    def setwindowname(title):
        pass

    def setwindowicon(filename):
        pass

    def setwindowsize(width, height):
        pass

    def setfullscreen(value):
        _init()
        Clock.schedule_once(lambda dt: _app.setfullscreen(value))

    def showmsgbox(title, message):
        _init()
        Clock.schedule_once(lambda dt: _app.showmsgbox(title, message))

    def addbutton(text, action, x, y, z):
        _init()
        Clock.schedule_once(lambda dt: _app.addbutton(text, action, x, y, z))

    def addtxtbox(x, y, z, width, height):
        _init()
        Clock.schedule_once(lambda dt: _app.addtxtbox(x, y, z, width, height))

    def txtinput():
        if _app is None:
            return ""
        return _app.txtinput()

    def addcheckbox(label, x, y, z):
        _init()
        Clock.schedule_once(lambda dt: _app.addcheckbox(label, x, y, z))

    def checkboxvalue():
        if _app is None:
            return False
        return _app.checkboxvalue()

    def adddropdown(options, x, y, z):
        _init()
        Clock.schedule_once(lambda dt: _app.adddropdown(options, x, y, z))

    def dropdownvalue():
        if _app is None:
            return ""
        return _app.dropdownvalue()

    def addslider(minimum, maximum, x, y, z):
        _init()
        Clock.schedule_once(lambda dt: _app.addslider(minimum, maximum, x, y, z))

    def slidervalue():
        if _app is None:
            return 0
        return _app.slidervalue()

    def settimeout(seconds, action):
        _init()
        Clock.schedule_once(lambda dt: action(), seconds)

elif platform == "ios":
    import ui
    import threading

    _window = None
    _textbox = None
    _checkbox = None
    _dropdown = None
    _slider = None
    _dropdown_options = []

    def _init():
        global _window
        if _window is None:
            _window = ui.View()
            _window.background_color = 'white'
            _window.frame = (0, 0, 375, 667)
            _window.present()

    def drawtext(text, x, y, z, hexcolor):
        _init()
        lbl = ui.Label()
        lbl.text = text
        lbl.text_color = ui.parse_color(hexcolor)
        lbl.frame = (x, y, 200, 30)
        _window.add_subview(lbl)

    def setbg(hexcolor):
        _init()
        _window.background_color = ui.parse_color(hexcolor)

    def drawimg(filename, x, y, z, width, height):
        _init()
        img = ui.ImageView()
        img.image = ui.Image.named(filename)
        img.frame = (x, y, width, height)
        _window.add_subview(img)

    def setwindowname(title):
        pass

    def setwindowicon(filename):
        pass

    def setwindowsize(width, height):
        pass

    def setfullscreen(value):
        pass

    def showmsgbox(title, message):
        _init()
        alert = ui.AlertController(title=title, message=message)
        alert.present('sheet')

    def addbutton(text, action, x, y, z):
        _init()
        btn = ui.Button(title=text)
        btn.frame = (x, y, 100, 40)
        btn.action = lambda sender: action()
        _window.add_subview(btn)

    def addtxtbox(x, y, z, width, height):
        global _textbox
        _init()
        _textbox = ui.TextField()
        _textbox.frame = (x, y, width, height)
        _window.add_subview(_textbox)

    def txtinput():
        if _textbox:
            return _textbox.text
        return ""

    def addcheckbox(label, x, y, z):
        global _checkbox
        _init()
        _checkbox = ui.Switch()
        _checkbox.frame = (x, y, 50, 30)
        _window.add_subview(_checkbox)
        lbl = ui.Label()
        lbl.text = label
        lbl.frame = (x+60, y, 100, 30)
        _window.add_subview(lbl)

    def checkboxvalue():
        if _checkbox:
            return _checkbox.value
        return False

    def adddropdown(options, x, y, z):
        global _dropdown, _dropdown_options
        _init()
        _dropdown_options = options.split(".%")
        _dropdown = ui.SegmentedControl()
        _dropdown.segments = _dropdown_options
        _dropdown.frame = (x, y, 200, 30)
        _window.add_subview(_dropdown)

    def dropdownvalue():
        if _dropdown:
            idx = _dropdown.selected_index
            if 0 <= idx < len(_dropdown_options):
                return _dropdown_options[idx]
        return ""

    def addslider(minimum, maximum, x, y, z):
        global _slider
        _init()
        _slider = ui.Slider()
        _slider.frame = (x, y, 200, 30)
        _slider.continuous = True
        _slider.value = minimum
        _slider.min_value = minimum
        _slider.max_value = maximum
        _window.add_subview(_slider)

    def slidervalue():
        if _slider:
            return _slider.value
        return 0

    import time

    def settimeout(seconds, action):
        def timer_func():
            time.sleep(seconds)
            action()
        threading.Thread(target=timer_func, daemon=True).start()
elif platform == "brython" or platform == "pyodide":
    from browser import document, html, timer  # Brython and Pyodide support this
    
    _widgets = {}

    def _init():
        # Nothing special needed for init on web
        pass

    def drawtext(text, x, y, z, hexcolor):
        span = html.SPAN(text, style=f"color:{hexcolor};position:absolute;left:{x}px;top:{y}px;z-index:{z};")
        document <= span
        _widgets[f"text_{len(_widgets)}"] = span

    def setbg(hexcolor):
        document.body.style.backgroundColor = hexcolor

    def drawimg(filename, x, y, z, width, height):
        img = html.IMG(src=filename, style=f"position:absolute;left:{x}px;top:{y}px;z-index:{z};width:{width}px;height:{height}px;")
        document <= img
        _widgets[f"img_{filename}"] = img

    def setwindowname(title):
        document.title = title

    def setwindowicon(filename):
        # Change favicon
        from browser import window
        link = document.select_one("link[rel~='icon']")
        if not link:
            link = html.LINK(rel="icon")
            document.head <= link
        link.attrs["href"] = filename

    def setwindowsize(width, height):
        # Not applicable in browser; could resize iframe or ignore
        pass

    def setfullscreen(value):
        # Request fullscreen or exit fullscreen for the document
        from browser import window
        doc = window.document
        if value:
            if hasattr(doc.documentElement, 'requestFullscreen'):
                doc.documentElement.requestFullscreen()
        else:
            if hasattr(doc, 'exitFullscreen'):
                doc.exitFullscreen()

    def showmsgbox(title, message):
        # Simple alert for now
        from browser import window
        window.alert(f"{title}\n\n{message}")

    def addbutton(text, action, x, y, z):
        btn = html.BUTTON(text, style=f"position:absolute;left:{x}px;top:{y}px;z-index:{z};")
        btn.bind("click", lambda ev: action())
        document <= btn
        _widgets[f"button_{text}"] = btn

    def addtxtbox(x, y, z, width, height):
        inp = html.INPUT(type="text", style=f"position:absolute;left:{x}px;top:{y}px;z-index:{z};width:{width}px;height:{height}px;")
        document <= inp
        _widgets["textbox"] = inp

    def txtinput():
        inp = _widgets.get("textbox")
        if inp:
            return inp.value
        return ""

    def addcheckbox(label, x, y, z):
        container = html.DIV(style=f"position:absolute;left:{x}px;top:{y}px;z-index:{z};")
        chk = html.INPUT(type="checkbox")
        lbl = html.LABEL(label)
        container <= chk + lbl
        document <= container
        _widgets["checkbox"] = chk

    def checkboxvalue():
        chk = _widgets.get("checkbox")
        if chk:
            return chk.checked
        return False

    def adddropdown(options, x, y, z):
        opts = options.split(".%")
        select = html.SELECT(style=f"position:absolute;left:{x}px;top:{y}px;z-index:{z};")
        for o in opts:
            option = html.OPTION(o)
            select <= option
        document <= select
        _widgets["dropdown"] = select

    def dropdownvalue():
        sel = _widgets.get("dropdown")
        if sel:
            return sel.value
        return ""

    def addslider(minimum, maximum, x, y, z):
        slider = html.INPUT(type="range", min=str(minimum), max=str(maximum), style=f"position:absolute;left:{x}px;top:{y}px;z-index:{z};")
        document <= slider
        _widgets["slider"] = slider

    def slidervalue():
        slider = _widgets.get("slider")
        if slider:
            try:
                return float(slider.value)
            except Exception:
                return 0
        return 0

    def settimeout(seconds, action):
        # Use browser.timer
        timer.set_timeout(action, int(seconds*1000))


else:
    # fallback dummy functions
    def drawtext(text, x, y, z, hexcolor):
        print(f"drawtext {text} at {x},{y},{z} with {hexcolor}")

    def setbg(hexcolor):
        print(f"setbg {hexcolor}")

    def drawimg(filename, x, y, z, width, height):
        print(f"drawimg {filename} at {x},{y},{z} size {width}x{height}")

    def setwindowname(title):
        print(f"setwindowname {title}")

    def setwindowicon(filename):
        print(f"setwindowicon {filename}")

    def setwindowsize(width, height):
        print(f"setwindowsize {width}x{height}")

    def setfullscreen(value):
        print(f"setfullscreen {value}")

    def showmsgbox(title, message):
        print(f"showmsgbox {title}: {message}")

    def addbutton(text, action, x, y, z):
        print(f"addbutton {text} at {x},{y},{z}")

    def addtxtbox(x, y, z, width, height):
        print(f"addtxtbox at {x},{y},{z} size {width}x{height}")

    def txtinput():
        return ""

    def addcheckbox(label, x, y, z):
        print(f"addcheckbox {label} at {x},{y},{z}")

    def checkboxvalue():
        return False

    def adddropdown(options, x, y, z):
        print(f"adddropdown {options} at {x},{y},{z}")

    def dropdownvalue():
        return ""

    def addslider(minimum, maximum, x, y, z):
        print(f"addslider {minimum}-{maximum} at {x},{y},{z}")

    def slidervalue():
        return 0

    def settimeout(seconds, action):
        import threading, time
        def timer_func():
            time.sleep(seconds)
            action()
        threading.Thread(target=timer_func, daemon=True).start()
