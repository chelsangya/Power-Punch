import serial
import pygame
import sys
import json
import os
import time
import threading
import random
import math
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import punch animation
from punch_animation2 import animate_punch_score, create_responsive_layout

# Serial setup with error handling
try:
    ser = serial.Serial('/dev/cu.usbmodem1301', 9600)
    SERIAL_CONNECTED = True
    print("Arduino connected successfully!")
except Exception as e:
    print(f"Arduino not connected: {e}")
    print("Running in demo mode - use keyboard to simulate punches!")
    SERIAL_CONNECTED = False
    ser = None

# MongoDB setup
try:
    mongodb_uri = os.getenv('MONGODB_URI')
    local_mongodb_uri = os.getenv('LOCAL_MONGODB_URI', 'mongodb://localhost:27017/')
    database_name = os.getenv('DATABASE_NAME', 'boxing_game')
    collection_name = os.getenv('COLLECTION_NAME', 'scores')
    
    if not mongodb_uri:
        raise Exception("MONGODB_URI not found in .env file")
    
    client = MongoClient(mongodb_uri)
    
    # Test the connection
    client.admin.command('ping')
    
    db = client[database_name]
    scores_collection = db[collection_name]
    print("Connected to MongoDB Atlas successfully")
except Exception as e:
    print(f"MongoDB Atlas connection failed: {e}")
    print("Falling back to local MongoDB...")
    try:
        # Fallback to local MongoDB
        client = MongoClient(local_mongodb_uri)
        client.admin.command('ping')
        db = client[database_name]
        scores_collection = db[collection_name]
        print("Connected to local MongoDB successfully")
    except Exception as local_e:
        print(f"Local MongoDB also failed: {local_e}")
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

# Colors - Professional Boxing Arena Theme
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
# Professional Boxing Colors - Blue and Red Theme
BOXING_BLUE = (30, 50, 120)       # Professional boxing blue
BOXING_RED = (180, 25, 25)        # Professional boxing red
RING_BLUE = (40, 80, 150)         # Ring corner blue
RING_RED = (200, 40, 40)          # Ring corner red
# Championship and Medal Colors
CHAMPION_GOLD = (255, 215, 0)     # Championship belt gold
SILVER = (192, 192, 192)          # Silver medal
BRONZE = (205, 127, 50)           # Bronze medal
# Arena Colors
ARENA_BLUE = (20, 35, 80)         # Arena background blue
ARENA_RED = (120, 20, 20)         # Arena background red
CANVAS_WHITE = (250, 250, 250)    # Clean ring canvas
# Professional Equipment Colors
STEEL_GRAY = (100, 100, 100)      # Professional equipment
LEATHER_BLACK = (40, 40, 40)      # Professional gloves
PRO_ORANGE = (255, 140, 0)        # Professional accent
TEXT_BLUE = (60, 100, 180)        # Professional text blue

minimum_threshold = 305

# State management - Enhanced with new player feature
current_state = "username_input"  # Start with username input
update_screen_display_time = 8  # seconds
update_screen_timer = 0
current_username = ""
input_active = True
show_leaderboard = False
show_new_player_button = False
button_rects = {}  # Store button rectangles for click detection
mouse_pos = (0, 0)  # Track mouse position for hover effects

# Animation state management
animation_active = False
animation_target_score = 0
animation_start_time = 0
animation_duration = 2.5

# Fonts - Enhanced typography with better sizing
font_title = pygame.font.Font(None, 80)   # Reduced from 120
font_large = pygame.font.Font(None, 60)   # Reduced from 90
font_medium = pygame.font.Font(None, 40)  # Reduced from 50
font_small = pygame.font.Font(None, 28)   # Reduced from 36
font_tiny = pygame.font.Font(None, 20)    # Reduced from 24

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

# Utility functions for UI
def draw_button(surface, text, x, y, width, height, color, text_color, border_color=None, hover=False):
    """Draw a modern button with rounded corners and optional hover effect"""
    button_rect = pygame.Rect(x, y, width, height)
    
    # Add hover effect
    if hover:
        color = tuple(min(255, c + 30) for c in color)
    
    # Draw button background with rounded corners
    pygame.draw.rect(surface, color, button_rect, border_radius=15)
    
    # Draw border if specified
    if border_color:
        pygame.draw.rect(surface, border_color, button_rect, 3, border_radius=15)
    
    # Draw text centered on button
    text_surface = font_medium.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=button_rect.center)
    surface.blit(text_surface, text_rect)
    
    return button_rect

def draw_card(surface, x, y, width, height, color=WHITE, border_color=STEEL_GRAY):
    """Draw a modern card with shadow effect"""
    # Draw shadow
    shadow_rect = pygame.Rect(x + 5, y + 5, width, height)
    pygame.draw.rect(surface, STEEL_GRAY, shadow_rect, border_radius=20)
    
    # Draw main card
    card_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, color, card_rect, border_radius=20)
    pygame.draw.rect(surface, border_color, card_rect, 2, border_radius=20)
    
    return card_rect

