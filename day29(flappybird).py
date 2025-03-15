import pygame
import random
import sys
import os
from enum import Enum

class GameState(Enum):
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

class FlappyBird:
    # Constants
    SCREEN_WIDTH = 1000
    SCREEN_HEIGHT = 700
    FPS = 60
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    
    def __init__(self):
        # Initialize pygame
        pygame.init()
        pygame.mixer.init()
        
        # Set up display
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird")
        self.clock = pygame.time.Clock()
        
        # Load assets
        self.load_assets()
        
        # Game objects
        self.bird = None
        self.pipes = []
        
        # Game variables
        self.score = 0
        self.high_score = self.load_high_score()
        self.game_state = GameState.MENU
        self.last_pipe_time = 0
        self.pipe_frequency = 1500  # milliseconds between pipe spawns
        
        # Start the game
        self.reset_game()
        self.game_loop()
    
    def load_assets(self):
        # Helper function to load and scale images
        def load_image(filename, size=None):
            try:
                # Try to load directly from working directory (no assets folder)
                image = pygame.image.load(filename).convert_alpha()
                return pygame.transform.scale(image, size) if size else image
            except pygame.error:
                # Create placeholder if image isn't found
                print(f"Warning: Could not load image {filename}, using placeholder")
                surface = pygame.Surface(size or (50, 50), pygame.SRCALPHA)
                pygame.draw.rect(surface, (255, 0, 0), surface.get_rect(), 1)
                if size is None and isinstance(surface, pygame.Surface):
                    return pygame.transform.scale(surface, (50, 50))
                return surface
        
        # Load images with error handling
        self.bird_img = load_image("bird.png", (50, 50))
        self.pipe_img = load_image("pipe.png", (100, 500))
        
        try:
            self.background_img = pygame.image.load("background.png").convert()
            self.background_img = pygame.transform.scale(self.background_img, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        except pygame.error:
            print("Warning: Could not load background image, using placeholder")
            self.background_img = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
            self.background_img.fill((135, 206, 235))  # Sky blue color as fallback
        
        # Load fonts
        self.font = pygame.font.Font(None, 36)
        self.large_font = pygame.font.Font(None, 72)
        
        # Load sounds with error handling
        def load_sound(filename):
            try:
                return pygame.mixer.Sound(filename)
            except pygame.error:
                print(f"Warning: Could not load sound {filename}")
                return None  # Return None if sound isn't found
        
        self.flap_sound = load_sound("flap.wav")
        self.hit_sound = load_sound("hit.wav")
        self.point_sound = load_sound("point.wav")
    
    def reset_game(self):
        """Reset the game state for a new game"""
        self.bird = Bird(self.bird_img, self.flap_sound)
        self.pipes = [Pipe(self.pipe_img, self.SCREEN_WIDTH + i * 400) for i in range(2)]
        self.score = 0
        self.game_state = GameState.MENU
        self.last_pipe_time = pygame.time.get_ticks()
    
    def game_loop(self):
        """Main game loop"""
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.game_state == GameState.MENU:
                            self.game_state = GameState.PLAYING
                        elif self.game_state == GameState.PLAYING:
                            self.bird.flap()
                        elif self.game_state == GameState.GAME_OVER:
                            self.reset_game()
                            self.game_state = GameState.PLAYING
            
            # Draw background
            self.screen.blit(self.background_img, (0, 0))
            
            # Update and draw based on game state
            if self.game_state == GameState.MENU:
                self.draw_menu()
                
            elif self.game_state == GameState.PLAYING:
                # Update bird and pipes
                self.bird.update()
                self.update_pipes()
                
                # Draw game objects
                self.bird.draw(self.screen)
                for pipe in self.pipes:
                    pipe.draw(self.screen)
                
                # Draw score
                self.draw_score()
                
                # Check collisions and boundaries
                if self.check_collisions() or self.bird.rect.bottom >= self.SCREEN_HEIGHT:
                    if self.hit_sound:
                        self.hit_sound.play()
                    self.game_over()
                
            elif self.game_state == GameState.GAME_OVER:
                # Draw game objects in final state
                self.bird.draw(self.screen)
                for pipe in self.pipes:
                    pipe.draw(self.screen)
                self.draw_score()
                
                # Draw game over screen
                self.draw_game_over()
            
            # Update display and tick clock
            pygame.display.update()
            self.clock.tick(self.FPS)
        
        # Quit game
        self.save_high_score()
        pygame.quit()
        sys.exit()
    
    def update_pipes(self):
        """Update pipe positions and spawn new pipes"""
        # Check if it's time to spawn a new pipe
        current_time = pygame.time.get_ticks()
        if current_time - self.last_pipe_time > self.pipe_frequency:
            self.pipes.append(Pipe(self.pipe_img, self.SCREEN_WIDTH))
            self.last_pipe_time = current_time
        
        # Update existing pipes
        pipes_to_remove = []
        for pipe in self.pipes:
            pipe.update()
            
            # Check if pipe is passed and score should increase
            if not pipe.scored and pipe.x + pipe.width < self.bird.rect.left:
                self.score += 1
                pipe.scored = True
                if self.point_sound:
                    self.point_sound.play()
                
                # Speed up difficulty as score increases
                if self.score % 5 == 0 and self.pipe_frequency > 800:
                    self.pipe_frequency -= 100
            
            # Remove pipes that have moved off-screen
            if pipe.x + pipe.width < 0:
                pipes_to_remove.append(pipe)
        
        # Remove off-screen pipes
        for pipe in pipes_to_remove:
            self.pipes.remove(pipe)
    
    def check_collisions(self):
        """Check if bird collides with any pipe"""
        for pipe in self.pipes:
            if pipe.collide(self.bird):
                return True
        return False
    
    def game_over(self):
        """Handle game over state"""
        self.game_state = GameState.GAME_OVER
        
        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score
    
    def draw_menu(self):
        """Draw the start menu"""
        title = self.large_font.render("FLAPPY BIRD", True, self.WHITE)
        instruction = self.font.render("Press SPACE to Start", True, self.WHITE)
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, self.WHITE)
        
        # Draw the bird in the center for menu screen
        self.bird.rect.center = (self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 50)
        self.bird.draw(self.screen)
        
        # Position and draw text
        title_rect = title.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 4))
        instruction_rect = instruction.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 50))
        high_score_rect = high_score_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 100))
        
        self.screen.blit(title, title_rect)
        self.screen.blit(instruction, instruction_rect)
        self.screen.blit(high_score_text, high_score_rect)
    
    def draw_game_over(self):
        """Draw the game over screen"""
        game_over_text = self.large_font.render("GAME OVER", True, self.WHITE)
        score_text = self.font.render(f"Score: {self.score}", True, self.WHITE)
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, self.WHITE)
        restart_text = self.font.render("Press SPACE to Restart", True, self.WHITE)
        
        # Position and draw text with semi-transparent background
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        
        game_over_rect = game_over_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 3))
        score_rect = score_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
        high_score_rect = high_score_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 50))
        restart_rect = restart_text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 100))
        
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(high_score_text, high_score_rect)
        self.screen.blit(restart_text, restart_rect)
    
    def draw_score(self):
        """Draw current score during gameplay"""
        score_text = self.font.render(f"Score: {self.score}", True, self.WHITE)
        self.screen.blit(score_text, (10, 10))
    
    def load_high_score(self):
        """Load high score from file"""
        try:
            with open("high_score.txt", "r") as file:
                return int(file.read())
        except (FileNotFoundError, ValueError):
            return 0
    
    def save_high_score(self):
        """Save high score to file"""
        try:
            with open("high_score.txt", "w") as file:
                file.write(str(self.high_score))
        except IOError:
            pass  # Silently fail if we can't write the file


