from kivy.app import App
from kivymd.app import MDApp
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.logger import Logger
from kivy.uix.button import Button
from kivy.properties import ListProperty

import kivy
import os
import utils
import time
import numpy as np
from io import BytesIO
from functools import partial, reduce
from dataclasses import dataclass
from collections import defaultdict, Counter
import intervaltree
from kivy import platform
from os import walk
from urllib.parse import unquote

from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
import kivy.uix.image
from PIL import Image, ImageOps, ImageDraw
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivymd.uix.filemanager.filemanager import MDFileManager

from android.storage import primary_external_storage_path
from android.storage import secondary_external_storage_path
from android import activity

if platform == "android":
    from jnius import cast
    from jnius import autoclass
    from android import mActivity, api_version

print(dir(utils))

files_path = ""

def get_display_metrics():
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    activity = PythonActivity.mActivity
    displayMetrics = activity.getContext().getResources().getDisplayMetrics()
    print(displayMetrics.widthPixels)
    print(displayMetrics.heightPixels)
    print(displayMetrics.widthPixels / displayMetrics.density)
    print(displayMetrics.heightPixels / displayMetrics.density)

def get_display_width():
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    activity = PythonActivity.mActivity
    displayMetrics = activity.getContext().getResources().getDisplayMetrics()
    return displayMetrics.widthPixels


def permissions_callback(permissions, grant_results):
    if permissions and all(grant_results):
        Logger.info("Runtime permissions: granted %s", permissions)
    else:
        Logger.error("Runtime permissions: not granted, %s", permissions)

def ask_permission(permissions):
    request_permissions(permissions, callback=permissions_callback)

if platform == "android":
    from android.permissions import request_permissions, Permission, check_permission  # pylint: disable=import-error # type: ignore
    ##ask_permission([Permission.READ_MEDIA_IMAGES, Permission.READ_MEDIA_AUDIO, Permission.READ_MEDIA_VIDEO, Permission.READ_EXTERNAL_STORAGE])
    ask_permission([Permission.READ_EXTERNAL_STORAGE])

def permissions_external_storage():                  
    if platform == "android":
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Environment = autoclass("android.os.Environment")
        Intent = autoclass("android.content.Intent")
        Settings = autoclass("android.provider.Settings")
        Uri = autoclass("android.net.Uri")
        if api_version > 29:
            # If you have access to the external storage, do whatever you need
            if Environment.isExternalStorageManager():

                # If you don't have access, launch a new activity to show the user the system's dialog
                # to allow access to the external storage
                pass
            else:
                try:
                    activity = mActivity.getApplicationContext()
                    uri = Uri.parse("package:" + activity.getPackageName())
                    intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION, uri)
                    #intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, uri)
                    currentActivity = cast(
                    "android.app.Activity", PythonActivity.mActivity
                    )
                    currentActivity.startActivityForResult(intent, 101)
                except:
                    intent = Intent()
                    intent.setAction(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION)
                    currentActivity = cast(
                    "android.app.Activity", PythonActivity.mActivity
                    )
                    currentActivity.startActivityForResult(intent, 101)


def on_activity_result(request, response, data):
    global files_path
    print(files_path)
    #file_f = data.getStringExtra("path")
    #print(file_f)
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    p_activity = PythonActivity.mActivity
    context = cast('android.content.ContextWrapper', p_activity.getApplicationContext())
    uri = data.getData()
    uri_path = unquote(uri.toString())
    pos = uri_path.rfind("/")
    filename = uri_path[pos+1:]
    inp_stream = context.getContentResolver().openInputStream(uri)
    Files = autoclass("java.nio.file.Files")
    StandardCopyOption = autoclass("java.nio.file.StandardCopyOption")

    File = autoclass("java.io.File")
    target_file = File(files_path + "/app/" + filename)
    Files.copy(inp_stream, target_file.toPath(), StandardCopyOption.REPLACE_EXISTING)



##permissions_external_storage()



@dataclass
class FlowItem:
    x: int
    y: int
    width: int
    height: int
    baseline: int
    linenumber: int


