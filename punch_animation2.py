import pygame
import time
import sys
import os

def animate_punch_score(screen, target_score, screen_width, screen_height, fonts):
    """
    Elegant and smooth punch score animation with modern UI design
    Returns when animation is complete
    """
    import math
    
    # Initialize pygame mixer if not already initialized
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    
    # Load and play calculate score sound
    calculate_score_sound = None
    try:
        calculate_score_path = os.path.join(os.path.dirname(__file__), "calculate2.mp3")
        calculate_score_sound = pygame.mixer.Sound(calculate_score_path)
        calculate_score_sound.play()
    except pygame.error as e:
        print(f"Could not load calculate2.mp3: {e}")
    except FileNotFoundError:
        print("calculate2.mp3 not found in the current directory")
    
    # Animation parameters
    animation_duration = 2.2  # Shorter, more focused
    start_time = time.time()
    current_score = 0
    
    # Clean, modern color palette
    WHITE = (255, 255, 255)
    LIGHT_GRAY = (200, 200, 200)
    DARK_GRAY = (80, 80, 80)
    ACCENT_BLUE = (74, 144, 226)      # Modern blue
    SUCCESS_GREEN = (46, 204, 113)    # Success green
    SOFT_RED = (231, 76, 60)          # Soft red
    BACKGROUND = (32, 32, 40)         # Clean dark background
    
    # Get fonts
    font_title = fonts.get('title', pygame.font.Font(None, 60))
    font_huge = pygame.font.Font(None, 180)
    font_medium = fonts.get('medium', pygame.font.Font(None, 36))
    
    while True:
        current_time = time.time()
        elapsed = current_time - start_time
        
        if elapsed >= animation_duration:
            current_score = target_score
            break
        
        progress = elapsed / animation_duration
        
        # Smooth easing function for natural feel
        ease_progress = 1 - math.pow(1 - progress, 3)  # Ease-out cubic
        current_score = int(target_score * ease_progress)
        
        # Clear screen with gradient background
        screen.fill(BACKGROUND)
        
        # Subtle animated background effect
        for i in range(5):
            alpha = int(20 - i * 3)
            circle_radius = 100 + i * 40 + int(30 * math.sin(elapsed * 2 + i * 0.5))
            circle_color = (*ACCENT_BLUE, alpha) if alpha > 0 else ACCENT_BLUE
            # Create a surface for transparency
            circle_surf = pygame.Surface((circle_radius * 2, circle_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (*ACCENT_BLUE, alpha), (circle_radius, circle_radius), circle_radius, 2)
            screen.blit(circle_surf, (screen_width // 2 - circle_radius, screen_height // 2 - circle_radius))
        
        # Clean title
        title_color = ACCENT_BLUE if progress < 0.8 else SUCCESS_GREEN
        title_text = "Calculating Impact"
        if progress > 0.6:
            title_text = "Score Computed"
        
        title_surface = font_title.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(screen_width // 2, 120))
        screen.blit(title_surface, title_rect)
        
        # Main score with smooth scaling
        scale_factor = 0.8 + 0.2 * ease_progress
        score_text = str(current_score)
        
        # Determine score color based on value
        if target_score < 300:
            score_color = LIGHT_GRAY
        elif target_score < 600:
            score_color = ACCENT_BLUE
        elif target_score < 800:
            score_color = SUCCESS_GREEN
        else:
            score_color = SOFT_RED
        
        score_surface = font_huge.render(score_text, True, score_color)
        
        # Scale the score text
        if scale_factor != 1.0:
            scaled_width = int(score_surface.get_width() * scale_factor)
            scaled_height = int(score_surface.get_height() * scale_factor)
            score_surface = pygame.transform.scale(score_surface, (scaled_width, scaled_height))
        
        score_rect = score_surface.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(score_surface, score_rect)
        
        # Progress bar
        bar_width = 300
        bar_height = 6
        bar_x = (screen_width - bar_width) // 2
        bar_y = screen_height // 2 + 120
        
        # Background bar
        pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
        
        # Progress fill
        fill_width = int(bar_width * progress)
        progress_color = ACCENT_BLUE if progress < 0.8 else SUCCESS_GREEN
        pygame.draw.rect(screen, progress_color, (bar_x, bar_y, fill_width, bar_height))
        
        # Percentage text
        percentage_text = f"{int(progress * 100)}%"
        percentage_surface = font_medium.render(percentage_text, True, LIGHT_GRAY)
        percentage_rect = percentage_surface.get_rect(center=(screen_width // 2, bar_y + 30))
        screen.blit(percentage_surface, percentage_rect)
        
        # Score category
        if progress > 0.3:
            category = "WEAK"
            if target_score > 300: category = "GOOD"
            if target_score > 500: category = "STRONG"
            if target_score > 700: category = "POWERFUL"
            if target_score > 900: category = "DEVASTATING"
            
            category_surface = font_medium.render(category, True, score_color)
            category_rect = category_surface.get_rect(center=(screen_width // 2, screen_height // 2 + 180))
            screen.blit(category_surface, category_rect)
        
        pygame.display.flip()
        pygame.time.wait(16)  # 60 FPS for smooth animation

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
    
    # Stop the calculate score sound when animation main loop ends
    if calculate_score_sound:
        calculate_score_sound.stop()
    
    # Clean final reveal animation
    for reveal in range(4):
        screen.fill(BACKGROUND)
        
        # Gentle pulsing effect
        pulse_scale = 1.0 + 0.1 * math.sin(reveal * 2)
        
        # Final score color based on performance
        if target_score < 300:
            final_color = LIGHT_GRAY
        elif target_score < 600:
            final_color = ACCENT_BLUE
        elif target_score < 800:
            final_color = SUCCESS_GREEN
        else:
            final_color = SOFT_RED
        
        # "Final Score" title
        final_title = font_title.render("Final Score", True, final_color)
        title_rect = final_title.get_rect(center=(screen_width // 2, 140))
        screen.blit(final_title, title_rect)
        
        # Final score with gentle pulse
        score_surface = font_huge.render(str(target_score), True, final_color)
        if pulse_scale != 1.0:
            scaled_width = int(score_surface.get_width() * pulse_scale)
            scaled_height = int(score_surface.get_height() * pulse_scale)
            score_surface = pygame.transform.scale(score_surface, (scaled_width, scaled_height))
        
        score_rect = score_surface.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(score_surface, score_rect)
        
        # Performance rating
        rating = "WEAK"
        if target_score > 300: rating = "GOOD"
        if target_score > 500: rating = "STRONG"
        if target_score > 700: rating = "POWERFUL"
        if target_score > 900: rating = "DEVASTATING"
        
        rating_surface = font_medium.render(rating, True, final_color)
        rating_rect = rating_surface.get_rect(center=(screen_width // 2, screen_height // 2 + 140))
        screen.blit(rating_surface, rating_rect)
        
        # Subtle decorative line
        line_width = 200
        line_y = screen_height // 2 + 100
        pygame.draw.line(screen, final_color, 
                        (screen_width // 2 - line_width // 2, line_y),
                        (screen_width // 2 + line_width // 2, line_y), 2)
        
        pygame.display.flip()
        pygame.time.wait(300)
        
        # Handle quit events during reveal
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
    pygame.mixer.init()  # Initialize mixer for sound
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Punch Animation Test")
    
    layout = create_responsive_layout(800, 600)
    
    # Test animation with score 750
    animate_punch_score(screen, 750, 800, 600, layout['fonts'])
    
    # Wait a bit then quit
    pygame.time.wait(2000)
    pygame.quit()
