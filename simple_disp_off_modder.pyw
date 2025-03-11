# Credits:
# Programmer : Simon Brunning - simon@brunningonline.net
# Notes      : Based on (i.e. ripped off from) Mark Hammond's
#              win32gui_taskbar.py and win32gui_menu.py demos from PyWin32
# 
# actually modified to  work to a reasonable end by myself (rotemlv)

from windo import change_display_off_timer as original_disp_off_timer


# corrected fun
def change_display_off_timer(icon, time):
    original_disp_off_timer(time)


import os
from collections.abc import Iterable

import win32api
import win32con
import win32gui_struct

try:
    import winxpgui as win32gui
except ImportError:
    print("Let me tell you about a porcupine's ba")
    import win32gui


def start_em():
    print("Everyting in motion")


class SysTrayIcon(object):
    QUIT = 'QUIT'
    SPECIAL_ACTIONS = [QUIT]

    FIRST_ID = 1023
    start_em()

    def __init__(self,
                 icon,
                 hover_text,
                 menu_options,
                 on_quit=None,
                 default_menu_index=None,
                 window_class_name=None, ):

        self.icon = icon
        self.hover_text = hover_text
        self.on_quit = on_quit

        menu_options = menu_options + (('Quit', None, self.QUIT),)
        self._next_action_id = self.FIRST_ID
        self.menu_actions_by_id_set = set()
        self.menu_options = self._add_ids_to_menu_options(list(menu_options))
        self.menu_actions_by_id = dict(self.menu_actions_by_id_set)
        del self._next_action_id

        self.default_menu_index = (default_menu_index or 0)
        self.window_class_name = window_class_name or "SysTrayIconPy"

        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
                       win32con.WM_DESTROY: self.destroy,
                       win32con.WM_COMMAND: self.command,
                       win32con.WM_USER + 20: self.notify, }
        # Register the Window class.
        window_class = win32gui.WNDCLASS()
        hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
        window_class.lpszClassName = self.window_class_name
        window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        window_class.hbrBackground = win32con.COLOR_WINDOW
        window_class.lpfnWndProc = message_map  # could also specify a wndproc.
        classAtom = win32gui.RegisterClass(window_class)
        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(classAtom,
                                          self.window_class_name,
                                          style,
                                          0,
                                          0,
                                          win32con.CW_USEDEFAULT,
                                          win32con.CW_USEDEFAULT,
                                          0,
                                          0,
                                          hinst,
                                          None)
        win32gui.UpdateWindow(self.hwnd)
        self.notify_id = None
        self.refresh_icon()
        win32gui.PumpMessages()

    def _add_ids_to_menu_options(self, menu_options):
        result = []
        for menu_option in menu_options:
            # Handle parameterized menu items
            if len(menu_option) >= 4:
                option_text, option_icon, option_action, params = menu_option[:4]
                submenu_options = menu_option[4:] if len(menu_option) > 4 else None

                if callable(option_action):
                    self.menu_actions_by_id_set.add((self._next_action_id, (option_action, params)))
                    result.append(menu_option[:3] + (self._next_action_id,))

                elif non_string_iterable(submenu_options):
                    result.append((
                        option_text,
                        option_icon,
                        self._add_ids_to_menu_options(submenu_options),
                        self._next_action_id
                    ))

            # Handle special actions (including QUIT)
            elif len(menu_option) == 3 and menu_option[2] in self.SPECIAL_ACTIONS:
                option_text, option_icon, option_action = menu_option
                self.menu_actions_by_id_set.add((self._next_action_id, option_action))
                result.append(menu_option + (self._next_action_id,))

            # Handle regular menu items
            elif len(menu_option) == 3 and callable(menu_option[2]):
                option_text, option_icon, option_action = menu_option
                self.menu_actions_by_id_set.add((self._next_action_id, option_action))
                result.append(menu_option + (self._next_action_id,))

            elif len(menu_option) == 3 and non_string_iterable(menu_option[2]):
                option_text, option_icon, option_action = menu_option
                result.append((
                    option_text,
                    option_icon,
                    self._add_ids_to_menu_options(option_action),
                    self._next_action_id
                ))

            self._next_action_id += 1
        return result

    def execute_menu_option(self, id):
        menu_action = self.menu_actions_by_id[id]

        # Handle parameterized functions
        if isinstance(menu_action, tuple):
            func, params = menu_action
            func(self, *params)
        # Handle special actions (including QUIT)
        elif menu_action in self.SPECIAL_ACTIONS:
            if menu_action == self.QUIT:
                self.destroy(self.hwnd, None, None, None)
        # Handle regular functions
        else:
            menu_action(self)

    def refresh_icon(self):
        # Try and find a custom icon
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(self.icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst,
                                       self.icon,
                                       win32con.IMAGE_ICON,
                                       0,
                                       0,
                                       icon_flags)
        else:
            print("Can't find icon file - using default.")
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if self.notify_id:
            message = win32gui.NIM_MODIFY
        else:
            message = win32gui.NIM_ADD
        self.notify_id = (self.hwnd,
                          0,
                          win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                          win32con.WM_USER + 20,
                          hicon,
                          self.hover_text)
        win32gui.Shell_NotifyIcon(message, self.notify_id)

    def restart(self, hwnd, msg, wparam, lparam):
        self.refresh_icon()

    def destroy(self, hwnd, msg, wparam, lparam):
        if self.on_quit: self.on_quit(self)
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)  # Terminate the app.
        return 0  # everything worked fine

    def notify(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_LBUTTONDBLCLK:
            self.execute_menu_option(self.default_menu_index + self.FIRST_ID)
        elif lparam == win32con.WM_RBUTTONUP:
            self.show_menu()
        elif lparam == win32con.WM_LBUTTONUP:
            pass
        return True

    def show_menu(self):
        menu = win32gui.CreatePopupMenu()
        self.create_menu(menu, self.menu_options)
        # win32gui.SetMenuDefaultItem(menu, 1000, 0)

        pos = win32gui.GetCursorPos()
        # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                self.hwnd,
                                None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    def create_menu(self, menu, menu_options):
        for option_text, option_icon, option_action, option_id in menu_options[::-1]:
            if option_icon:
                option_icon = self.prep_menu_icon(option_icon)

            if option_id in self.menu_actions_by_id:
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                wID=option_id)
                win32gui.InsertMenuItem(menu, 0, 1, item)
            else:
                submenu = win32gui.CreatePopupMenu()
                self.create_menu(submenu, option_action)
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                hSubMenu=submenu)
                win32gui.InsertMenuItem(menu, 0, 1, item)

    def prep_menu_icon(self, icon):
        # First load the icon.
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

        hdcBitmap = win32gui.CreateCompatibleDC(0)
        hdcScreen = win32gui.GetDC(0)
        hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
        hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
        # Fill the background.
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
        win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
        # unclear if brush needs to be feed.  Best clue I can find is:
        # "GetSysColorBrush returns a cached brush instead of allocating a new
        # one." - implies no DeleteObject
        # draw the icon
        win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        win32gui.SelectObject(hdcBitmap, hbmOld)
        win32gui.DeleteDC(hdcBitmap)

        return hbm

    def command(self, hwnd, msg, wparam, lparam):
        command_id = win32gui.LOWORD(wparam)
        self.execute_menu_option(command_id)
        return 0  # for now


