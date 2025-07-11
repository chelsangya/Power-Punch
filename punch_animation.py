import pygame
import time
import sys

def animate_punch_score(screen, target_score, screen_width, screen_height, fonts):
    """
    Animate the punch score like a real punching bag
    Returns when animation is complete
    """
    # Animation parameters
    animation_duration = 2.5  # 2.5 seconds
    start_time = time.time()
    current_score = 0
    
    # Colors - Boxing-themed to match main UI
    WHITE = (255, 255, 255)
    BOXING_RED = (180, 30, 30)        # Deep boxing glove red
    CHAMPION_GOLD = (255, 215, 0)     # Championship belt gold
    DARK_BG = (25, 20, 15)           # Boxing gym atmosphere
    
    # Get fonts
    font_title = fonts.get('title', pygame.font.Font(None, 80))
    font_huge = pygame.font.Font(None, 200)
    font_medium = fonts.get('medium', pygame.font.Font(None, 40))
    
    while True:
        current_time = time.time()
        elapsed = current_time - start_time
        
        if elapsed >= animation_duration:
            current_score = target_score
            break
        
        # Calculate current score with realistic easing
        progress = elapsed / animation_duration
        # Use exponential ease-out for natural punch bag feel
        eased_progress = 1 - (1 - progress) ** 2
        current_score = int(target_score * eased_progress)
        
        # Add some randomness in the middle for realism
        if 0.2 < progress < 0.8:
            wobble = int(target_score * 0.1 * (0.5 - abs(progress - 0.5)) * 4)
            current_score += wobble
            current_score = max(0, min(target_score, current_score))
        
        # Clear screen
        screen.fill(DARK_BG)
        
        # Title
        #   title_text = font_title.render("ANALYZING PUNCH...", True, RED) should be slightly up
        title_text = font_title.render("ANALYZING PUNCH...", True, BOXING_RED)
        # Center title at the top

        title_rect = title_text.get_rect(center=(screen_width // 2, 100))
        screen.blit(title_text, title_rect)
        
        # Animated score - huge and centered
        score_text = font_huge.render(str(current_score), True, WHITE)
        score_rect = score_text.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(score_text, score_rect)
        
        # Progress indicator
        progress_text = font_medium.render(f"Calculating force... {int(progress * 100)}%", True, (150, 160, 170))
        progress_rect = progress_text.get_rect(center=(screen_width // 2, screen_height // 2 + 120))
        screen.blit(progress_text, progress_rect)
        
        # Visual effect - pulsing circle around score
        pulse_radius = 150 + int(20 * abs(1 - 2 * (elapsed % 0.5) / 0.5))
        pygame.draw.circle(screen, (100, 100, 100), (screen_width // 2, screen_height // 2), pulse_radius, 3)
        
        pygame.display.flip()
        pygame.time.wait(50) 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
    
    # Final flash effect
    for flash in range(3):
        screen.fill(DARK_BG)
        
        # Flash between colors
        flash_color = CHAMPION_GOLD if flash % 2 == 0 else WHITE
        
        # Final title
        final_title = font_title.render("FINAL SCORE!", True, flash_color)
        final_rect = final_title.get_rect(center=(screen_width // 2, 150))
        screen.blit(final_title, final_rect)
        
        # Final score
        final_score = font_huge.render(str(target_score), True, flash_color)
        final_rect = final_score.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(final_score, final_rect)
        
        pygame.display.flip()
        pygame.time.wait(250)  # Flash duration
        
        # Handle quit events during flash
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

def create_responsive_layout(screen_width, screen_height):
    """
    Create a responsive layout that adapts to different screen sizes
    """
    # Base dimensions for a 1920x1080 screen
    base_width = 1920
    base_height = 1080
    
    # Calculate scaling factors
    width_scale = screen_width / base_width
    height_scale = screen_height / base_height
    scale = min(width_scale, height_scale)  # Use smaller scale to maintain aspect ratio
    
    # Responsive sidebar width (20-30% of screen width)
    sidebar_width = max(250, min(400, int(screen_width * 0.25)))
    main_width = screen_width - sidebar_width
    
    # Responsive font sizes
    font_sizes = {
        'title': max(40, int(80 * scale)),
        'large': max(30, int(60 * scale)),
        'medium': max(20, int(40 * scale)),
        'small': max(16, int(28 * scale)),
        'tiny': max(12, int(20 * scale))
    }
    
    # Create font objects
    fonts = {}
    for name, size in font_sizes.items():
        fonts[name] = pygame.font.Font(None, size)
    
    return {
        'sidebar_width': sidebar_width,
        'main_width': main_width,
        'fonts': fonts,
        'scale': scale
    }

if __name__ == "__main__":
    # Test the animation
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Punch Animation Test")
    
    layout = create_responsive_layout(800, 600)
    
    # Test animation with score 750
    animate_punch_score(screen, 750, 800, 600, layout['fonts'])
    
    # Wait a bit then quit
    pygame.time.wait(2000)
    pygame.quit()