def get_baselines(new_lines):
    baselines = []
    for i in range(len(new_lines)):
        freqs , vals = np.histogram([nl[3] for nl in new_lines[i]])
        ind = np.argmax(freqs)
        bl = int((vals[ind] + vals[ind+1])/2)
        baselines.append(bl)
    return baselines

def find_runs(x):
    """Find runs of consecutive items in an array."""

    # ensure array
    x = np.asanyarray(x)
    if x.ndim != 1:
        raise ValueError('only 1D array supported')
    n = x.shape[0]

    # handle empty array
    if n == 0:
        return np.array([]), np.array([]), np.array([])

    else:
        # find run starts
        loc_run_start = np.empty(n, dtype=bool)
        loc_run_start[0] = True
        np.not_equal(x[:-1], x[1:], out=loc_run_start[1:])
        run_starts = np.nonzero(loc_run_start)[0]

        # find run values
        run_values = x[loc_run_start]

        # find run lengths
        run_lengths = np.diff(np.append(run_starts, n))

        return run_values, run_starts, run_lengths


def flow_step(new_w, indent_width, indents, state):
    indents_processed = dict()

    def inner_flow_step(_, b):
        w, d, line_counter, i, fi, d_indents = state
        if indents[b.linenumber] > 0 and not indents_processed.get(b.linenumber, False):
            line_counter += 1
            state[2] = line_counter
            d[line_counter].append(b)
            d_indents[line_counter] = True
            indents_processed[b.linenumber] = True
            state[0] = 2*indent_width + b.width
        else:
            if w+b.width <= (new_w - indent_width):
                d[line_counter].append(b)
                state[0] += b.width
                if indents[b.linenumber] == 2:
                    if i < len(fi)-2:
                        next_item = fi[i+2]
                        if next_item.linenumber > b.linenumber:
                            line_counter += 1
                            state[2] = line_counter
                            state[0] = 2*indent_width
                            d_indents[line_counter] = True
                            indents_processed[next_item.linenumber] = True
            else:
                line_counter += 1
                state[2] = line_counter
                d[line_counter].append(b)
                state[0] = indent_width + b.width

        state[3] += 1

    return inner_flow_step


