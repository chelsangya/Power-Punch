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
from punch_animation import animate_punch_score, create_responsive_layout

# Serial setup with error handling
try:
    ser = serial.Serial('/dev/cu.usbmodem1401', 9600)
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

# Colors - Boxing-themed UI palette
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
# Boxing ring colors
BOXING_RED = (180, 30, 30)        # Deep boxing glove red
CHAMPION_GOLD = (255, 215, 0)     # Championship belt gold
SILVER = (192, 192, 192)          # Silver medal
BRONZE = (205, 127, 50)           # Bronze medal
# Ring canvas and rope colors
CANVAS_CREAM = (245, 240, 220)    # Boxing ring canvas
ROPE_BLUE = (25, 70, 120)         # Traditional ring rope blue
ROPE_RED = (160, 25, 25)          # Traditional ring rope red
# Gym atmosphere colors
GYM_STEEL = (70, 80, 90)          # Steel gym equipment
LEATHER_BROWN = (101, 67, 33)     # Boxing glove leather
SWEAT_GRAY = (85, 85, 85)         # Gym atmosphere
MUSCLE_PURPLE = (150, 75, 175)    # Power/strength theme - brighter purple
# Blood and bruise colors (for impact effects)
BLOOD_RED = (139, 0, 0)           # Dark red for impact
BRUISE_PURPLE = (72, 61, 139)     # Deep bruise color
# Training colors
TRAINING_ORANGE = (255, 140, 0)   # Training equipment orange
SPEED_YELLOW = (255, 215, 50)     # Speed bag yellow

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

def draw_card(surface, x, y, width, height, color=WHITE, border_color=SWEAT_GRAY):
    """Draw a modern card with shadow effect"""
    # Draw shadow
    shadow_rect = pygame.Rect(x + 5, y + 5, width, height)
    pygame.draw.rect(surface, GYM_STEEL, shadow_rect, border_radius=20)
    
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

