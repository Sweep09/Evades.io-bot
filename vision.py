import cv2 as cv
import numpy as np
from threading import Thread, Lock
from time import time, sleep

class Vision:
    
    # constants
    TRACKBAR_WINDOW = 'Trackbars'
    
    #properties
    needle_img = None
    needle_w = 0
    needle_h = 0
    method = None
    
    def __init__(self, needle_img_path, method=cv.TM_CCOEFF_NORMED):
        
        self.needle_img = cv.imread(needle_img_path, cv.IMREAD_GRAYSCALE)
        self.needle_w = self.needle_img.shape[1]
        self.needle_h = self.needle_img.shape[0]
        
        self.method = method

    def findPos(self, haystack_img, threshold=0.61,  max_results=30):
    
    
    
        if len(haystack_img.shape) == 3:
            haystack_img = cv.cvtColor(haystack_img, cv.COLOR_BGR2GRAY)

        result = cv.matchTemplate(haystack_img, self.needle_img, self.method)

        locations = np.where(result >= threshold)
        locations = list(zip(*locations[::-1]))
        
        # if no results, return now
        if not locations:
            return np.array([], dtype=np.int32).reshape(0,4)

        rectangles = []
        for loc in locations:
            rect = [int(loc[0]), int(loc[1]), self.needle_w, self.needle_h]
            rectangles.append(rect)
            rectangles.append(rect)

        rectangles, weights = cv.groupRectangles(rectangles, 1, 0.2)
        
        # for performance reasons, returns limited number of results
        if len(rectangles) > max_results:
            print(f'Warning: {len(rectangles)} results found, but only {max_results} will be returned.')
            rectangles = rectangles[:max_results]
        
        return rectangles
    
    def get_points(self, rectangles) -> list:

        points = []
    
            # need to loop over all locations and draw rectangle
        for (x, y, w, h) in rectangles:
            
            # determine center pos
            center_x = x + int(w/2)
            center_y = y + int(h/2)
            #save the points
            points.append((center_x, center_y))
            
        return points

                
    def draw_rectangles(self, haystack_img, rectangles):
        
        line_type = cv.LINE_4
        line_color = (0,0,0)
        

        for (x, y, w, h) in rectangles:
            
            # determine box pos
            top_left = (x,y)
            bottom_right = (x + w, y + h)
            # draw box
            cv.rectangle(haystack_img, top_left, bottom_right, line_color, lineType=line_type)
            
        return haystack_img
    

    def draw_crosshairs(self, haystack_img, points):
        
        marker_type = cv.MARKER_CROSS
        marker_color = (255,0,255)
        
        for (center_x, center_y) in points:
            
            # draw center points
            cv.drawMarker(haystack_img, (center_x,center_y), marker_color, marker_type)
    
        return haystack_img
    
    # create real-time gui with adjustable controls
    # placeholder for reference
    '''def init_control_gui(self):
        cv.namedWindow(self.TRACKBAR_WINDOW, cv.WINDOW_NORMAL)
        cv.resizeWindow(self.TRACKBAR_WINDOW, 350, 700)
        
        # required callback. using getTrackbarPos() instead.
        def nothing(position):
            pass
        
        # create trackbar for bracketing
        # OpenCV scale for HSV is H: 0-179, S: 0-255, V: 0-255
        cv.createTrackbar('HMin', self.TRACKBAR_WINDOW, 0, 179, nothing)
        cv.createTrackbar('SMin', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('VMin', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('HMax', self.TRACKBAR_WINDOW, 0, 179, nothing)
        cv.createTrackbar('SMax', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('VMax', self.TRACKBAR_WINDOW, 0, 255, nothing)
        # set default val for Max HSV trackbars
        cv.setTrackbarPos('HMax', self.TRACKBAR_WINDOW, 179)
        cv.setTrackbarPos('SMax', self.TRACKBAR_WINDOW, 255)
        cv.setTrackbarPos('VMax', self.TRACKBAR_WINDOW, 255)
        
        # trackbars for increasing/decreasing sat and val
        cv.createTrackbar('SAdd', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('SSub', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('VAdd', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('VSub', self.TRACKBAR_WINDOW, 0, 255, nothing)
        
    # returns HSB filter object based on control GUI vals
    def get_hsv_filter_from_controls(self):
        # get current pos of trackbars
        hsv_filter = HsvFilter()
        hsv_filter.hMin = cv.getTrackbarPos('HMin', self.TRACKBAR_WINDOW)
        hsv_filter.sMin = cv.getTrackbarPos('SMin', self.TRACKBAR_WINDOW)
        hsv_filter.vMin = cv.getTrackbarPos('VMin', self.TRACKBAR_WINDOW)
        hsv_filter.hMax = cv.getTrackbarPos('HMax', self.TRACKBAR_WINDOW)
        hsv_filter.sMax = cv.getTrackbarPos('SMax', self.TRACKBAR_WINDOW)
        hsv_filter.vMax = cv.getTrackbarPos('VMax', self.TRACKBAR_WINDOW)
        hsv_filter.sAdd = cv.getTrackbarPos('SAdd', self.TRACKBAR_WINDOW)
        hsv_filter.sSub = cv.getTrackbarPos('SSub', self.TRACKBAR_WINDOW)
        hsv_filter.vAdd = cv.getTrackbarPos('VAdd', self.TRACKBAR_WINDOW)
        hsv_filter.vSub = cv.getTrackbarPos('VSub', self.TRACKBAR_WINDOW)
        
        return hsv_filter
    
    # apply filter to resulting img
    def apply_hsv_filter(self, original_img, hsv_filter=None):
        # convert img to HSV
        hsv = cv.cvtColor(original_img, cv.COLOR_BGR2HSV)
        
        if not hsv_filter:
            hsv_filter = self.get_hsv_filter_from_controls()
        
        # add/sub sat and val
        h, s, v = cv.split(hsv)
        s = self.shift_channel(s, hsv_filter.sAdd)
        s = self.shift_channel(s, -hsv_filter.sSub)
        v = self.shift_channel(v, hsv_filter.vAdd)
        v = self.shift_channel(v, -hsv_filter.vSub)
        hsv = cv.merge([h, s, v])

        # set min/max hsv display vals
        lower = np.array([hsv_filter.hMin, hsv_filter.sMin, hsv_filter.vMin])
        upper = np.array([hsv_filter.hMax, hsv_filter.sMax, hsv_filter.vMax])
        
        # apply thresholds
        mask = cv.inRange(hsv, lower, upper)
        result = cv.bitwise_and(hsv, hsv, mask=mask)
        
        # convert img back to BGR for imshow() to display
        img = cv.cvtColor(result, cv.COLOR_HSV2BGR)
        
        return img
    
    # apply adjustment to HSV channel
    def shift_channel(self, c, amount):
        if amount > 0:
            lim = 255 - amount
            c[c >= lim] = 255
            c[c < lim] += amount
        elif amount < 0:
            amount = -amount
            lim = amount
            c[c <= lim] = 0
            c[c > lim] -= amount
            
        return c'''
    
