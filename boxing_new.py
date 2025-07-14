import serial
import pygame
import sys
import json
import os
import time
import threading
import random
from pymongo import MongoClient
from datetime import datetime

ser = serial.Serial('/dev/cu.usbmodem1301', 9600)

# MongoDB setup
try:
    client = MongoClient('mongodb://localhost:27017/')  # Default MongoDB connection
    db = client['boxing_game']
    scores_collection = db['scores']
    print("Connected to MongoDB successfully")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    client = None
    db = None
    scores_collection = None

pygame.init()
pygame.mixer.init()

# Taunts and praises
insults = [
    "Is that all you've got?",
    "You're hitting like a feather!",
    "Is the bag too heavy for you?",
    "Are you even trying?",
    "I've seen toddlers hit harder!",
    "You call that a punch?",
    "Come on, put some muscle into it!",
    "Were you aiming for a fly?",
    "You're going to need more than that!",
    "Maybe boxing isn't your sport!",
    "That was weak!",
    "Are you sure you're awake?",
    "Is your grandma punching for you?",
    "I've seen pillows hit harder!",
    "Was that a punch or a pat?"
]

praises = [
    "You're a powerhouse!",
    "Now that's a punch!",
    "You're unstoppable!",
    "Keep it up, champ!",
    "You're on fire!",
    "That's some serious power!",
    "You're dominating the game!",
    "Impressive hit!",
    "You have fists of steel!",
    "Boxing legend in the making!"
]

insults_music = ["barbie.mp3"]
praises_music = ["cena.mp3"]

# Display setup
info = pygame.display.Info()
screen_width, screen_height = info.current_w, info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption('Power Punch Boxing Game')

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (54, 161, 93)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)

minimum_threshold = 305

# State management
current_state = "username_input"  # Start with username input
update_screen_display_time = 8  # seconds
update_screen_timer = 0
current_username = ""
input_active = True
show_leaderboard = False

# Fonts
font_large = pygame.font.Font(None, 90)
font_medium = pygame.font.Font(None, 40)
font_small = pygame.font.Font(None, 36)

# Images
background_img = pygame.image.load('images/bg.png')
barbie_img = pygame.image.load('images/barbie.png')
cena_img = pygame.image.load('images/cenaa.png')

# JSON file to store high scores
high_score_file = 'high_scores.json'

UPDATE_DELAY = 0.5
last_update_time = 0

# MongoDB functions
def store_score_to_mongodb(username, score):
    """Store a user's score to MongoDB"""
    if scores_collection is not None:
        try:
            score_data = {
                "username": username,
                "score": score,
                "timestamp": datetime.now()
            }
            scores_collection.insert_one(score_data)
            print(f"Score stored for {username}: {score}")
        except Exception as e:
            print(f"Error storing score: {e}")
    else:
        print("MongoDB not connected. Score not stored.")

def get_leaderboard():
    """Get top 10 scores from MongoDB"""
    if scores_collection is not None:
        try:
            top_scores = list(scores_collection.find().sort("score", -1).limit(10))
            return top_scores
        except Exception as e:
            print(f"Error retrieving leaderboard: {e}")
            return []
    else:
        print("MongoDB not connected. Cannot retrieve leaderboard.")
        return []

def get_user_high_score(username):
    """Get a specific user's highest score"""
    if scores_collection is not None:
        try:
            user_scores = list(scores_collection.find({"username": username}).sort("score", -1).limit(1))
            if user_scores:
                return user_scores[0]["score"]
            return 0
        except Exception as e:
            print(f"Error retrieving user high score: {e}")
            return 0
    else:
        return 0

def get_overall_high_score():
    """Get the overall highest score from MongoDB"""
    if scores_collection is not None:
        try:
            highest = list(scores_collection.find().sort("score", -1).limit(1))
            if highest:
                return highest[0]["score"]
            return 0
        except Exception as e:
            print(f"Error retrieving overall high score: {e}")
            return 0
    else:
        return 0

# File-based high score functions
def read_high_scores():
    if os.path.exists(high_score_file):
        with open(high_score_file, 'r') as file:
            return json.load(file)
    return {"high_score": 0}

def write_high_score(score):
    with open(high_score_file, 'w') as file:
        json.dump({"high_score": score}, file)

def play_song(song):
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load(song)
        pygame.mixer.music.play()

# Initialize high score
high_scores = read_high_scores()
highest_score = max(high_scores["high_score"], get_overall_high_score())

