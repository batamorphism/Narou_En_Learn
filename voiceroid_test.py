# https://blog.sky-net.pw/article/9
import win32gui
import win32con
import time


class VoiceRoidError(Exception):
    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return str(self.reason)


class VoiceRoid(object):
    def __init__(self, name):
        self.name = name
        self.parentHwnd = win32gui.FindWindow(None, name)

        if self.parentHwnd == 0:
            raise VoiceRoidError("VoiceRoidNotFound")
        self.play = self.getHandle(text="再生")[0]
        self.textbox = self.getHandle(name="WindowsForms10.RichEdit20W")[0]

    def getHandle(self, **args):
        result = []

        def enumwindows(hwnd, args):
            if not args.get("text", None) is None:
                if args["text"] in win32gui.GetWindowText(hwnd):
                    result.append(hwnd)
            elif not args.get("name") is None:
                if args["name"] in win32gui.GetClassName(hwnd):
                    result.append(hwnd)

        win32gui.EnumChildWindows(
            self.parentHwnd,
            enumwindows,
            args
        )
        return result

    def sendText(self, hwnd, text):
        win32gui.SendMessage(hwnd, win32con.WM_SETTEXT, 0, text)

    def say(self, text):
        while True:
            time.sleep(0.15)
            if len(self.getHandle(text="一時停止")) < 1:
                break
        self.sendText(self.textbox, text)

        win32gui.SendMessage(self.play, win32con.BM_CLICK, 0, 0)

if __name__ == "__main__":
    import sys
    args = sys.argv
    print(args)

    if 1 < len(args):
        voiceroid = VoiceRoid("VOICEROID＋ 結月ゆかり EX")
        text = args[1]
        voiceroid.say(text)


voiceroid = VoiceRoid("VOICEROID＋ 民安ともえ EX")
voiceroid.say('This is a test.')
