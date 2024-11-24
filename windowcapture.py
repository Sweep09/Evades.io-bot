import cv2 as cv
import numpy as np
import win32gui, win32ui, win32con, win32api
from threading import Thread, Lock
from time import time, sleep

class WindowCapture:
    
    # threading properties
    stopped = True
    lock = None
    screenshot = None

    # properties
    w = 0 
    h = 0 
    hwnd = None
    cropped_x = 0
    cropped_y = 0
    offset_x = 0
    offset_y = 0
    
    # constructor
    def __init__(self, window_name=None):
        # create lock obj
        self.lock = Lock()
        self.thread = None
        self.fps = 0
        self.last_time = None
        
        if window_name is None:
            self.hwnd = win32gui.GetDesktopWindow()
        else:
            self.hwnd = win32gui.FindWindow(None, window_name)
            if not self.hwnd:
                raise Exception('Window not found: {}'.format(window_name))

        # get window size
        window_rect = win32gui.GetWindowRect(self.hwnd)
        print("Window rect:", window_rect)
        self.w = window_rect[2] - window_rect[0]
        self.h = window_rect[3] - window_rect[1]
        print("Calculated window dimensions (w, h):", self.w, self.h)
 
    def get_screenshot(self):

        retries = 3
        for attempt in range(retries):
            try:
                # get window image data
                wDC = win32gui.GetWindowDC(self.hwnd)
                dcObj=win32ui.CreateDCFromHandle(wDC)

                cDC=dcObj.CreateCompatibleDC()
                # create bitmap obj
                dataBitMap = win32ui.CreateBitmap()
                dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
                cDC.SelectObject(dataBitMap)
        
            
                # copy window's device context to memory device context
                cDC.BitBlt((0,0),(self.w, self.h) , dcObj, (self.cropped_x,
                                                            self.cropped_y), 
                                                            win32con.SRCCOPY)
        
                # save file
                #dataBitMap.SaveBitmapFile(cDC, bmpfilenamename)
                signedIntsArray = dataBitMap.GetBitmapBits(True)
                img = np.fromstring(signedIntsArray, dtype='uint8')
                img.shape = (self.h, self.w, 4)
        

                # Free Resources
                dcObj.DeleteDC()
                cDC.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, wDC)
                win32gui.DeleteObject(dataBitMap.GetHandle())
    
                # drop alpha channel or cv.matchTemplate() will throw an error.
                #img = img[...,:3]
    
                # make image C_CONTIGUOUS to avoid errors.
                #img = np.ascontiguousarray(img)
                # convert colors
                img = cv.cvtColor(img, cv.COLOR_BGRA2GRAY)

                #print(f"Capturing window with dimensions: {self.w}x{self.h}")
                return img
        
            except win32ui.error as e:
                print(f"Attempt {attempt + 1}/{retries} failed: {e}")
                dcObj.DeleteDC()
                cDC.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, wDC)
                win32gui.DeleteObject(dataBitMap.GetHandle())
                if attempt == retries - 1:
                    raise
                else:
                    sleep(1)
    
    @staticmethod
    def list_window_names():
        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                print(hex(hwnd), win32gui.GetWindowText(hwnd))
        win32gui.EnumWindows(winEnumHandler, None)

    # translate screenshot pixels to screen pixels
    #def get_screen_pos(self, pos):
     #   return (pos[0] + self.offset_x, pos[1] + self.offset_y)

    def move_window(self, window_name, x=1920, y=0):
        #Checks if a second monitor is available.
        monitors = win32api.EnumDisplayMonitors()
        # move window to other if available
        if len(monitors) > 1:
            # Get window title from hwnd
            cv.moveWindow(window_name, x, y)
            print(f"Window '{window_name}' moved to position ({x}, {y})")

    def get_fps(self):
        return self.fps
    
    # threading methods
    def start(self):
        print('starting capture thread')
        self.stopped = False
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()
        
    def stop(self):
        print('stopping capture thread')
        self.stopped = True
        
    def run(self):
        while not self.stopped:
            try:
                current_time = time()
                # get updated img of window
                with self.lock:
                    self.screenshot = self.get_screenshot()

                #fps calculation
                if self.last_time:
                    elapsed_time = current_time - self.last_time
                    self.fps = 1 / elapsed_time
                self.last_time = current_time
                
                sleep(0.02)
            except Exception as e:
                print(f"Error capturing screenshot: {e}")
            