def prepare_flow(img):
    img_gray = img.convert("L")
    threshold = 100
    img_b = img_gray.point(lambda p: 255 if p > threshold else 0)
    img_i = ImageOps.invert(img_b)
    structure = np.ones((3, 3), dtype=np.int8)
    # label separate components
    labeled, _ = utils.label(img_i, structure)
    ll = defaultdict(list)
    nz = np.nonzero(labeled)
    ln = len(nz[0])

    for i in range(ln):
        a = nz[0][i]
        b = nz[1][i]
        ll[labeled[a][b]].append([a, b])
    rects = []
    for k in ll:
        c = np.array(ll[k])
        ymin = np.min(c[:, 0])
        ymax = np.max(c[:, 0])
        xmin = np.min(c[:, 1])
        xmax = np.max(c[:, 1])
        rects.append((xmin, xmax, ymin, ymax))

    w, h = img.size
    d = defaultdict(list)
    for r in rects:
        if (r[2] != r[3]):
            d[(r[2], r[3])].append(r)
    tr = intervaltree.IntervalTree.from_tuples(d.keys())

    heights = np.array([x[3]-x[2] for x in rects])
    widths = np.array([x[1]-x[0] for x in rects])
    mean_h = np.mean(heights)
    mean_w = np.mean(widths)

    ints = []
    for i in range(h):
        ints.append(len(tr.at(i)))

    ys = utils.find_peaks(ints, distance=1.5*mean_h)[0]

    all_lines = []
    for y in ys:
        line = []
        for z in [d[(x.begin, x.end)] for x in tr.at(y)]:
            line.extend(z)
        all_lines.append(line)

    limits = []
    limits_set = set()
    for lin in all_lines:
        lower = np.min([r[2] for r in lin])
        upper = np.max([r[3] for r in lin])
        if not (lower, upper) in limits_set:
            limits.append((lower, upper))
            limits_set.add((lower, upper))

    new_lines = []
    for lim in limits:
        intvs = tr.overlap(lim[0], lim[1])
        new_line = []
        for z in [d[(x.begin, x.end)] for x in intvs]:
            new_line.extend(z)
        new_lines.append(sorted(new_line, key=lambda x: x[0]))

    # detect and correct low lines

    ratios = []
    max_value_args = []
    for line in new_lines:
        hs = [r[3]-r[2] for r in line]
        m = np.max(hs)
        max_value_args.append(np.argwhere(hs == m)[0][0])
        ratios.append(np.round(np.max(hs) / np.mean(hs), 1))

    common_ratio, _ = Counter(ratios).most_common(1)[0]
    to_correct_inds = [x[0] for x in np.argwhere(ratios < common_ratio)]

    for i, line in enumerate(new_lines):
        if i in to_correct_inds:
            x1, x2, y1, y2 = line[max_value_args[i]]
            r = ratios[i]
            coef = 1.1 * common_ratio / r
            line[max_value_args[i]] = (x1, x2, y2 - int(coef*(y2 - y1)), y2)

    # end detecting

    new_limits = []
    for lin in new_lines:
        new_lower = np.min([r[2] for r in lin])
        new_upper = np.max([r[3] for r in lin])
        new_limits.append((new_lower, new_upper))

    v_limits = []
    for i, lim in enumerate(new_limits):
        ymin, ymax = new_limits[i]
        line_b = img_i.crop((0, ymin, w, ymax))
        np_line = np.array(line_b)
        rv, rs, rl = find_runs(np.sum(np_line, axis=0))
        zero_inds = np.where(rv == 0)[0]
        A = rs[zero_inds]
        B = rs[zero_inds] + rl[zero_inds]
        C = []
        for element in zip(A, B):
            C.extend(element)
        v_limits.append(C)
    baselines = get_baselines(new_lines)

    flow_items = []
    left_spaces = []
    for i, l in enumerate(new_limits):
        lower, upper = l
        height = upper - lower
        v_limit = v_limits[i]
        baseline = baselines[i]
        vlen = len(v_limit)
        for k, p in enumerate(zip(v_limit[:-1], v_limit[1:])):
            xmin, xmax = p
            width = xmax - xmin
            if k == 0:
                left_spaces.append(width)
            elif k != vlen-2:
                flow_items.append(FlowItem(xmin, lower, width, height, upper - baseline, i))
            else:
                flow_items.append(FlowItem(xmin, lower, int(0.5*mean_w), height, upper - baseline, i))

    common_left_space, _ = Counter([ls for ls in left_spaces]).most_common(1)[0]
    indents = dict()
    for i, s in enumerate(left_spaces):
        if abs(s - common_left_space) > 5*mean_w:
            indents[i] = 2
        elif abs(s - common_left_space) > 0.3*mean_w:
            indents[i] = 1
        else:
            indents[i] = 0

    return int(5*mean_w), flow_items, w, indents, mean_h


def reflow(img, indent_width, flow_items, w, indents, mean_h):
    new_w = int(0.8 * w)
    state = [indent_width, defaultdict(list), 0, 0, flow_items, dict()]
    reduce(flow_step(new_w, indent_width, indents, state), flow_items, None)
    new_h = int((state[2] * 3 + 15) * mean_h)
    line_count = state[2]
    reflowed_lines = state[1]
    d_indents = state[5]
    newimage = Image.new(mode='RGB', size=(new_w, new_h), color='white')

    y = int(3 * mean_h)
    line_h = int(3*mean_h)
    x = indent_width

    for line_num in range(line_count+1):
        reflowed_line = reflowed_lines[line_num]
        for k, s in enumerate(reflowed_line):
            if k == 0 and d_indents.get(line_num, False):
                x += int(0.2*indent_width)

            letter_img = img.crop((s.x, s.y, s.x + s.width, s.y + s.height))
            newimage.paste(letter_img, (x, y + line_h + s.baseline - s.height))
            x += s.width
        x = indent_width
        if line_num < line_count:
            line_to_check = reflowed_lines[line_num+1]
            max_height = np.max([x.height for x in line_to_check])
            y += int(3 * mean_h) if 3*mean_h > max_height else int(max_height)
        else:
            y += int(3 * mean_h)
    return newimage

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

    def get_storage_path(self):

        pp = primary_external_storage_path()
        sp = secondary_external_storage_path()
        print(pp)
        print(sp)
        if pp is None:
            return sp
        return pp


