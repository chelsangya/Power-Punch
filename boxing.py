import serial
import pygame
import sys
import json
import os
import time
import threading
import random


ser = serial.Serial('/dev/cu.usbmodem1301', 9600)

pygame.init()
pygame.mixer.init()


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

insults_music = [
    "barbie.mp3",
    
]

praises_music = [
    "cena.mp3",
    
]

# Display setup
info = pygame.display.Info()
screen_width, screen_height = info.current_w, info.current_h
screen = pygame.display.set_mode(
    (screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption('Sensor Display')

# Colors
WHITE = (255, 255, 255)
BLACK = (255, 255, 255)
GREEN = (54, 161, 93)
minimum_threshold = 305

# Add a new variable for state management and a timer for returning to the initial screen
current_state = "initial"
update_screen_display_time = 8  # seconds
update_screen_timer = 0

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

# Read high scores


def read_high_scores():
    if os.path.exists(high_score_file):
        with open(high_score_file, 'r') as file:
            return json.load(file)
    return {"high_score": 0}

# Write high scores


def write_high_score(score):
    with open(high_score_file, 'w') as file:
        json.dump({"high_score": score}, file)

# Play song if not already playing


def play_song(song):
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load(song)
        pygame.mixer.music.play()


# Initialize high score
high_scores = read_high_scores()
highest_score = high_scores["high_score"]
# Update the display_initial_screen function to reset the timer


def display_initial_screen():
    global current_state, update_screen_timer
    screen.blit(pygame.transform.scale(background_img,
                (screen_width, screen_height)), (0, 0))

    title_text = font_large.render("POWER PUNCH", True, BLACK)
    sub_text = font_medium.render(
        "Let's see what you got? Hit the pad, watch your score soar!", True, BLACK)
    sub_text_two = font_medium.render(
        "Show off your power and dominate the leaderboard!", True, BLACK)
    high_score_text = font_large.render(
        f"High Score: {highest_score}", True, GREEN)

    title_rect = title_text.get_rect(
        center=(screen_width / 2, screen_height * 0.3))
    sub_text_rect = sub_text.get_rect(
        center=(screen_width / 2, screen_height * 0.45))
    sub_text_two_rect = sub_text_two.get_rect(
        center=(screen_width / 2, screen_height * 0.5))
    high_score_rect = high_score_text.get_rect(
        center=(screen_width / 2, screen_height * 0.93))

    screen.blit(title_text, title_rect)
    screen.blit(sub_text, sub_text_rect)
    screen.blit(sub_text_two, sub_text_two_rect)
    screen.blit(high_score_text, high_score_rect)
    pygame.display.flip()

    # Reset state and timer
    current_state = "initial"
    update_screen_timer = 0


display_initial_screen()
# funciton to display the pages after each punch


def update_display(fsr1, fsr2, average_force):
    global highest_score, last_update_time, current_state, update_screen_timer
    current_time = time.time()

    if current_time - last_update_time < UPDATE_DELAY:
        return  # Skip update if too soon

    last_update_time = current_time
    screen.blit(pygame.transform.scale(background_img,
                (screen_width, screen_height)), (0, 0))

    avg_force_text = font_large.render(
        f"Your Score is: {average_force}", True, GREEN)
    pygame.draw.rect(screen, WHITE, pygame.Rect(screen_width * 0.2, screen_height *
                     0.4, screen_width * 0.6, screen_height * 0.1), border_radius=10)
    screen.blit(avg_force_text, (screen_width * 0.25, screen_height * 0.42))

    if average_force >=650 and average_force <= 865:
        # Display the "barbie" image
        screen.blit(pygame.transform.scale(barbie_img, (screen_width // 4, screen_height // 4)), (screen_width * 0.75, screen_height * 0.5))
        play_song('barbie.mp3')
        # Select and display a random insult
        insult = random.choice(insults)
        insult_text = font_medium.render(insult, True, BLACK)
        insult_rect = insult_text.get_rect(
            center=(screen_width * 0.5, screen_height * 0.15))
        screen.blit(insult_text, insult_rect)
    elif average_force > 865:
        # Display the "cena" image
        screen.blit(pygame.transform.scale(cena_img, (screen_width // 4,
                    screen_height // 4)), (screen_width * 0.75, screen_height * 0.5))
        play_song('cena.mp3')

        # Select and display a random praise
        praise = random.choice(praises)
        praise_text = font_small.render(praise, True, BLACK)
        praise_rect = praise_text.get_rect(
            center=(screen_width * 0.5, screen_height * 0.7))
        screen.blit(praise_text, praise_rect)
    else:
        # Display the "barbie" image
        screen.blit(pygame.transform.scale(barbie_img, (screen_width // 2,
                    screen_height // 2)), (screen_width * 0.75, screen_height * 0.5))
        play_song('barbie.mp3')

        # Select and display a random insult
        insult = random.choice(insults)
        insult_text = font_medium.render(insult, True, BLACK)
        insult_rect = insult_text.get_rect(
            center=(screen_width * 0.5, screen_height * 0.15))
        screen.blit(insult_text, insult_rect)

        if average_force > highest_score:
            highest_score = average_force
            write_high_score(highest_score)

            # Display congratulatory message for beating the high score
            congrats_text = font_medium.render(
                "New High Score! Congratulations!", True, GREEN)
            congrats_rect = congrats_text.get_rect(
                center=(screen_width * 0.5, screen_height * 0.8))
            screen.blit(congrats_text, congrats_rect)

            # Update high score averageaver
            high_score_text = font_medium.render(
                f"High Score: {highest_score}", True, GREEN)
            screen.blit(high_score_text, (screen_width * 0.5 -
                        high_score_text.get_width() / 2, screen_height * 0.85))

    pygame.display.flip()

# Set the state to "update" and start the timer
    current_state = "update"
    update_screen_timer = time.time()


# Main loop for reading serial data
def read_serial_data():
    while True:
        global minimum_threshold
        try:
            line = ser.readline().decode('utf-8').strip()
            # print(line)
            if line:
                parts = line.split(",")
                if len(parts) == 3:
                    fsr1_str = parts[0].split(": ")[1]
                    fsr2_str = parts[1].split(": ")[1]
                    fsr1 = int(fsr1_str)
                    fsr2 = int(fsr2_str)
                    if fsr1 > minimum_threshold and fsr2 > minimum_threshold:
                        average_force = (fsr1 + fsr2)/2
                    elif fsr1 < minimum_threshold:
                        average_force = fsr2
                    elif fsr2 < minimum_threshold:
                        average_force = fsr1
                    print("average force", average_force)
                    if average_force >= 650:
                        update_display(fsr1, fsr2, average_force)
        except ValueError:
            continue


serial_thread = threading.Thread(target=read_serial_data)
serial_thread.daemon = True
serial_thread.start()

# main starting pint here
while True:
    try:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                screen = pygame.display.set_mode(
                    (screen_width, screen_height), pygame.RESIZABLE)
                display_initial_screen()

        if current_state == "update" and time.time() - update_screen_timer > update_screen_display_time:
            display_initial_screen()  # Go back to the initial screen

    except KeyboardInterrupt:
        print("Exiting...")
        break