def display_username_input():
    """Display username input screen"""
    global current_username, input_active
    screen.blit(pygame.transform.scale(background_img, (screen_width, screen_height)), (0, 0))
    
    title_text = font_large.render("ENTER YOUR NAME", True, BLACK)
    instruction_text = font_medium.render("Type your username and press ENTER", True, BLACK)
    
    # Username input box
    input_box_rect = pygame.Rect(screen_width * 0.3, screen_height * 0.5, screen_width * 0.4, 60)
    pygame.draw.rect(screen, WHITE, input_box_rect, border_radius=10)
    pygame.draw.rect(screen, BLACK, input_box_rect, 3, border_radius=10)
    
    username_text = font_medium.render(current_username, True, BLACK)
    screen.blit(username_text, (input_box_rect.x + 10, input_box_rect.y + 15))
    
    # Cursor blinking effect
    if input_active and int(time.time() * 2) % 2:
        cursor_x = input_box_rect.x + 15 + username_text.get_width()
        pygame.draw.line(screen, BLACK, (cursor_x, input_box_rect.y + 10), 
                        (cursor_x, input_box_rect.y + 50), 2)
    
    title_rect = title_text.get_rect(center=(screen_width / 2, screen_height * 0.3))
    instruction_rect = instruction_text.get_rect(center=(screen_width / 2, screen_height * 0.4))
    
    screen.blit(title_text, title_rect)
    screen.blit(instruction_text, instruction_rect)
    
    # Instructions
    enter_text = font_small.render("Press ENTER to start | Press 'L' to view leaderboard", True, BLACK)
    enter_rect = enter_text.get_rect(center=(screen_width / 2, screen_height * 0.7))
    screen.blit(enter_text, enter_rect)
    
    pygame.display.flip()

def display_leaderboard():
    """Display the leaderboard screen"""
    screen.blit(pygame.transform.scale(background_img, (screen_width, screen_height)), (0, 0))
    
    title_text = font_large.render("LEADERBOARD - TOP 10", True, BLACK)
    title_rect = title_text.get_rect(center=(screen_width / 2, screen_height * 0.1))
    screen.blit(title_text, title_rect)
    
    leaderboard = get_leaderboard()
    
    if leaderboard:
        y_offset = screen_height * 0.2
        for i, entry in enumerate(leaderboard):
            rank = i + 1
            username = entry["username"]
            score = entry["score"]
            
            # Color coding for top 3
            if rank == 1:
                color = GOLD
            elif rank == 2:
                color = SILVER
            elif rank == 3:
                color = BRONZE
            else:
                color = BLACK
            
            rank_text = font_medium.render(f"{rank}. {username}: {score}", True, color)
            rank_rect = rank_text.get_rect(center=(screen_width / 2, y_offset))
            screen.blit(rank_text, rank_rect)
            y_offset += 50
    else:
        no_data_text = font_medium.render("No scores available yet!", True, BLACK)
        no_data_rect = no_data_text.get_rect(center=(screen_width / 2, screen_height * 0.5))
        screen.blit(no_data_text, no_data_rect)
    
    # Instructions
    back_text = font_small.render("Press 'B' to go back | Press 'ESC' to return to game", True, BLACK)
    back_rect = back_text.get_rect(center=(screen_width / 2, screen_height * 0.9))
    screen.blit(back_text, back_rect)
    
    pygame.display.flip()

def display_initial_screen():
    """Display the main game screen"""
    global current_state, update_screen_timer
    screen.blit(pygame.transform.scale(background_img, (screen_width, screen_height)), (0, 0))

    title_text = font_large.render("POWER PUNCH", True, BLACK)
    sub_text = font_medium.render("Let's see what you got? Hit the pad, watch your score soar!", True, BLACK)
    sub_text_two = font_medium.render("Show off your power and dominate the leaderboard!", True, BLACK)
    high_score_text = font_large.render(f"High Score: {highest_score}", True, GREEN)
    
    if current_username:
        user_text = font_medium.render(f"Player: {current_username}", True, BLACK)
        user_rect = user_text.get_rect(center=(screen_width / 2, screen_height * 0.2))
        screen.blit(user_text, user_rect)

    title_rect = title_text.get_rect(center=(screen_width / 2, screen_height * 0.3))
    sub_text_rect = sub_text.get_rect(center=(screen_width / 2, screen_height * 0.45))
    sub_text_two_rect = sub_text_two.get_rect(center=(screen_width / 2, screen_height * 0.5))
    high_score_rect = high_score_text.get_rect(center=(screen_width / 2, screen_height * 0.93))

    screen.blit(title_text, title_rect)
    screen.blit(sub_text, sub_text_rect)
    screen.blit(sub_text_two, sub_text_two_rect)
    screen.blit(high_score_text, high_score_rect)
    
    # Instructions
    instructions_text = font_small.render("Press 'L' for leaderboard | Press 'U' to change user", True, BLACK)
    instructions_rect = instructions_text.get_rect(center=(screen_width / 2, screen_height * 0.85))
    screen.blit(instructions_text, instructions_rect)
    
    pygame.display.flip()

    current_state = "initial"
    update_screen_timer = 0