class Bird:
    def __init__(self, image, sound=None):
        self.image = image
        self.original_image = image  # Store original for rotation
        self.rect = self.image.get_rect(center=(100, FlappyBird.SCREEN_HEIGHT // 2))
        self.velocity = 0
        self.gravity = 0.5
        self.max_velocity = 10
        self.flap_sound = sound
        self.angle = 0
    
    def flap(self):
        self.velocity = -8
        if self.flap_sound:
            self.flap_sound.play()
    
    def update(self):
        # Update velocity and position
        self.velocity = min(self.velocity + self.gravity, self.max_velocity)
        self.rect.y += self.velocity
        
        # Rotate bird based on velocity
        self.angle = -self.velocity * 3  # Simple rotation based on velocity
        self.angle = max(-30, min(self.angle, 45))  # Clamp rotation
        
        # Create rotated image
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        
        # Keep center position
        center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = center
        
        # Prevent bird from going off-screen
        if self.rect.top <= 0:
            self.rect.top = 0
            self.velocity = 0
    
    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Pipe:
    def __init__(self, image, x):
        self.image = image
        self.x = x
        self.width = 80
        self.height = 500
        self.gap = 200  # Gap between top and bottom pipes
        self.speed = 5
        self.scored = False  # Flag to track if this pipe has been scored
        
        # Random gap position
        self.top = random.randint(100, FlappyBird.SCREEN_HEIGHT - self.gap - 100)
        self.bottom = self.top + self.gap
    
    def update(self):
        self.x -= self.speed
    
    def draw(self, screen):
        # Draw top pipe (flipped)
        top_pipe = pygame.transform.flip(self.image, False, True)
        screen.blit(top_pipe, (self.x, self.top - self.height))
        
        # Draw bottom pipe
        screen.blit(self.image, (self.x, self.bottom))
    
    def collide(self, bird):
        # Define collision rectangles for top and bottom pipes
        top_pipe_rect = pygame.Rect(self.x, 0, self.width, self.top)
        bottom_pipe_rect = pygame.Rect(self.x, self.bottom, self.width, FlappyBird.SCREEN_HEIGHT - self.bottom)
        
        # Check for collision with bird
        return bird.rect.colliderect(top_pipe_rect) or bird.rect.colliderect(bottom_pipe_rect)


# Run the game if this script is executed directly
if __name__ == "__main__":
    # Start the game
    game = FlappyBird()