def draw_gradient_background(surface, color1, color2):
    """Draw a gradient background"""
    for y in range(screen_height):
        ratio = y / screen_height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (screen_width, y))

def draw_simple_button(surface, text, x, y, width, height, color, text_color, hover=False):
    """Draw a simple professional button"""
    button_rect = pygame.Rect(x, y, width, height)
    
    # Hover effect
    if hover:
        color = tuple(min(255, c + 30) for c in color)
    
    # Simple button
    pygame.draw.rect(surface, color, button_rect)
    pygame.draw.rect(surface, text_color, button_rect, 3)
    
    # Text
    text_surface = font_medium.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=button_rect.center)
    surface.blit(text_surface, text_rect)
    
    return button_rect

def draw_leaderboard_sidebar(sidebar_width):
    """Draw professional boxing leaderboard with blue and red theme"""
    # Calculate sidebar position (right side)
    sidebar_x = screen_width - sidebar_width
    
    # Professional blue gradient background
    for x in range(sidebar_width):
        ratio = x / sidebar_width
        r = int(ARENA_BLUE[0] * (1 - ratio) + BOXING_BLUE[0] * ratio)
        g = int(ARENA_BLUE[1] * (1 - ratio) + BOXING_BLUE[1] * ratio)
        b = int(ARENA_BLUE[2] * (1 - ratio) + BOXING_BLUE[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (sidebar_x + x, 0), (sidebar_x + x, screen_height))
    
    # Clean border - no effects
    pygame.draw.line(screen, BOXING_RED, (sidebar_x, 0), (sidebar_x, screen_height), 4)
    
    # Header section
    header_height = 80
    header_rect = pygame.Rect(sidebar_x, 0, sidebar_width, header_height)
    pygame.draw.rect(screen, BOXING_RED, header_rect)
    
    # Simple title
    title_text = font_large.render("LEADERBOARD", True, WHITE)
    title_rect = title_text.get_rect(center=(sidebar_x + sidebar_width // 2, 40))
    screen.blit(title_text, title_rect)
    
    # Get leaderboard data
    leaderboard = get_leaderboard()
    
    if leaderboard:
        # Table header
        header_y = 90
        header_bg = pygame.Rect(sidebar_x + 10, header_y, sidebar_width - 20, 35)
        pygame.draw.rect(screen, CANVAS_WHITE, header_bg)
        pygame.draw.rect(screen, BLACK, header_bg, 2)
        
        # Header text
        rank_text = font_small.render("RANK", True, BLACK)
        name_text = font_small.render("NAME", True, BLACK)
        score_text = font_small.render("SCORE", True, BLACK)
        
        screen.blit(rank_text, (sidebar_x + 20, header_y + 10))
        screen.blit(name_text, (sidebar_x + 80, header_y + 10))
        screen.blit(score_text, (sidebar_x + sidebar_width - 80, header_y + 10))

        entry_y = header_y + 40
        entry_height = 30
        
        for i, entry in enumerate(leaderboard[:10]):
            rank = i + 1
            username = entry["username"]
            score = entry["score"]
            
            # Simple alternating backgrounds
            if rank == 1:
                bg_color = CHAMPION_GOLD
                text_color = BLACK
            elif rank == 2:
                bg_color = SILVER
                text_color = BLACK
            elif rank == 3:
                bg_color = BRONZE
                text_color = BLACK
            else:
                bg_color = CANVAS_WHITE if i % 2 == 0 else (240, 240, 240)
                text_color = BLACK
            
            entry_rect = pygame.Rect(sidebar_x + 10, entry_y, sidebar_width - 20, entry_height)
            pygame.draw.rect(screen, bg_color, entry_rect)
            pygame.draw.rect(screen, BLACK, entry_rect, 1)
            
            # Simple text positioning
            rank_surface = font_small.render(f"{rank}", True, text_color)
            name_surface = font_small.render(username[:8], True, text_color)
            score_surface = font_small.render(str(score), True, text_color)
            
            screen.blit(rank_surface, (sidebar_x + 25, entry_y + 8))
            screen.blit(name_surface, (sidebar_x + 80, entry_y + 8))
            screen.blit(score_surface, (sidebar_x + sidebar_width - 75, entry_y + 8))
            
            entry_y += entry_height + 2
    
    else:
        no_data_text = font_medium.render("NO SCORES YET", True, WHITE)
        no_data_rect = no_data_text.get_rect(center=(sidebar_x + sidebar_width // 2, 200))
        screen.blit(no_data_text, no_data_rect)


def display_username_input():
    """Display username input with top leaderboard and bottom input section"""
    global current_username, input_active, button_rects
    
    # Play background music
    if not pygame.mixer.music.get_busy():
        try:
            pygame.mixer.music.load("wait_at_0.mp3")
            pygame.mixer.music.play(-1)
            print("Playing wait_at_0.mp3 in loop")
        except pygame.error as e:
            print(f"Could not load wait_at_0.mp3: {e}")
        except FileNotFoundError:
            print("wait_at_0.mp3 not found")
    
    button_rects.clear()
    
    # Professional boxing arena background - Red and Blue split
    # Top half - Blue arena
    top_rect = pygame.Rect(0, 0, screen_width, screen_height // 2)
    pygame.draw.rect(screen, ARENA_BLUE, top_rect)
    
    # Bottom half - Red arena  
    bottom_rect = pygame.Rect(0, screen_height // 2, screen_width, screen_height // 2)
    pygame.draw.rect(screen, ARENA_RED, bottom_rect)
    
    # Center dividing line
    pygame.draw.line(screen, WHITE, (0, screen_height // 2), (screen_width, screen_height // 2), 6)
    
    # TOP SECTION - Title and Leaderboard
    title_y = 40
    subtitle_text = font_large.render("Current Champions", True, CHAMPION_GOLD)
    
    subtitle_rect = subtitle_text.get_rect(center=(screen_width // 2, title_y + 50))
    

    # Horizontal leaderboard in top section
    leaderboard_y = 120
    leaderboard = get_leaderboard()
    
    if leaderboard:
        # Header
        screen.blit(subtitle_text, subtitle_rect)
        
        # Show top 5 horizontally with improved design
        top_5 = leaderboard[:5]
        card_width = min(200, (screen_width - 120) // 5)
        card_height = 120
        spacing = 25
        total_width = len(top_5) * card_width + (len(top_5) - 1) * spacing
        start_x = (screen_width - total_width) // 2
        card_y = leaderboard_y + 40
        
        for i, entry in enumerate(top_5):
            card_x = start_x + i * (card_width + spacing)
            
            # Enhanced card design with modern styling
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            # Enhanced shadow for depth
            shadow_rect = pygame.Rect(card_x + 4, card_y + 4, card_width, card_height)
            pygame.draw.rect(screen, (30, 30, 30), shadow_rect, border_radius=15)
            
            # Gradient-like effect with lighter border
            card_color = CANVAS_WHITE
            border_color = STEEL_GRAY
            text_color = BLACK
            rank_number = f"#{i+1}"
                
            pygame.draw.rect(screen, card_color, card_rect, border_radius=15)
            pygame.draw.rect(screen, border_color, card_rect, 2, border_radius=15)
            
            # Top section - Rank with background circle
            rank_circle_center = (card_x + card_width // 2, card_y + 30)
            rank_circle_radius = 18
            # pygame.draw.circle(screen, BOXING_BLUE, rank_circle_center, rank_circle_radius)
            # pygame.draw.circle(screen, WHITE, rank_circle_center, rank_circle_radius - 2)
            
            # Rank number in circle
            rank_text = font_small.render(rank_number, True, BOXING_BLUE)
            rank_rect = rank_text.get_rect(center=rank_circle_center)
            # screen.blit(rank_text, rank_rect)
            
            # Middle section - Fighter name with better spacing
            name_y = card_y + 40
            name_text = font_medium.render(entry["username"][:10], True, text_color)
            name_rect = name_text.get_rect(center=(card_x + card_width // 2, name_y))
            screen.blit(name_text, name_rect)
            
            # Bottom section - Score with background
            score_bg_rect = pygame.Rect(card_x + 10, card_y + 75, card_width - 20, 35)
            pygame.draw.rect(screen, BOXING_BLUE, score_bg_rect, border_radius=8)
            
            # Score text in white on blue background
            score_text = font_medium.render(str(entry["score"]), True, WHITE)
            score_rect = score_text.get_rect(center=score_bg_rect.center)
            screen.blit(score_text, score_rect)
    
    # BOTTOM SECTION - Username Input
    input_section_y = screen_height // 2 + 100
    
    # Input prompt
    prompt_text = font_large.render("ENTER FIGHTER NAME", True, WHITE)
    prompt_rect = prompt_text.get_rect(center=(screen_width // 2, input_section_y))
    screen.blit(prompt_text, prompt_rect)
    
    # Username input box - centered
    input_box_width = 400
    input_box_height = 60
    input_box_x = (screen_width - input_box_width) // 2
    input_box_y = input_section_y + 60
    
    input_box_rect = pygame.Rect(input_box_x, input_box_y, input_box_width, input_box_height)
    
    # Clean input box styling
    box_color = CANVAS_WHITE if input_active else (220, 220, 220)
    pygame.draw.rect(screen, box_color, input_box_rect)
    pygame.draw.rect(screen, BLACK, input_box_rect, 3)
    
    # Username text
    username_text = font_medium.render(current_username, True, BLACK)
    text_x = input_box_rect.x + 15
    text_y = input_box_rect.y + (input_box_rect.height - username_text.get_height()) // 2
    screen.blit(username_text, (text_x, text_y))
    
    # Simple cursor
    if input_active and int(time.time() * 2) % 2:
        cursor_x = text_x + username_text.get_width() + 5
        cursor_y = input_box_rect.y + 15
        pygame.draw.line(screen, BLACK, (cursor_x, cursor_y), (cursor_x, cursor_y + 30), 2)
    
    pygame.display.flip()

def display_initial_screen():
    """Display main game screen with horizontal split layout"""
    global current_state, update_screen_timer, button_rects
    
    # Continue playing wait music
    if not pygame.mixer.music.get_busy():
        try:
            pygame.mixer.music.load("wait_at_0.mp3")
            pygame.mixer.music.play(-1)
            print("Playing wait_at_0.mp3 in loop")
        except pygame.error as e:
            print(f"Could not load wait_at_0.mp3: {e}")
        except FileNotFoundError:
            print("wait_at_0.mp3 not found")
    
    button_rects.clear()
    
    # Split screen horizontally - Left Blue, Right Red
    left_width = screen_width // 2
    
    # Left side - Blue scoring area
    left_rect = pygame.Rect(0, 0, left_width, screen_height)
    pygame.draw.rect(screen, ARENA_BLUE, left_rect)
    
    # Right side - Red leaderboard area
    right_rect = pygame.Rect(left_width, 0, screen_width - left_width, screen_height)
    pygame.draw.rect(screen, ARENA_RED, right_rect)
    
    # Center dividing line
    pygame.draw.line(screen, WHITE, (left_width, 0), (left_width, screen_height), 6)
    
    # LEFT SIDE - Score Display
    if current_username:
        # Title
        score_title = font_large.render("PUNCH POWER", True, WHITE)
        title_rect = score_title.get_rect(center=(left_width // 2, 80))
        screen.blit(score_title, title_rect)
        
        # Large score circle - clean and simple
        circle_center_x = left_width // 2
        circle_center_y = screen_height // 2
        circle_radius = 120
        
        # Outer circle
        pygame.draw.circle(screen, WHITE, (circle_center_x, circle_center_y), circle_radius, 6)
        
        # Inner circle
        inner_radius = circle_radius - 10
        pygame.draw.circle(screen, BOXING_BLUE, (circle_center_x, circle_center_y), inner_radius)
        
        # Score text
        big_score_font = pygame.font.Font(None, 150)
        score_text = big_score_font.render("0", True, WHITE)
        score_rect = score_text.get_rect(center=(circle_center_x, circle_center_y))
        screen.blit(score_text, score_rect)
        
        # Your score label
        label_text = font_medium.render("YOUR SCORE", True, WHITE)
        label_rect = label_text.get_rect(center=(circle_center_x, circle_center_y - circle_radius - 40))
        screen.blit(label_text, label_rect)
    
    # Target information at bottom left
    target_y = screen_height - 120
    target_info = [
        "TARGET ZONES:",
        "650+ = Good Hit",
        "865+ = Great Hit",
        "1000+ = Champion!"
    ]
    
    # for i, line in enumerate(target_info):
    #     color = CHAMPION_GOLD if i == 0 else WHITE
    #     font = font_medium if i == 0 else font_small
    #     text = font.render(line, True, color)
    #     text_rect = text.get_rect(center=(left_width // 2, target_y + i * 25))
    #     screen.blit(text, text_rect)
    
    # Demo mode instructions
    if not SERIAL_CONNECTED:
        demo_y = target_y + 120
        demo_text = font_tiny.render("DEMO: Press SPACE or 1/2/3 for test punches", True, PRO_ORANGE)
        demo_rect = demo_text.get_rect(center=(left_width // 2, demo_y))
        screen.blit(demo_text, demo_rect)
    
    # RIGHT SIDE - Leaderboard
    right_center = left_width + (screen_width - left_width) // 2
    
    # Leaderboard title
    leaderboard_title = font_large.render("HALL OF FAME", True, WHITE)
    title_rect = leaderboard_title.get_rect(center=(right_center, 60))
    screen.blit(leaderboard_title, title_rect)
    
    # Leaderboard content
    leaderboard = get_leaderboard()
    if leaderboard:
        start_y = 120
        
        # Table headers
        headers_y = start_y
        rank_x = left_width + 30
        name_x = left_width + 100
        score_x = left_width + 250
        
        # Header background
        header_rect = pygame.Rect(left_width + 20, headers_y, screen_width - left_width - 40, 40)
        pygame.draw.rect(screen, CANVAS_WHITE, header_rect)
        pygame.draw.rect(screen, BLACK, header_rect, 2)
        
        rank_header = font_small.render("RANK", True, BLACK)
        name_header = font_small.render("FIGHTER", True, BLACK)
        score_header = font_small.render("POWER", True, BLACK)
        
        screen.blit(rank_header, (rank_x, headers_y + 12))
        screen.blit(name_header, (name_x, headers_y + 12))
        screen.blit(score_header, (score_x, headers_y + 12))
        
        # Leaderboard entries - Show only top 5
        entry_y = headers_y + 50
        for i, entry in enumerate(leaderboard[:5]):
            rank = i + 1
            username = entry["username"]
            score = entry["score"]
            
            # Enhanced row background with better height
            row_height = 45
            row_rect = pygame.Rect(left_width + 20, entry_y, screen_width - left_width - 40, row_height)
            
            # Uniform color scheme for all ranks
            if rank == 1:
                row_color = CHAMPION_GOLD
                text_color = BLACK
                rank_display = "1st"
            elif rank == 2:
                row_color = SILVER
                text_color = BLACK
                rank_display = "2nd"
            elif rank == 3:
                row_color = BRONZE
                text_color = BLACK
                rank_display = "3rd"
            elif rank == 4:
                row_color = CANVAS_WHITE
                text_color = BLACK
                rank_display = "4th"
            else:
                row_color = CANVAS_WHITE
                text_color = BLACK
                rank_display = "5th"
            
            pygame.draw.rect(screen, row_color, row_rect, border_radius=8)
            pygame.draw.rect(screen, BLACK, row_rect, 2, border_radius=8)
            
            # Enhanced text with better formatting
            rank_text = font_small.render(rank_display, True, text_color)
            name_text = font_small.render(username[:15], True, text_color)
            score_text = font_medium.render(str(score), True, text_color)
            
            # Better text positioning
            screen.blit(rank_text, (rank_x, entry_y + 12))
            screen.blit(name_text, (name_x, entry_y + 12))
            screen.blit(score_text, (score_x, entry_y + 10))
            
            entry_y += row_height + 8  # Increased spacing between rows
    else:
        no_data_text = font_medium.render("NO CHAMPIONS YET", True, WHITE)
        no_data_rect = no_data_text.get_rect(center=(right_center, 200))
        screen.blit(no_data_text, no_data_rect)
    
    pygame.display.flip()
    current_state = "initial"
    update_screen_timer = 0

def update_display(fsr1, fsr2, average_force):
    """Update display after a punch with enhanced UI and permanent leaderboard"""
    global highest_score, last_update_time, current_state, update_screen_timer, button_rects
    global animation_active, animation_target_score, animation_start_time
    
    current_time = time.time()

    if current_time - last_update_time < UPDATE_DELAY:
        return

    last_update_time = current_time
    
    # Store score to MongoDB first
    if current_username:
        store_score_to_mongodb(current_username, average_force)
    
    # Start animation by setting animation state
    animation_active = True
    animation_target_score = int(average_force)
    animation_start_time = current_time
    current_state = "animating"

def show_punch_result_screen(average_force):
    """Show full-screen leaderboard after punch"""
    global current_state, update_screen_timer, button_rects
    
    # Clear button rects
    button_rects.clear()
    
    # Play final score sound
    try:
        pygame.mixer.music.load("final_score.mp3")
        pygame.mixer.music.play(0)  # Play once only
        print("Playing final_score.mp3")
    except pygame.error as e:
        print(f"Could not load final_score.mp3: {e}")
    except FileNotFoundError:
        print("final_score.mp3 not found")
    
    # Draw boxing gym atmosphere background
    screen.fill((25, 20, 15))
    
    # Draw full-screen leaderboard
    draw_fullscreen_leaderboard(current_username, average_force)

    pygame.display.flip()
    current_state = "punch_result"
    update_screen_timer = time.time()

def draw_fullscreen_leaderboard(username, force):
    """Draw professional full-screen leaderboard with enhanced UI design"""
    # Create gradient background
    for y in range(screen_height):
        color_value = max(15, min(45, 15 + (y * 30) // screen_height))
        pygame.draw.line(screen, (color_value, color_value * 0.8, color_value * 0.6), (0, y), (screen_width, y))
    
    # Enhanced title section with shadow and glow effect
    title_bg_rect = pygame.Rect(0, 0, screen_width, 120)
    pygame.draw.rect(screen, (20, 15, 15), title_bg_rect)
    pygame.draw.rect(screen, BOXING_RED, (0, 0, screen_width, 8))
    pygame.draw.rect(screen, CHAMPION_GOLD, (0, 112, screen_width, 8))
    
    # Title with shadow effect
    title_shadow = font_title.render("FIGHT RESULTS", True, BLACK)
    title_text = font_title.render("FIGHT RESULTS", True, WHITE)
    title_rect = title_text.get_rect(center=(screen_width // 2, 60))
    screen.blit(title_shadow, (title_rect.x + 3, title_rect.y + 3))
    screen.blit(title_text, title_rect)
    
    # User's enhanced score section
    if username and force > 0:
        score_y = 150
        
        # Main score card with gradient and shadow
        card_width = 700
        card_height = 120
        card_x = (screen_width - card_width) // 2
        
        # Card shadow
        shadow_rect = pygame.Rect(card_x + 6, score_y + 6, card_width, card_height)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=15)
        
        # Main card background
        card_rect = pygame.Rect(card_x, score_y, card_width, card_height)
        
        # Determine performance colors and text
        if force >= 1000:
            card_color = CHAMPION_GOLD
            accent_color = (255, 215, 0)
            perf_text = "CHAMPION LEVEL!"
            perf_icon = "👑"
        elif force >= 865:
            card_color = SILVER
            accent_color = (192, 192, 192)
            perf_text = "EXCELLENT HIT!"
            perf_icon = "⭐"
        elif force >= 650:
            card_color = BRONZE
            accent_color = (205, 127, 50)
            perf_text = "GOOD HIT!"
            perf_icon = "💪"
        else:
            card_color = CANVAS_WHITE
            accent_color = (150, 150, 150)
            perf_text = "KEEP TRAINING!"
            perf_icon = "🥊"
        
        pygame.draw.rect(screen, card_color, card_rect, border_radius=15)
        pygame.draw.rect(screen, BLACK, card_rect, 4, border_radius=15)
        
        # Accent border inside
        inner_rect = pygame.Rect(card_x + 8, score_y + 8, card_width - 16, card_height - 16)
        pygame.draw.rect(screen, accent_color, inner_rect, 2, border_radius=10)
        
        # Player name section
        name_label = font_small.render("FIGHTER:", True, BLACK)
        name_text = font_large.render(f"{username}", True, BLACK)
        screen.blit(name_label, (card_x + 30, score_y + 20))
        screen.blit(name_text, (card_x + 30, score_y + 45))
        
        # Score section with larger font
        score_label = font_small.render("POWER SCORE:", True, BLACK)
        score_text = font_title.render(f"{int(force)}", True, BLACK)
        score_x = card_x + card_width - 200
        screen.blit(score_label, (score_x, score_y + 20))
        screen.blit(score_text, (score_x, score_y + 45))
        
        # Performance banner below card
        banner_y = score_y + card_height + 20
        banner_width = 500
        banner_height = 50
        banner_x = (screen_width - banner_width) // 2
        
        banner_rect = pygame.Rect(banner_x, banner_y, banner_width, banner_height)
        pygame.draw.rect(screen, accent_color, banner_rect, border_radius=25)
        pygame.draw.rect(screen, BLACK, banner_rect, 3, border_radius=25)
        
        perf_final_text = font_medium.render(perf_text, True, BLACK)
        perf_rect = perf_final_text.get_rect(center=(screen_width // 2, banner_y + 25))
        screen.blit(perf_final_text, perf_rect)
    
    # Enhanced leaderboard table
    table_y = 300
    leaderboard = get_leaderboard()
    
    if leaderboard:
        # Leaderboard title with decorative elements
        leaderboard_title = font_large.render("TOP CHAMPIONS", True, WHITE)
        title_bg_width = leaderboard_title.get_width() + 60
        title_bg_rect = pygame.Rect((screen_width - title_bg_width) // 2, table_y - 10, title_bg_width, 50)
        # pygame.draw.rect(screen, (40, 30, 25), title_bg_rect, border_radius=25)
        # pygame.draw.rect(screen, CHAMPION_GOLD, title_bg_rect, 3, border_radius=25)
        
        title_rect = leaderboard_title.get_rect(center=(screen_width // 2, table_y + 15))
        # screen.blit(leaderboard_title, title_rect)
        
        # Enhanced table setup
        table_start_y = table_y + 70
        table_width = min(850, screen_width - 80)
        table_x = (screen_width - table_width) // 2
        
        # Column positions with better spacing
        rank_col = table_x + 40
        name_col = table_x + 150
        score_col = table_x + 650
        
        # Enhanced table header
        header_rect = pygame.Rect(table_x, table_start_y, table_width, 60)
        pygame.draw.rect(screen, (30, 25, 20), header_rect, border_radius=10)
        pygame.draw.rect(screen, CHAMPION_GOLD, header_rect, 4, border_radius=10)
        
        rank_header = font_medium.render("RANK", True, CHAMPION_GOLD)
        name_header = font_medium.render("FIGHTER", True, CHAMPION_GOLD)
        score_header = font_medium.render("POWER", True, CHAMPION_GOLD)
        
        screen.blit(rank_header, (rank_col, table_start_y + 18))
        screen.blit(name_header, (name_col, table_start_y + 18))
        screen.blit(score_header, (score_col, table_start_y + 18))
        
        # Enhanced table entries - Show only top 5
        entry_start_y = table_start_y + 70
        row_height = 65  # Increased for better visual appeal
        
        for i, entry in enumerate(leaderboard[:5]):
            rank = i + 1
            entry_username = entry["username"]
            score = entry["score"]
            
            entry_y = entry_start_y + (i * row_height)
            row_rect = pygame.Rect(table_x + 5, entry_y, table_width - 10, row_height - 8)
            
            # Check if current user
            is_current_user = (entry_username == username and abs(score - force) < 10)
            
            # Enhanced row styling with medal colors and effects
            if rank == 1:
                row_color = CHAMPION_GOLD
                text_color = BLACK
                rank_display = "1"
                shadow_color = (255, 215, 0, 50)
            elif rank == 2:
                row_color = SILVER  
                text_color = BLACK
                rank_display = "2"
                shadow_color = (192, 192, 192, 50)
            elif rank == 3:
                row_color = BRONZE
                text_color = BLACK
                rank_display = "3"
                shadow_color = (205, 127, 50, 50)
            else:
                row_color = (240, 240, 240) if not is_current_user else PRO_ORANGE
                text_color = BLACK
                rank_display = f"#{rank}"
                shadow_color = (100, 100, 100, 30)
            
            # Row shadow
            shadow_rect = pygame.Rect(row_rect.x + 3, row_rect.y + 3, row_rect.width, row_rect.height)
            pygame.draw.rect(screen, shadow_color[:3], shadow_rect, border_radius=12)
            
            # Main row
            pygame.draw.rect(screen, row_color, row_rect, border_radius=12)
            pygame.draw.rect(screen, BLACK, row_rect, 3, border_radius=12)
            
            # Highlight current user with glow effect
            if is_current_user:
                glow_rect = pygame.Rect(row_rect.x - 3, row_rect.y - 3, row_rect.width + 6, row_rect.height + 6)
                pygame.draw.rect(screen, PRO_ORANGE, glow_rect, 2, border_radius=15)
            
            # Enhanced row content with larger fonts
            if rank <= 3:
                rank_text = font_medium.render(rank_display, True, text_color)
            else:
                rank_text = font_medium.render(rank_display, True, text_color)
            
            name_text = font_medium.render(entry_username[:18], True, text_color)
            score_text = font_medium.render(str(int(score)), True, text_color)
            
            # Better text positioning with perfect vertical centering
            text_y_offset = (row_height - 30) // 2
            screen.blit(rank_text, (rank_col, entry_y + text_y_offset))
            screen.blit(name_text, (name_col, entry_y + text_y_offset))
            screen.blit(score_text, (score_col, entry_y + text_y_offset))
    
    else:
        # Enhanced "no data" message
        no_data_bg = pygame.Rect((screen_width - 600) // 2, table_y + 50, 600, 100)
        pygame.draw.rect(screen, (40, 30, 25), no_data_bg, border_radius=20)
        pygame.draw.rect(screen, BOXING_RED, no_data_bg, 3, border_radius=20)
        
        no_data_text = font_large.render("NO FIGHTERS YET", True, WHITE)
        be_first_text = font_medium.render("BE THE FIRST CHAMPION!", True, CHAMPION_GOLD)
        
        no_data_rect = no_data_text.get_rect(center=(screen_width // 2, table_y + 80))
        be_first_rect = be_first_text.get_rect(center=(screen_width // 2, table_y + 110))
        
        screen.blit(no_data_text, no_data_rect)
        screen.blit(be_first_text, be_first_rect)
    
    # Enhanced bottom instruction with animated effect
    instruction_bg = pygame.Rect((screen_width - 400) // 2, screen_height - 80, 400, 50)
    # pygame.draw.rect(screen, (20, 15, 15), instruction_bg, border_radius=25)
    # pygame.draw.rect(screen, WHITE, instruction_bg, 2, border_radius=25)
    
    instruction_text = font_medium.render("Press any key to continue...", True, WHITE)
    instruction_rect = instruction_text.get_rect(center=(screen_width // 2, screen_height - 55))
    # screen.blit(instruction_text, instruction_rect)
 

def read_serial_data():
    """Main loop for reading serial data with robust error handling"""
    global SERIAL_CONNECTED, ser
    
    if not SERIAL_CONNECTED:
        print("Demo mode: No serial data will be read")
        return
        
    reconnect_attempts = 0
    max_reconnect_attempts = 3
    
    while True:
        try:
            # Check if serial connection is still valid
            if ser is None or not ser.is_open:
                raise serial.SerialException("Serial connection lost")
                
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
                        
                # Reset reconnect attempts on successful read
                reconnect_attempts = 0
                
        except (ValueError, IndexError):
            # Data parsing errors - continue trying
            continue
            
        except (serial.SerialException, OSError) as e:
            print(f"Serial connection error: {e}")
            
            # Try to reconnect
            if reconnect_attempts < max_reconnect_attempts:
                reconnect_attempts += 1
                print(f"Attempting to reconnect... (attempt {reconnect_attempts}/{max_reconnect_attempts})")
                
                try:
                    if ser and ser.is_open:
                        ser.close()
                    
                    # Wait a bit before reconnecting
                    import time
                    time.sleep(2)
                    
                    # Try to reconnect
                    ser = serial.Serial('/dev/cu.usbmodem1301', 9600)
                    print("Reconnected to Arduino successfully!")
                    reconnect_attempts = 0  # Reset on successful reconnection
                    
                except Exception as reconnect_error:
                    print(f"Reconnection failed: {reconnect_error}")
                    if reconnect_attempts >= max_reconnect_attempts:
                        print("Max reconnection attempts reached. Switching to demo mode.")
                        SERIAL_CONNECTED = False
                        ser = None
                        break
            else:
                print("Serial connection permanently lost. Switching to demo mode.")
                SERIAL_CONNECTED = False
                ser = None
                break
                
        except Exception as e:
            print(f"Unexpected error in serial reading: {e}")
            # Wait a bit and continue
            import time
            time.sleep(1)

def handle_button_click(click_pos):
    """Handle mouse clicks on buttons"""
    global current_state, current_username, input_active
    
    for button_name, button_rect in button_rects.items():
        if button_rect.collidepoint(click_pos):
            print(f"Button clicked: {button_name}")
            
            if button_name == "start":
                if current_username.strip():
                    current_state = "initial"
                    input_active = False
                    display_initial_screen()
            
            elif button_name == "new_player":
                current_state = "username_input"
                current_username = ""
                input_active = True
                display_username_input()
            
            elif button_name == "demo":
                if not SERIAL_CONNECTED:
                    # Simulate a random punch for demo
                    simulated_score = random.randint(650, 1000)
                    print(f"Demo punch: {simulated_score}")
                    update_display(simulated_score//2, simulated_score//2, simulated_score)
            
            break  # Only handle one button click at a time

# Start serial reading thread only if connected
if SERIAL_CONNECTED:
    serial_thread = threading.Thread(target=read_serial_data)
    serial_thread.daemon = True
    serial_thread.start()
    print("Serial reading thread started")
else:
    print("Demo mode active - use keyboard controls!")

def display_animation_screen():
    """Display the punch animation screen"""
    global current_state, animation_active, animation_target_score
    
    try:
        print(f"Starting animation with target score: {animation_target_score}")
        
        # Stop wait music when animation starts
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            print("Stopped wait_at_0.mp3 - animation starting")
        
        # Create fonts dictionary for animate_punch_score function
        fonts = {
            'title': font_title,
            'large': font_large,
            'medium': font_medium,
            'small': font_small,
            'tiny': font_tiny
        }
        
        # Use the proper animation function with sound from punch_animation2.py
        animate_punch_score(screen, animation_target_score, screen_width, screen_height, fonts)
        
        print("Animation completed")
        
        # Animation completed
        animation_active = False
        show_punch_result_screen(animation_target_score)
        
    except Exception as e:
        print(f"Animation error: {e}")
        import traceback
        traceback.print_exc()
        animation_active = False
        show_punch_result_screen(animation_target_score)

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
                    elif event.unicode.isprintable() and len(current_username) < 20:
                        current_username += event.unicode
                        display_username_input()
                elif current_state == "initial":
                    if event.key == pygame.K_u:
                        current_state = "username_input"
                        current_username = ""
                        input_active = True
                        display_username_input()
                    # Demo mode: Simulate punches with keyboard
                    elif not SERIAL_CONNECTED:
                        if event.key == pygame.K_SPACE:
                            # Simulate a random punch
                            simulated_score = random.randint(650, 1000)
                            print(f"Demo punch: {simulated_score}")
                            update_display(simulated_score//2, simulated_score//2, simulated_score)
                        elif event.key == pygame.K_1:
                            # Weak punch
                            update_display(300, 300, 600)
                        elif event.key == pygame.K_2:
                            # Medium punch  
                            update_display(400, 450, 750)
                        elif event.key == pygame.K_3:
                            # Strong punch
                            update_display(500, 550, 900)
                elif current_state == "punch_result":
                    # Allow any key to continue from leaderboard screen
                    pygame.mixer.music.stop()  # Stop final score music
                    current_state = "username_input"
                    current_username = ""
                    input_active = True
                    # Force music restart when coming from result screen
                    pygame.mixer.music.stop()
                    display_username_input()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse clicks on buttons
                if event.button == 1:  # Left click
                    click_pos = pygame.mouse.get_pos()
                    handle_button_click(click_pos)
            elif event.type == pygame.MOUSEMOTION:
                # Track mouse position for hover effects
                mouse_pos = pygame.mouse.get_pos()

        # Handle animation state in main thread
        if current_state == "animating" and animation_active:
            display_animation_screen()

        # Return to name entering screen after showing score (for auto-timeout)
        if current_state == "punch_result" and time.time() - update_screen_timer > update_screen_display_time:
            pygame.mixer.music.stop()  # Stop final score music
            current_state = "username_input"
            current_username = ""
            input_active = True
            # Force music restart when auto-returning from result screen
            pygame.mixer.music.stop()
            display_username_input()

    except KeyboardInterrupt:
        print("Exiting...")
        break