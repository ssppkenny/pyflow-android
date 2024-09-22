from kivymd.app import MDApp
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.logger import Logger
from kivy.properties import ListProperty

import kivy
import utils
from io import BytesIO
from kivy import platform
from urllib.parse import unquote

from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
import kivy.uix.image
from PIL import Image, ImageOps
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivymd.uix.filemanager.filemanager import MDFileManager

from android.storage import primary_external_storage_path
from android.storage import secondary_external_storage_path
from android import activity

import mydjvulib
import cv2
import reflow

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
        aIntent.addCategory(Intent.CATEGORY_OPENABLE)
        aIntent.setType("*")
        activity.bind(on_activity_result=on_activity_result)
        p_activity.startActivityForResult(aIntent, 42)

    def load(self, path, filename):
        print(f"path = {path}")
        self.filename = filename[0]
        page_width = 1.2 * get_display_width()
        if filename[0].endswith(".djvu"):
            img = self.load_djvu(self.pageno, self.filename)
        else:
            img = self.load_pdf(self.pageno, self.filename, page_width)
        data = BytesIO()
        img.save(data, format='png')
        data.seek(0)
        im = CoreImage(BytesIO(data.read()), ext='png')
        self.ids.image.texture = im.texture
        self.dismiss_popup()

    def single_tap(self, t):
        print(t)
        w, _ = Window.size
        x, _ = self.touch.pos
        print("single tap")
        print(f"x = {x}, w = {w}")
        if x < (w / 2):
            self.pageno -= (1 if self.pageno > 0 else 0)
        else:
            self.pageno += 1
        self.update(True)

    def double_tap(self, touch):
        print(touch)
        self.reflowed = not self.reflowed
        try:
            self.update(False)
        except Exception as e:
            print(e)

    def touch_down(self, touch):
        if self.filename is None:
            return
        self.mouse_x, _ = touch.pos
        touch.grab(self)
        # if self.scheduled_event is not None:
        #     self.scheduled_event.cancel()
        #     self.scheduled_event = None
        # if touch.is_double_tap:
        #     print("is double tap")
        #     self.double_tap(touch)
        # else:
        #     double_tap_wait_s = 0.5

    def touch_move(self, touch):
        pass

    def touch_up(self, touch):
        if touch.grab_current is self:
            x1 = self.mouse_x
            x2, _ = touch.pos

            if x1 < x2 and x2 - x1 > 50:
                self.pageno += 1
                self.update(True)
            elif x2 < x1 and x1 - x2 > 50:
                self.pageno -= (1 if self.pageno > 0 else 0)
                self.update(True)
            else:
                self.reflowed = not self.reflowed
                self.update(False)

    def load_djvu(self, pageno, filepath):
        arr = mydjvulib.get_image_as_arrray(pageno, filepath)
        _, bw = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return Image.fromarray(bw, "L")

    def load_pdf(self, pageno, filepath, page_width):
        b = utils.get_page_for_display(pageno, filepath, page_width)
        w, h = utils.get_page_size_for_display(pageno, filepath, page_width)
        return Image.frombytes("RGBA", (w, h), b)

    def update(self, load_new_page):
        if self.filename is None:
            return
        page_width = 1.2 * get_display_width()
        if load_new_page:
            if self.filename.endswith(".djvu"):
                self.img = self.load_djvu(self.pageno, self.filename)
            else:
                self.img = self.load_pdf(self.pageno, self.filename, page_width)
        if self.reflowed:
            new_image = reflow.reflow(self.img)
            data = BytesIO()
            new_image.save(data, format='png')
            data.seek(0)
            im = CoreImage(BytesIO(data.read()), ext='png')
            self.ids.image.texture = im.texture
        else:
            data = BytesIO()
            self.img.save(data, format='png')
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
