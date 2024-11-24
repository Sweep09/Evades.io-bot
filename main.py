import cv2 as cv
import os
from time import time, sleep
from windowcapture import WindowCapture
from vision import Vision, Detection
import keyboard
from bot import EvadesBot, BotState
import win32gui, win32con

os.chdir(os.path.dirname(os.path.abspath(__file__)))

#add window title to parameters or leave blank
wincap = WindowCapture('Evades')
vision = Vision('img/gray-enemy-big.jpg')
detector = Detection('img/gray-enemy-big.jpg')
bot = EvadesBot((wincap.offset_x, wincap.offset_y), (wincap.w, wincap.h))


    

wincap.start()
detector.start()
bot.start()



window_name = 'Matches'
cv.namedWindow(window_name, cv.WINDOW_NORMAL)
cv.resizeWindow(window_name, 800, 600)
wincap.move_window(window_name)
hwnd = win32gui.FindWindow(None, window_name)
if hwnd:
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
else:
    print(f"Could not find window: {window_name}")


maximized_width = wincap.w
maximized_height = wincap.h

loop_time = time()
sleep(0.0001)

while True:
    if wincap.screenshot is not None:
        #access screenshot
        #with wincap.lock:
        screenshot=wincap.screenshot

        top = 150  # Remove 50 pixels from the top
        bottom = screenshot.shape[0]  # Remove 20 pixels from the bottom
        left = 150  # Remove 30 pixels from the left
        right = screenshot.shape[1] - 150  # Remove 30 pixels from the right
    
        # do object detection
        detector.update(screenshot)

        if bot.state == BotState.INITIALIZING:
            enemies = vision.get_points(detector.rectangles)
            bot.update_enemies(enemies)
        elif bot.state == BotState.MOVING:
            enemies = vision.get_points(detector.rectangles)
            bot.update_enemies(enemies)
            bot.update_screenshot(screenshot)

        elif bot.state == BotState.AVOIDING:
            enemies = vision.get_points(detector.rectangles)
            bot.update_enemies(enemies)
            bot.update_screenshot(screenshot)
        else:
            print(f"Main: Unknown state {bot.state}")

        # output onto original img
        detection_img = vision.draw_rectangles(screenshot, detector.rectangles)

        # display processed img
        cropped_img = screenshot[top:bottom, left:right]
        resized_img = cv.resize(cropped_img, (wincap.w, wincap.h), interpolation=cv.INTER_AREA)
        cv.imshow(window_name, resized_img)
        
    else:
        print('no screenshit yet')
        
    wincap_fps = wincap.get_fps()
    detector_fps = detector.get_fps()

    #print(f"Main FPS: {1 / (time() - loop_time):.2f}")
    #print(f"WindowCapture FPS: {wincap_fps:.2f}")
    #print(f"Detection FPS: {detector_fps:.2f}")

    loop_time = time()
    
    sleep(0.01)

    # exit window
    if cv.waitKey(1) & 0xFF == ord('q') or keyboard.is_pressed('q'):
        wincap.stop()
        detector.stop()
        bot.stop()
        cv.destroyAllWindows()
        break