class Root(FloatLayout):
    loadfile = ObjectProperty(None)
    text_input = ObjectProperty(None)
    image = ObjectProperty(None)
    pageno = 0
    scheduled_event = None
    filename = None
    reflowed = False


    def dismiss_popup(self):
        self._popup.dismiss()

    def handle_selection(self, selection):
        print("SELECTION = ")
        print(selection)
        self.load(selection, selection)


    def show_load(self):
        #from plyer import filechooser
        #filechooser.open_file(on_selection = self.handle_selection)
        #print("PATH:")
        #print(path)
        #path = primary_external_storage_path()
        #self.file_manager = MDFileManager(exit_manager=self.exit_file_manager, select_path=self.select_path)
        #self.file_manager.show(path)
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def add(self):
        global files_path
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        p_activity = PythonActivity.mActivity
        context = cast('android.content.ContextWrapper', p_activity.getApplicationContext())
        file_f = cast('java.io.File', context.getFilesDir())
        print(file_f.getAbsolutePath())
        files_path = file_f.getAbsolutePath()

        Intent = autoclass("android.content.Intent")
        aIntent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        aIntent.putExtra("path", file_f.getAbsolutePath())
        aIntent.addCategory(Intent.CATEGORY_OPENABLE);
        aIntent.setType("*/*")
        activity.bind(on_activity_result=on_activity_result)
        p_activity.startActivityForResult(aIntent, 42)


    def load(self, path, filename):
        print(filename)
        self.filename = filename[0]
        page_width = get_display_width()
        b = utils.get_page_for_display(self.pageno, filename[0], page_width)
        w, h = utils.get_page_size_for_display(self.pageno, filename[0], page_width)
        print(w,h)
        img = Image.frombytes("RGBA", (w, h), b)
        data = BytesIO()
        img.save(data, format='png')
        data.seek(0)
        im = CoreImage(BytesIO(data.read()), ext='png')
        self.ids.image.texture = im.texture

        #self.exit_file_manager()
        self.dismiss_popup()

    def single_tap(self, t):
        w, _ = Window.size
        x, _ = self.touch.pos
        if x < (w / 2):
            self.pageno -= (1 if self.pageno > 0 else 0)
        else:
            self.pageno += 1
        self.update()

    def double_tap(self, touch):
        self.reflowed = not self.reflowed
        try:
            self.update()
        except Exception as e:
            print(e)

    def touch_down(self, touch):
        if self.filename is None:
            return
        self.touch = touch
        if self.scheduled_event is not None:
            self.scheduled_event.cancel()
            self.scheduled_event = None
        if touch.is_double_tap:
            self.double_tap(touch)
        else:
            double_tap_wait_s = 1
            self.scheduled_event = Clock.schedule_once(
                partial(self.single_tap), double_tap_wait_s)

    def update(self):
        page_width = get_display_width()
        b = utils.get_page_for_display(self.pageno, self.filename, page_width)
        w, h = utils.get_page_size_for_display(self.pageno, self.filename, page_width)
        img = Image.frombytes("RGBA", (w, h), b)
        if self.reflowed:
            indent_width, flow_items, w, indents, mean_h = prepare_flow(img)
            new_image = reflow(img, indent_width, flow_items, w,
                               indents, mean_h)
            data = BytesIO()
            new_image.save(data, format='png')
            data.seek(0)
            im = CoreImage(BytesIO(data.read()), ext='png')
            self.ids.image.texture = im.texture
        else:
            data = BytesIO()
            img.save(data, format='png')
            data.seek(0)
            im = CoreImage(BytesIO(data.read()), ext='png')
            self.ids.image.texture = im.texture


class Editor(MDApp):
    pass

Factory.register('Root', cls=Root)
Factory.register('LoadDialog', cls=LoadDialog)


if __name__ == '__main__':
    app = Editor()
    app.run()