class Detection:
    
    # threading properties
    stopped = True
    lock = None
    buffer = [None, None] # double buffer for screenshots
    buffer_index = 0
    rectangles = []
    
    vision = None # placeholder for vision instance
    
    def __init__(self, needle_img_path):
        # create lock obj
        self.lock = Lock()
        self.thread = None
        self.vision = Vision(needle_img_path)

        self.buffer = None
        self.buffer_index = 0

        self.rectangles = []

        self.fps = 0
        self.last_time = None
        
    def update(self, screenshot):
        with self.lock:
            self.buffer = screenshot

    def get_fps(self):
        return self.fps

    def start(self):
        print('starting detection thread')
        self.stopped = False
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()
        
    def stop(self):
        print('stopping detection thread')
        self.stopped = True
        
    def run(self):
        while not self.stopped:
            # do obj dectection
            try:
                current_time = time()
                if self.buffer is not None:
                    with self.lock:
                        screenshot = self.buffer
                    self.rectangles = self.vision.findPos(screenshot)

                #fps calculation
                if self.last_time:
                    elapsed_time = current_time - self.last_time
                    self.fps = 0.9 * self.fps + 0.1 * (1 / elapsed_time)
                self.last_time = current_time
                #sleep(0.002)

            except Exception as e:
                print(f"Error assigning rectangles: {e}")