def non_string_iterable(obj):
    return isinstance(obj, Iterable) and not isinstance(obj, str)
    # try:
    #     iter(obj)
    # except TypeError:
    #     return False
    # else:
    #     return not isinstance(obj, str)


def declare_display_timer_variants():
    return tuple(
        [(f'{i} Minutes'
          if i > 1 else "1 Minute", next(icons), change_display_off_timer, (i,))
         for i in [1, 2, 3, 5, 10, 15, 20, 25, 30, 45]] +
        [(f'{i} Hours'
          if i > 1 else "1 Hour", next(icons), change_display_off_timer, (i * 60,)) for i in [1, 2, 3, 4, 5]]
        + [("Never", next(icons), change_display_off_timer, (0,))]
    )


# Minimal self test. You'll need a bunch of ICO files in the current working
# directory in order for this to work...
if __name__ == '__main__':
    import itertools, glob

    icons = itertools.cycle(glob.glob('*.ico'))
    hover_text = "WintoolEZ"


    def hello(sysTrayIcon, whom): print(f"Hello World and {whom}.")


    def simon(sysTrayIcon): print("Hello Simon.")


    def switch_icon(sysTrayIcon):
        sysTrayIcon.icon = next(icons)
        sysTrayIcon.refresh_icon()


    menu_options = (
        ('Display timer', next(icons),
         declare_display_timer_variants(),
         ),

    )


    # print(menu_options)

    def bye(sysTrayIcon): print('Bye, then.')


    SysTrayIcon(next(icons), hover_text, menu_options, on_quit=bye, default_menu_index=1)
