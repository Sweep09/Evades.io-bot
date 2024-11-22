import cv2 as cv
import os
from time import time, sleep
from windowcapture import WindowCapture
from vision import Vision, Detection
import keyboard
from bot import EvadesBot, BotState

os.chdir(os.path.dirname(os.path.abspath(__file__)))

#add window title to parameters or leave blank
wincap = WindowCapture('Evades')
vision = Vision('img/gray-enemy-big.jpg')
detector = Detection('img/gray-enemy-big.jpg')
bot = EvadesBot((wincap.offset_x, wincap.offset_y), (wincap.w, wincap.h))


    

wincap.start()
detector.start()
#bot.start()

loop_time = time()
sleep(0.0001)
while True:
    if wincap.screenshot is not None:
        #access screenshot
        with wincap.lock:
            screenshot=wincap.screenshot
    
        # do object detection
        detector.update(screenshot)

        '''if bot.state == BotState.INITIALIZING:
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
'''
        # output onto original img
        detection_img = vision.draw_rectangles(screenshot, detector.rectangles)

        # display processed img
        cv.imshow('Matches', screenshot)

        wincap.move_window()
    else:
        print('no screenshit yet')
        
    wincap_fps = wincap.get_fps()
    detector_fps = detector.get_fps()

    #print(f"Main FPS: {1 / (time() - loop_time):.2f}")
    #print(f"WindowCapture FPS: {wincap_fps:.2f}")
    #print(f"Detection FPS: {detector_fps:.2f}")

    loop_time = time()
    
    sleep(0.001)

    # exit window
    if cv.waitKey(1) & 0xFF == ord('q') or keyboard.is_pressed('q'):
        wincap.stop()
        detector.stop()
        bot.stop()
        cv.destroyAllWindows()
        break