def update_display(fsr1, fsr2, average_force):
    """Update display after a punch"""
    global highest_score, last_update_time, current_state, update_screen_timer
    current_time = time.time()

    if current_time - last_update_time < UPDATE_DELAY:
        return

    last_update_time = current_time
    screen.blit(pygame.transform.scale(background_img, (screen_width, screen_height)), (0, 0))

    avg_force_text = font_large.render(f"Your Score is: {average_force}", True, GREEN)
    pygame.draw.rect(screen, WHITE, pygame.Rect(screen_width * 0.2, screen_height * 0.4, 
                     screen_width * 0.6, screen_height * 0.1), border_radius=10)
    screen.blit(avg_force_text, (screen_width * 0.25, screen_height * 0.42))

    # Store score to MongoDB
    if current_username:
        store_score_to_mongodb(current_username, average_force)

    if average_force >= 650 and average_force <= 865:
        screen.blit(pygame.transform.scale(barbie_img, (screen_width // 4, screen_height // 4)), 
                   (screen_width * 0.75, screen_height * 0.5))
        play_song('barbie.mp3')
        insult = random.choice(insults)
        insult_text = font_medium.render(insult, True, BLACK)
        insult_rect = insult_text.get_rect(center=(screen_width * 0.5, screen_height * 0.15))
        screen.blit(insult_text, insult_rect)
    elif average_force > 865:
        screen.blit(pygame.transform.scale(cena_img, (screen_width // 4, screen_height // 4)), 
                   (screen_width * 0.75, screen_height * 0.5))
        play_song('cena.mp3')
        praise = random.choice(praises)
        praise_text = font_small.render(praise, True, BLACK)
        praise_rect = praise_text.get_rect(center=(screen_width * 0.5, screen_height * 0.7))
        screen.blit(praise_text, praise_rect)
    else:
        screen.blit(pygame.transform.scale(barbie_img, (screen_width // 2, screen_height // 2)), 
                   (screen_width * 0.75, screen_height * 0.5))
        play_song('barbie.mp3')
        insult = random.choice(insults)
        insult_text = font_medium.render(insult, True, BLACK)
        insult_rect = insult_text.get_rect(center=(screen_width * 0.5, screen_height * 0.15))
        screen.blit(insult_text, insult_rect)

    # Check for new high score
    if average_force > highest_score:
        highest_score = average_force
        write_high_score(highest_score)
        
        congrats_text = font_medium.render("New High Score! Congratulations!", True, GREEN)
        congrats_rect = congrats_text.get_rect(center=(screen_width * 0.5, screen_height * 0.8))
        screen.blit(congrats_text, congrats_rect)
        
        high_score_text = font_medium.render(f"High Score: {highest_score}", True, GREEN)
        screen.blit(high_score_text, (screen_width * 0.5 - high_score_text.get_width() / 2, 
                    screen_height * 0.85))

    pygame.display.flip()
    current_state = "update"
    update_screen_timer = time.time()

def read_serial_data():
    """Main loop for reading serial data"""
    while True:
        global minimum_threshold
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                parts = line.split(",")
                if len(parts) == 3:
                    fsr1_str = parts[0].split(": ")[1]
                    fsr2_str = parts[1].split(": ")[1]
                    fsr1 = int(fsr1_str)
                    fsr2 = int(fsr2_str)
                    
                    if fsr1 > minimum_threshold and fsr2 > minimum_threshold:
                        average_force = (fsr1 + fsr2) / 2
                    elif fsr1 < minimum_threshold:
                        average_force = fsr2
                    elif fsr2 < minimum_threshold:
                        average_force = fsr1
                    else:
                        continue
                        
                    print("average force", average_force)
                    if average_force >= 650 and current_state == "initial":
                        update_display(fsr1, fsr2, average_force)
        except (ValueError, IndexError):
            continue

# Start serial reading thread
serial_thread = threading.Thread(target=read_serial_data)
serial_thread.daemon = True
serial_thread.start()

# Initial display
display_username_input()

# Main game loop
while True:
    try:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                if current_state == "username_input":
                    display_username_input()
                elif current_state == "leaderboard":
                    display_leaderboard()
                else:
                    display_initial_screen()
            elif event.type == pygame.KEYDOWN:
                if current_state == "username_input":
                    if event.key == pygame.K_RETURN:
                        if current_username.strip():
                            current_state = "initial"
                            input_active = False
                            display_initial_screen()
                    elif event.key == pygame.K_BACKSPACE:
                        current_username = current_username[:-1]
                        display_username_input()
                    elif event.key == pygame.K_l:
                        current_state = "leaderboard"
                        display_leaderboard()
                    elif event.unicode.isprintable() and len(current_username) < 20:
                        current_username += event.unicode
                        display_username_input()
                elif current_state == "leaderboard":
                    if event.key == pygame.K_b or event.key == pygame.K_ESCAPE:
                        current_state = "username_input"
                        display_username_input()
                elif current_state == "initial":
                    if event.key == pygame.K_l:
                        current_state = "leaderboard"
                        display_leaderboard()
                    elif event.key == pygame.K_u:
                        current_state = "username_input"
                        current_username = ""
                        input_active = True
                        display_username_input()

        # Return to initial screen after showing score
        if current_state == "update" and time.time() - update_screen_timer > update_screen_display_time:
            display_initial_screen()

    except KeyboardInterrupt:
        print("Exiting...")
        break