def draw_modern_button(surface, text, x, y, width, height, color, text_color, hover=False):
    """Draw a modern button with enhanced styling and proper text fitting"""
    button_rect = pygame.Rect(x, y, width, height)
    
    # Hover effect
    if hover:
        color = tuple(min(255, c + 40) for c in color)
        # Add glow effect
        glow_rect = pygame.Rect(x - 3, y - 3, width + 6, height + 6)
        pygame.draw.rect(surface, (color[0]//3, color[1]//3, color[2]//3), glow_rect, border_radius=25)
    
    # Main button
    pygame.draw.rect(surface, color, button_rect, border_radius=20)
    
    # Inner shadow/highlight
    highlight_color = tuple(min(255, c + 60) for c in color)
    pygame.draw.rect(surface, highlight_color, 
                    pygame.Rect(x + 2, y + 2, width - 4, height // 2), border_radius=18)
    
    # Smart text sizing - choose font that fits
    font_to_use = font_small  # Start with smaller font
    text_surface = font_to_use.render(text, True, text_color)
    
    # If text is too wide, try even smaller font
    if text_surface.get_width() > width - 20:
        font_to_use = font_tiny
        text_surface = font_to_use.render(text, True, text_color)
    
    # If still too wide, truncate text
    if text_surface.get_width() > width - 20:
        while len(text) > 1 and text_surface.get_width() > width - 20:
            text = text[:-1]
            text_surface = font_to_use.render(text + "...", True, text_color)
    
    # Text with shadow
    shadow_surface = font_to_use.render(text, True, (30, 30, 30))
    shadow_rect = shadow_surface.get_rect(center=(button_rect.centerx + 2, button_rect.centery + 2))
    surface.blit(shadow_surface, shadow_rect)
    
    # Main text
    text_rect = text_surface.get_rect(center=button_rect.center)
    surface.blit(text_surface, text_rect)
    
    return button_rect

def draw_leaderboard_sidebar(sidebar_width):
    """Draw spectacular professional leaderboard sidebar with modern UI"""
    # Calculate sidebar position (right side)
    sidebar_x = screen_width - sidebar_width
    
    # Create sophisticated background with depth
    # Main gradient background - boxing gym colors
    for x in range(sidebar_width):
        ratio = x / sidebar_width
        # Boxing gym gradient with leather/steel tones
        r = int(20 * (1 - ratio) + 35 * ratio)
        g = int(15 * (1 - ratio) + 25 * ratio)
        b = int(10 * (1 - ratio) + 15 * ratio)
        pygame.draw.line(screen, (r, g, b), (sidebar_x + x, 0), (sidebar_x + x, screen_height))
    
    # Enhanced left border with animated glow
    import time
    glow_intensity = abs(int(time.time() * 2) % 100 - 50) / 50.0
    base_glow = 150 + int(glow_intensity * 105)
    
    # Multi-layer border glow - championship gold
    for i in range(8):
        alpha_factor = max(0, 1 - i / 5.0)
        border_brightness = int(base_glow * alpha_factor)
        border_color = (border_brightness, int(border_brightness * 0.84), 0)
        pygame.draw.line(screen, border_color, (sidebar_x + i, 0), (sidebar_x + i, screen_height), 1)
    
    # Elegant header section with gradient
    header_height = 100
    header_rect = pygame.Rect(sidebar_x, 0, sidebar_width, header_height)
    
    # Header gradient
    for y in range(header_height):
        ratio = y / header_height
        r = int(30 * (1 - ratio) + 15 * ratio)
        g = int(45 * (1 - ratio) + 25 * ratio)  
        b = int(70 * (1 - ratio) + 40 * ratio)
        pygame.draw.line(screen, (r, g, b), (sidebar_x, y), (sidebar_x + sidebar_width, y))
    
    # Header border
    pygame.draw.rect(screen, CHAMPION_GOLD, header_rect, 3)

    
    # Title with layered shadow effect
    for offset in [(3, 3), (2, 2), (1, 1)]:
        shadow_color = (5, 5, 5) if offset == (3, 3) else (10, 10, 10) if offset == (2, 2) else (15, 15, 15)
        title_shadow = font_large.render("LEADERBOARD", True, shadow_color)
        shadow_rect = title_shadow.get_rect(center=(sidebar_x + sidebar_width // 2 + offset[0], 55 + offset[1]))
        screen.blit(title_shadow, shadow_rect)
    
    # Main title
    title_text = font_large.render("HALL OF FAME", True, CHAMPION_GOLD)
    title_rect = title_text.get_rect(center=(sidebar_x + sidebar_width // 2, 55))
    screen.blit(title_text, title_rect)
 
    
    # Get leaderboard data
    leaderboard = get_leaderboard()
    
    if leaderboard:
        # Elegant header section for rankings
        header_y = 110
        header_bg = pygame.Rect(sidebar_x + 8, header_y, sidebar_width - 16, 40)
        
        # Header gradient
        for i in range(40):
            ratio = i / 40
            r = int(25 * (1 - ratio) + 35 * ratio)
            g = int(35 * (1 - ratio) + 50 * ratio)
            b = int(55 * (1 - ratio) + 75 * ratio)
            pygame.draw.line(screen, (r, g, b), 
                           (sidebar_x + 8, header_y + i), 
                           (sidebar_x + sidebar_width - 8, header_y + i))
        
        pygame.draw.rect(screen, (100, 85, 20), header_bg, 2, border_radius=12)
        
        # Header text with better positioning and proper alignment
        rank_text = font_small.render("RANK", True, CHAMPION_GOLD)
        name_text = font_small.render("CHAMPION", True, CHAMPION_GOLD)
        score_text = font_small.render("POWER", True, CHAMPION_GOLD)
        
        screen.blit(rank_text, (sidebar_x + 20, header_y + 12))
        screen.blit(name_text, (sidebar_x + 85, header_y + 12))
        screen.blit(score_text, (sidebar_x + sidebar_width - 100, header_y + 12))

        entry_y = header_y + 55
        entry_height = 38  
        entry_spacing = 10
        
        for i, entry in enumerate(leaderboard[:10]):  # Show top 10
            rank = i + 1
            username = entry["username"]
            score = entry["score"]
            
            # Dynamic background colors with special effects
            if rank == 1:
                # Gold champion special effects
                bg_base = (45, 40, 10)
                border_color = CHAMPION_GOLD
                text_glow = True
                bg_intensity = 0.7 + 0.3 * glow_intensity
            elif rank == 2:
                # Silver runner-up
                bg_base = (40, 40, 40)
                border_color = SILVER
                text_glow = True
                bg_intensity = 0.6 + 0.2 * glow_intensity
            elif rank == 3:
                # Bronze third place
                bg_base = (45, 30, 15)
                border_color = BRONZE
                text_glow = True
                bg_intensity = 0.5 + 0.2 * glow_intensity
            else:
                # Regular entries with alternating colors
                if i % 2 == 0:
                    bg_base = (25, 35, 50)
                    border_color = (60, 80, 110)
                else:
                    bg_base = (20, 30, 45)
                    border_color = (50, 70, 100)
                text_glow = False
                bg_intensity = 1.0
            
            # Apply intensity to background
            bg_color = tuple(int(c * bg_intensity) for c in bg_base)
            
            entry_rect = pygame.Rect(sidebar_x + 8, entry_y, sidebar_width - 16, entry_height)
            
            # Enhanced glow for top 3
            if rank <= 3:
                for glow_layer in range(3):  # Reduced glow layers for cleaner look
                    glow_rect = pygame.Rect(sidebar_x + 8 - glow_layer, entry_y - glow_layer, 
                                          sidebar_width - 16 + 2*glow_layer, entry_height + 2*glow_layer)
                    glow_alpha = max(0, 30 - glow_layer * 10)
                    if rank == 1:
                        glow_tint = (min(255, 80 + glow_alpha), min(255, 70 + glow_alpha), 0)
                    elif rank == 2:
                        glow_tint = (min(255, 50 + glow_alpha), min(255, 50 + glow_alpha), min(255, 50 + glow_alpha))
                    else:
                        glow_tint = (min(255, 60 + glow_alpha), min(255, 40 + glow_alpha), 0)
                    
                    # Simulate glow with multiple rectangles
                    pygame.draw.rect(screen, glow_tint, glow_rect, 1, border_radius=12)
            
            # Main entry background
            pygame.draw.rect(screen, bg_color, entry_rect, border_radius=10)
            pygame.draw.rect(screen, border_color, entry_rect, 2, border_radius=10)
            
            # Rank display with icons and styling
            if rank == 1:
                rank_display = "#1"
                rank_color = CHAMPION_GOLD
            elif rank == 2:
                rank_display = "#2"
                rank_color = SILVER
            elif rank == 3:
                rank_display = "#3"
                rank_color = BRONZE
            else:
                rank_display = f"#{rank}"
                rank_color = (180, 190, 200)
            
            # Text with enhanced shadow for readability - proper alignment
            text_y_offset = (entry_height - font_small.get_height()) // 2  # Center vertically
            
            for shadow_offset in [(1, 1)]:  # Single shadow for cleaner look
                shadow_intensity = 0.4
                shadow_color = tuple(int(c * shadow_intensity) for c in (0, 0, 0))
                
                rank_shadow = font_small.render(rank_display, True, shadow_color)
                name_shadow = font_small.render(username[:8], True, shadow_color)
                score_shadow = font_small.render(str(score), True, shadow_color)
                
                screen.blit(rank_shadow, (sidebar_x + 15 + shadow_offset[0], entry_y + text_y_offset + shadow_offset[1]))
                screen.blit(name_shadow, (sidebar_x + 85 + shadow_offset[0], entry_y + text_y_offset + shadow_offset[1]))
                screen.blit(score_shadow, (sidebar_x + sidebar_width - 80 + shadow_offset[0], entry_y + text_y_offset + shadow_offset[1]))
            
            # Main text with enhanced colors and proper alignment
            text_color = WHITE if rank > 3 else (255, 255, 220)
            
            rank_surface = font_small.render(rank_display, True, rank_color)
            name_surface = font_small.render(username[:8], True, text_color)
            score_surface = font_small.render(str(score), True, rank_color)
            
            # Properly aligned text positioning
            screen.blit(rank_surface, (sidebar_x + 15, entry_y + text_y_offset))
            screen.blit(name_surface, (sidebar_x + 85, entry_y + text_y_offset))
            screen.blit(score_surface, (sidebar_x + sidebar_width - 80, entry_y + text_y_offset))
            
            entry_y += entry_height + entry_spacing
    
    else:
        # No leaderboard data
        no_data_y = 200  # Fixed Y position for no data message
        no_data_text = font_large.render("NO CHAMPIONS YET", True, CHAMPION_GOLD)
        no_data_rect = no_data_text.get_rect(center=(sidebar_x + sidebar_width // 2, no_data_y))
        screen.blit(no_data_text, no_data_rect)


def display_username_input():
    """Display username input with permanent leaderboard sidebar on right"""
    global current_username, input_active, button_rects
    
    # Clear button rects
    button_rects.clear()
    
    # Draw boxing gym atmosphere background
    screen.fill((25, 20, 15))
    
    # Calculate layout dimensions (leaderboard on right)
    sidebar_width = int(screen_width * 0.35)
    main_width = screen_width - sidebar_width
    
    # Draw permanent leaderboard sidebar on right
    draw_leaderboard_sidebar(sidebar_width)
    
    # Main content area (left side)
    main_x = 0
    
    # Title section with better spacing
    title_y = 60
    title_text = font_title.render("POWER PUNCH", True, CHAMPION_GOLD)
    subtitle_text = font_large.render("Boxing Championship", True, WHITE)
    
    title_rect = title_text.get_rect(center=(main_width // 2, title_y))
    subtitle_rect = subtitle_text.get_rect(center=(main_width // 2, title_y + 60))
    
    screen.blit(title_text, title_rect)
    screen.blit(subtitle_text, subtitle_rect)
    
    # Username input section
    input_y = 200
    
    # Username input box
    input_box_width = min(350, main_width - 80)
    input_box_height = 60
    input_box_x = (main_width - input_box_width) // 2
    input_box_y = input_y + 40
    
    input_box_rect = pygame.Rect(input_box_x, input_box_y, input_box_width, input_box_height)
    
    # Modern input box styling
    box_color = (40, 50, 60) if input_active else (30, 40, 50)
    border_color = CHAMPION_GOLD if input_active else (70, 80, 90)
    pygame.draw.rect(screen, box_color, input_box_rect, border_radius=15)
    pygame.draw.rect(screen, border_color, input_box_rect, 4, border_radius=15)
    
    # Username text with proper sizing
    username_text = font_small.render(current_username, True, WHITE)
    text_x = input_box_rect.x + 15
    text_y = input_box_rect.y + (input_box_rect.height - username_text.get_height()) // 2
    screen.blit(username_text, (text_x, text_y))
    
    # Animated cursor
    if input_active and int(time.time() * 2) % 2:
        cursor_x = text_x + username_text.get_width() + 5
        cursor_y = input_box_rect.y + 15
        pygame.draw.line(screen, CHAMPION_GOLD, (cursor_x, cursor_y), (cursor_x, cursor_y + 30), 2)
    
    # Start button (only if username is entered)
    if current_username.strip():
        button_width = 200
        button_height = 50
        start_button_x = (main_width - button_width) // 2
        start_button_y = input_y + 120
        
        hover = 'start' in button_rects and button_rects['start'].collidepoint(mouse_pos) if button_rects else False
        button_rects['start'] = draw_modern_button(screen, "START GAME", start_button_x, start_button_y, 
                                                 button_width, button_height, ROPE_BLUE, WHITE, hover)
    
    pygame.display.flip()

def display_initial_screen():
    """Display main game screen with permanent leaderboard sidebar"""
    global current_state, update_screen_timer, button_rects
    
    # Clear button rects
    button_rects.clear()
    
    # Draw boxing gym atmosphere background
    screen.fill((25, 20, 15))
    
    # Calculate layout dimensions
    sidebar_width = int(screen_width * 0.35)
    main_width = screen_width - sidebar_width
    
    # Draw permanent leaderboard sidebar
    draw_leaderboard_sidebar(sidebar_width)
    
    # Main content area (left side, avoiding leaderboard)
    main_x = 0
    
    # Show enhanced circular score display for user
    if current_username:
        # Draw large enhanced circular score display
        circle_center_x = main_x + main_width // 2
        circle_center_y = screen_height // 2
        circle_radius = 140
        
        # Outer circle (thick championship gold border)
        pygame.draw.circle(screen, CHAMPION_GOLD, (circle_center_x, circle_center_y), circle_radius, 8)
        
        # Inner circle (dark boxing bag background)
        inner_radius = circle_radius - 8
        pygame.draw.circle(screen, (30, 25, 20), (circle_center_x, circle_center_y), inner_radius)
        
        # Very large "0" in the center with shadow
        big_score_font = pygame.font.Font(None, 180)
        
        # Score shadow
        shadow_text = big_score_font.render("0", True, (10, 15, 20))
        shadow_rect = shadow_text.get_rect(center=(circle_center_x + 4, circle_center_y + 4))
        screen.blit(shadow_text, shadow_rect)
        
        # Main score text
        score_text = big_score_font.render("0", True, WHITE)
        score_rect = score_text.get_rect(center=(circle_center_x, circle_center_y))
        screen.blit(score_text, score_rect)
        
        # Enhanced label above the circle
        score_label = font_medium.render("YOUR SCORE", True, CHAMPION_GOLD)
        label_rect = score_label.get_rect(center=(circle_center_x, circle_center_y - circle_radius - 50))
        screen.blit(score_label, label_rect)
        
        # Add decorative elements around the circle
        for angle in range(0, 360, 45):
            dot_x = circle_center_x + int((circle_radius + 25) * math.cos(math.radians(angle)))
            dot_y = circle_center_y + int((circle_radius + 25) * math.sin(math.radians(angle)))
            pygame.draw.circle(screen, CHAMPION_GOLD, (dot_x, dot_y), 4)
    
    # Target zone with enhanced styling
    target_y = screen_height - 200
    target_text = font_medium.render("Target: 650+ for Good, 865+ for Great!", True, MUSCLE_PURPLE)
    target_rect = target_text.get_rect(center=(main_x + main_width // 2, target_y))
    
    # Add background for target text with brighter contrast
    target_bg_rect = pygame.Rect(target_rect.x - 20, target_rect.y - 10, target_rect.width + 40, target_rect.height + 20)
    pygame.draw.rect(screen, (35, 25, 45), target_bg_rect, border_radius=15)  # Darker background for better contrast
    pygame.draw.rect(screen, MUSCLE_PURPLE, target_bg_rect, 3, border_radius=15)  # Thicker border
    
    screen.blit(target_text, target_rect)
    
    # Demo mode instructions (if Arduino not connected)
    if not SERIAL_CONNECTED:
        demo_y = target_y + 60
        demo_text = font_small.render("DEMO MODE: Press SPACE for random punch, or 1/2/3 for specific scores", True, TRAINING_ORANGE)
        demo_rect = demo_text.get_rect(center=(main_x + main_width // 2, demo_y))
        
        # Demo mode background
        demo_bg_rect = pygame.Rect(demo_rect.x - 15, demo_rect.y - 8, demo_rect.width + 30, demo_rect.height + 16)
        pygame.draw.rect(screen, (45, 35, 20), demo_bg_rect, border_radius=10)
        pygame.draw.rect(screen, TRAINING_ORANGE, demo_bg_rect, 2, border_radius=10)
        
        screen.blit(demo_text, demo_rect)
    
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
    
    # Draw boxing gym atmosphere background
    screen.fill((25, 20, 15))
    
    # Draw full-screen leaderboard
    draw_fullscreen_leaderboard(current_username, average_force)

    pygame.display.flip()
    current_state = "punch_result"
    update_screen_timer = time.time()

def draw_fullscreen_leaderboard(username, force):
    """Draw full-screen leaderboard with current user's score and clean table"""
    # Boxing gym background
    screen.fill((25, 20, 15))
    
    # Title section - centered and prominent
    title_y = 60
    title_text = font_title.render("FINAL SCORE", True, CHAMPION_GOLD)
    title_rect = title_text.get_rect(center=(screen_width // 2, title_y))
    screen.blit(title_text, title_rect)
    
    # User's score card - compact version at top
    if username and force > 0:
        card_y = 120
        card_width = 300
        card_height = 80
        card_x = (screen_width - card_width) // 2
        
        # Draw card with boxing theme
        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        
        # Card shadow
        shadow_rect = pygame.Rect(card_x + 5, card_y + 5, card_width, card_height)
        pygame.draw.rect(screen, (15, 10, 5), shadow_rect, border_radius=15)
        
        # Main card background
        pygame.draw.rect(screen, LEATHER_BROWN, card_rect, border_radius=15)
        pygame.draw.rect(screen, CHAMPION_GOLD, card_rect, 4, border_radius=15)
        
        # Score label and value on same line
        label_text = font_small.render("YOUR SCORE:", True, CHAMPION_GOLD)
        score_text = font_large.render(f"{int(force)}", True, WHITE)
        
        # Center both texts together
        total_width = label_text.get_width() + 20 + score_text.get_width()
        start_x = card_x + (card_width - total_width) // 2
        
        screen.blit(label_text, (start_x, card_y + 30))
        screen.blit(score_text, (start_x + label_text.get_width() + 20, card_y + 25))
    
    # BIG LEADERBOARD TABLE - much larger and more prominent
    table_start_y = 220
    leaderboard = get_leaderboard()
    
    if leaderboard:
        # BIG TABLE HEADER - much larger and more prominent
        header_y = table_start_y
        header_width = min(1200, screen_width - 100)  # Much wider table
        header_height = 80  # Taller header
        header_x = (screen_width - header_width) // 2
        
        # Column headers - bigger spacing
        col_header_y = header_y + 20
        rank_col_x = header_x + 100
        name_col_x = header_x + 350
        score_col_x = header_x + 800
        
        # Column header background - bigger
        col_header_rect = pygame.Rect(header_x, col_header_y, header_width, 60)
        pygame.draw.rect(screen, (40, 35, 30), col_header_rect, border_radius=15)
        pygame.draw.rect(screen, ROPE_BLUE, col_header_rect, 4, border_radius=15)
        
        # Column headers text - larger fonts for big table
        rank_header = font_medium.render("RANK", True, CHAMPION_GOLD)
        name_header = font_medium.render("FIGHTER", True, CHAMPION_GOLD)
        score_header = font_medium.render("POWER SCORE", True, CHAMPION_GOLD)
        
        screen.blit(rank_header, (rank_col_x, col_header_y + 20))
        screen.blit(name_header, (name_col_x, col_header_y + 20))
        screen.blit(score_header, (score_col_x, col_header_y + 20))
        
        # Table entries - bigger spacing and fonts
        entry_start_y = col_header_y + 80
        entry_height = 50  # Much taller rows
        
        for i, entry in enumerate(leaderboard[:8]):
            rank = i + 1
            entry_username = entry["username"]
            score = entry["score"]
            
            entry_y = entry_start_y + (i * entry_height)
            
            # Check if current user
            is_current_user = (entry_username == username and abs(score - force) < 10)
            
            # Row background
            row_rect = pygame.Rect(header_x + 10, entry_y, header_width - 20, entry_height - 5)
            
            if rank == 1:
                # Gold background for first place
                pygame.draw.rect(screen, (60, 50, 20), row_rect, border_radius=8)
                pygame.draw.rect(screen, CHAMPION_GOLD, row_rect, 3, border_radius=8)
                text_color = CHAMPION_GOLD
            elif rank == 2:
                # Silver background for second place
                pygame.draw.rect(screen, (45, 45, 45), row_rect, border_radius=8)
                pygame.draw.rect(screen, SILVER, row_rect, 2, border_radius=8)
                text_color = SILVER
            elif rank == 3:
                # Bronze background for third place
                pygame.draw.rect(screen, (55, 35, 20), row_rect, border_radius=8)
                pygame.draw.rect(screen, BRONZE, row_rect, 2, border_radius=8)
                text_color = BRONZE
            elif is_current_user:
                # Highlight current user
                pygame.draw.rect(screen, (70, 50, 30), row_rect, border_radius=8)
                pygame.draw.rect(screen, CHAMPION_GOLD, row_rect, 2, border_radius=8)
                text_color = CHAMPION_GOLD
            else:
                # Regular entries
                bg_color = (35, 30, 25) if i % 2 == 0 else (30, 25, 20)
                pygame.draw.rect(screen, bg_color, row_rect, border_radius=8)
                pygame.draw.rect(screen, GYM_STEEL, row_rect, 1, border_radius=8)
                text_color = WHITE
            
            # Entry text - bigger font for big table
            rank_text = font_small.render(f"#{rank}", True, text_color)
            name_text = font_small.render(entry_username[:15], True, text_color)
            score_text = font_small.render(str(int(score)), True, text_color)
            
            # Position text in columns - adjusted for bigger table
            screen.blit(rank_text, (rank_col_x, entry_y + 18))
            screen.blit(name_text, (name_col_x, entry_y + 18))
            screen.blit(score_text, (score_col_x, entry_y + 18))
    
    else:
        # No data message
        no_data_text = font_large.render("NO CHAMPIONS YET - BE THE FIRST!", True, CHAMPION_GOLD)
        no_data_rect = no_data_text.get_rect(center=(screen_width // 2, table_start_y + 100))
        screen.blit(no_data_text, no_data_rect)
 

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
        
        # Simple built-in animation instead of external module
        animation_duration = 2.0  # 2 seconds
        start_time = time.time()
        current_score = 0
        
        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            
            if elapsed >= animation_duration:
                current_score = animation_target_score
                break
            
            # Calculate current score with easing
            progress = elapsed / animation_duration
            eased_progress = 1 - (1 - progress) ** 2
            current_score = int(animation_target_score * eased_progress)
            
            # Clear screen with boxing gym background
            screen.fill((25, 20, 15))
            
            # Title
            title_text = font_title.render("ANALYZING PUNCH...", True, BOXING_RED)
            title_rect = title_text.get_rect(center=(screen_width // 2, 100))
            screen.blit(title_text, title_rect)
            
            # Animated score - huge and centered
            huge_font = pygame.font.Font(None, 200)
            score_text = huge_font.render(str(current_score), True, WHITE)
            score_rect = score_text.get_rect(center=(screen_width // 2, screen_height // 2))
            screen.blit(score_text, score_rect)
            
            # Progress indicator
            progress_text = font_medium.render(f"Calculating force... {int(progress * 100)}%", True, (150, 160, 170))
            progress_rect = progress_text.get_rect(center=(screen_width // 2, screen_height // 2 + 200))
            screen.blit(progress_text, progress_rect)
            
            # Visual effect - pulsing circle around score
            pulse_radius = 150 + int(20 * abs(1 - 2 * (elapsed % 0.5) / 0.5))
            pygame.draw.circle(screen, (100, 100, 100), (screen_width // 2, screen_height // 2), pulse_radius, 3)
            
            pygame.display.flip()
            pygame.time.wait(50)
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
        
        # Final flash effect
        for flash in range(3):
            screen.fill((25, 20, 15))
            
            # Flash between colors
            flash_color = CHAMPION_GOLD if flash % 2 == 0 else WHITE
            
            # Final title
            final_title = font_title.render("FINAL SCORE!", True, flash_color)
            final_rect = final_title.get_rect(center=(screen_width // 2, 150))
            screen.blit(final_title, final_rect)
            
            # Final score
            huge_font = pygame.font.Font(None, 200)
            final_score = huge_font.render(str(animation_target_score), True, flash_color)
            final_rect = final_score.get_rect(center=(screen_width // 2, screen_height // 2))
            screen.blit(final_score, final_rect)
            
            pygame.display.flip()
            pygame.time.wait(250)
            
            # Handle quit events during flash
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
        
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
                    current_state = "username_input"
                    current_username = ""
                    input_active = True
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
            current_state = "username_input"
            current_username = ""
            input_active = True
            display_username_input()

    except KeyboardInterrupt:
        print("Exiting...")
        break