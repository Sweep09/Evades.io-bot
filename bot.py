from math import sqrt
import cv2 as cv
import pyautogui
from time import time, sleep
from threading import Thread, Lock
from enum import Enum
from math import sqrt
import keyboard
import math


class BotState(Enum):
    
    INITIALIZING = 0
    MOVING = 1
    AVOIDING = 2
    

class EvadesBot:
    
    # constants
    INITIALIZING_SECONDS = 5
    IGNORE_RADIUS = 100
    
    # threading properties
    stopped = True
    lock = None
    
    state = None
    enemies = []
    screenshot = None
    timestamp = None
    window_offset = (0,0)
    window_w = 0
    window_h = 0
    
    def __init__(self, window_offset, window_size):
        
        self.lock = Lock()
        self.thread = None
        
        self.window_offset = window_offset
        self.window_w = window_size[0]
        self.window_h = window_size[1]
        
        self.state = BotState.INITIALIZING
        self.timestamp = time()
        
    def enemy_close(self):
        
        enemies = self.enemies_ordered_by_distance(self.enemies)
        
        enemy_i = 0
        found_blob = False
        while not found_blob and enemy_i < len(enemies):
            
            if self.stopped:
                break
            
            # load next enemy in list and translate relative coords
            enemy_pos = enemies[enemy_i]
            screen_x, screen_y = self.get_screen_pos(enemy_pos)
            # attempt to move mouse opposite of enemy
            #self.mirrored_x = self.window_w - screen_x
            #self.mirrored_y = self.window_h - screen_y
            #print(f'moving mouse to x:{screen_x} y: {screen_y}')
            
            found_blob = True
            enemy_i += 1
            
        return found_blob
        
    def enemies_ordered_by_distance(self, enemies):
        # might need to offset
        my_pos = (round(self.window_w / 2 + 8), round(self.window_h / 2 + 76))
        
        def pythagorean_distance(pos):
            return sqrt((pos[0] - my_pos[0])**2 + (pos[1] - my_pos[1])**2)
        enemies.sort(key=pythagorean_distance)
        # ignore enemies that are too far
        enemies = [e for e in enemies if pythagorean_distance(e) < self.IGNORE_RADIUS]
        return enemies
        
    def get_screen_pos(self, pos):
        return (pos[0] + self.window_offset[0], pos[1] + self.window_offset[1])
        
    def update_enemies(self, enemies):
        with self.lock:
            self.enemies = enemies
        
    def update_screenshot(self, screenshot):
        with self.lock:
            self.screenshot = screenshot
    
    #Chatgpt
    def calculate_avoidance_direction(self, my_pos, enemy_pos):
    # Calculate the vector from the enemy to the bot
        vector_x = my_pos[0] - enemy_pos[0]
        vector_y = my_pos[1] - enemy_pos[1]

        # Normalize the vector to get the direction
        magnitude = math.sqrt(vector_x**2 + vector_y**2)
        # If the magnitude is 0, the bot and enemy are in the same position
        if magnitude == 0:
            return (0, 0)  

        direction_x = vector_x / magnitude
        direction_y = vector_y / magnitude

        # Define a constant to determine how far to move away
        MOVE_DISTANCE = self.IGNORE_RADIUS 

        # Calculate the move distance in each direction
        move_x = direction_x * MOVE_DISTANCE
        move_y = direction_y * MOVE_DISTANCE

        return (move_x, move_y)
    # 
    def start(self):
        self.stopped = False
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.stopped = True

        
    def run(self):
        while not self.stopped:
            try:
                my_pos = (round(self.window_w / 2 + 8), round(self.window_h / 2 + 76))
                if self.state == BotState.INITIALIZING:
                    #print("Initializing")
                    if time() > self.timestamp + self.INITIALIZING_SECONDS:
                        # start moving after wait period
                        with self.lock:
                            self.state = BotState.MOVING
                    
                elif self.state == BotState.MOVING:
                    #print(f"your pos is set to:{my_pos}")
                    #pyautogui.moveTo(my_pos)
                    if not self.enemy_close():
                        #move right
                        #move_x, move_y = 150, 0
                        #pyautogui.moveTo(my_pos[0] + move_x, my_pos[1] + move_y)
                        pass
                    else:
                        with self.lock:
                            self.state = BotState.AVOIDING
                
                elif self.state == BotState.AVOIDING:
                    enemies_ordered = self.enemies_ordered_by_distance(self.enemies)
                    if not self.enemy_close():
                        with self.lock:
                            self.state = BotState.MOVING
                    
                    enemy_pos = enemies_ordered[0]
                    print(enemy_pos)
                    move_x, move_y = self.calculate_avoidance_direction(my_pos, enemy_pos)
                    print(f"Moving away from enemy: {move_x}, {move_y}")
                    #pyautogui.moveTo(my_pos[0] + move_x, my_pos[1] + move_y)

                    
            except IndexError:
                print("Can't avoid enemies.")
            except Exception as e:
                print(f"Error initiating bot: {e}")
                                
            sleep(0.01)

            
