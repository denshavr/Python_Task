import pygame
import sys
import random
from game_objects import Paddle, Ball, Brick, PowerUp, Laser, Particle, Firework

# CONFIG
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BG_COLOR = pygame.Color('grey12')
BRICK_COLORS = [(178, 34, 34), (255, 165, 0), (255, 215, 0), (50, 205, 50)]

# INITIALIZATION
def init_pygame():
    pygame.init()
    pygame.mixer.init()
    return pygame.time.Clock(), pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

def load_fonts():
    return {
        'title': pygame.font.Font(None, 70),
        'game': pygame.font.Font(None, 40),
        'message': pygame.font.Font(None, 30),
    }

def load_sounds():
    try:
        return {
            'bounce': pygame.mixer.Sound('bounce.wav'),
            'brick_break': pygame.mixer.Sound('brick_break.wav'),
            'game_over': pygame.mixer.Sound('game_over.wav'),
            'laser': pygame.mixer.Sound('laser.wav')
        }
    except pygame.error:
        class DummySound: 
            def play(self): pass
        return {k: DummySound() for k in ['bounce', 'brick_break', 'game_over', 'laser']}

# GAME SETUP
def create_brick_wall(level):
    bricks = []
    rows = 3 + level
    cols = 10
    width = 75
    height = 20
    pad = 5
    offset_y = 50

    for row in range(rows):
        for col in range(cols):
            x = col * (width + pad) + pad
            y = row * (height + pad) + offset_y
            color = BRICK_COLORS[row % len(BRICK_COLORS)]
            bricks.append(Brick(x, y, width, height, color))
    return bricks

def reset_game_state():
    return {
        'paddle': Paddle(SCREEN_WIDTH, SCREEN_HEIGHT),
        'balls': [Ball(SCREEN_WIDTH, SCREEN_HEIGHT)],
        'bricks': create_brick_wall(1),
        'power_ups': [],
        'lasers': [],
        'particles': [],
        'fireworks': [],
        'level': 1,
        'score': 0,
        'lives': 3,
        'message': "",
        'msg_timer': 0,
        'firework_timer': 0,
        'state': 'title_screen',
        'sound_enabled': True
    }

# MAIN LOOP
def main():
    clock, screen = init_pygame()
    pygame.display.set_caption("PyGame Arkanoid")
    fonts = load_fonts()
    sounds = load_sounds()
    state = reset_game_state()

    while True:
        pygame.display.set_caption(f"Sound Enabled: {state['sound_enabled']}")
        handle_events(state, sounds)
        update_and_draw(screen, fonts, sounds, state)
        pygame.display.flip()
        clock.tick(60)

# EVENT HANDLING
def handle_events(state, sounds):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.KEYDOWN:
            handle_keydown(event.key, state, sounds)

def handle_keydown(key, state, sounds):
    if key == pygame.K_m:
        state['sound_enabled'] = not state['sound_enabled']
        return

    if key == pygame.K_SPACE:
        if state['state'] == 'title_screen':
            state['state'] = 'playing'
        elif state['state'] in ['game_over', 'you_win']:
            reset = reset_game_state()
            state.update(reset)
        for ball in state['balls']:
            ball.is_glued = False

        if state['state'] == 'playing' and state['paddle'].has_laser:
            state['lasers'].append(Laser(state['paddle'].rect.centerx, state['paddle'].rect.top))
            if state['sound_enabled']:
                sounds['laser'].play()
            state['paddle'].laser_charges -= 1

    elif key == pygame.K_f and state['paddle'].has_laser:
        for offset in [-30, 30]:
            state['lasers'].append(Laser(state['paddle'].rect.centerx + offset, state['paddle'].rect.top))
        if state['sound_enabled']:
            sounds['laser'].play()

# UPDATE AND DRAW
def update_and_draw(screen, fonts, sounds, state):
    screen.fill(BG_COLOR)
    game_state = state['state']

    if game_state == 'title_screen':
        draw_title_screen(screen, fonts)
    elif game_state == 'playing':
        update_game(screen, fonts, sounds, state)
    else:
        draw_end_screen(screen, fonts, state)

    update_messages_and_particles(screen, fonts, state)

# SCENE DRAWING
def draw_title_screen(screen, fonts):
    title = fonts['title'].render("Welcome to ARKANOID!", True, (255, 255, 255))
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50)))
    
    prompt = fonts['game'].render("Press SPACE to Start", True, (255, 255, 255))
    screen.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20)))

    mute = fonts['message'].render("Press M to mute/unmute sounds", True, (200, 200, 200))
    screen.blit(mute, mute.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60)))

def draw_end_screen(screen, fonts, state):
    if state['state'] == 'you_win':
        state['firework_timer'] -= 1
        if state['firework_timer'] <= 0:
            state['fireworks'].append(Firework(SCREEN_WIDTH, SCREEN_HEIGHT))
            state['firework_timer'] = random.randint(20, 50)
        for fw in state['fireworks'][:]:
            fw.update()
            if fw.is_dead():
                state['fireworks'].remove(fw)
        for fw in state['fireworks']:
            fw.draw(screen)

    msg = "GAME OVER" if state['state'] == 'game_over' else "YOU WIN!"
    screen.blit(fonts['game'].render(msg, True, (255, 255, 255)), 
                (SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 - 20))
    screen.blit(fonts['game'].render("Press SPACE to return to Title", True, (255, 255, 255)), 
                (SCREEN_WIDTH/2 - 150, SCREEN_HEIGHT/2 + 30))

# GAMEPLAY UPDATE
def update_game(screen, fonts, sounds, state):
    paddle = state['paddle']
    paddle.update()
    keys = pygame.key.get_pressed()
    balls = state['balls']

    for ball in balls[:]:
        result, hit = ball.update(paddle, keys[pygame.K_SPACE])
        if result == 'lost':
            balls.remove(ball)
            if not balls:
                state['lives'] -= 1
                if state['lives'] <= 0:
                    state['state'] = 'game_over'
                    if state['sound_enabled']:
                        sounds['game_over'].play()
                else:
                    balls.append(Ball(SCREEN_WIDTH, SCREEN_HEIGHT))
                    paddle.reset()
            continue
        if hit in ['wall', 'paddle'] and state['sound_enabled']:
            sounds['bounce'].play()
            for _ in range(5):
                state['particles'].append(Particle(ball.rect.centerx, ball.rect.centery, (255, 255, 0), 1, 3, 1, 3, 0))

    handle_collisions(state, sounds)
    draw_game_objects(screen, fonts, state)

def handle_collisions(state, sounds):
    # Bricks
    for ball in state['balls']:
        for brick in state['bricks'][:]:
            if ball.rect.colliderect(brick.rect):
                ball.speed_y *= -1
                for _ in range(15):
                    state['particles'].append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 4, 1, 4, 0.05))
                state['bricks'].remove(brick)
                state['score'] += 10
                if state['sound_enabled']:
                    sounds['brick_break'].play()
                if random.random() < 0.3:
                    power = PowerUp(brick.rect.centerx, brick.rect.centery, random.choice(['grow', 'laser', 'glue', 'slow', 'multi']))
                    state['power_ups'].append(power)
                break

    # PowerUps
    for power in state['power_ups'][:]:
        power.update()
        if power.rect.top > SCREEN_HEIGHT:
            state['power_ups'].remove(power)
        elif power.active_timer <= 0 and state['paddle'].rect.colliderect(power.rect):
            state['message'] = power.PROPERTIES[power.type]['message']
            state['msg_timer'] = 120
            if power.type in ['grow', 'laser', 'glue']:
                state['paddle'].activate_power_up(power.type)
            elif power.type == 'slow':
                for b in state['balls']:
                    b.activate_power_up('slow')
            elif power.type == 'multi':
                b = state['balls'][0]
                for _ in range(2):
                    nb = Ball(SCREEN_WIDTH, SCREEN_HEIGHT)
                    nb.rect.center = b.rect.center
                    nb.speed_x = random.choice([-1, 1]) * abs(b.speed_x)
                    nb.speed_y = -abs(b.speed_y)
                    state['balls'].append(nb)
            state['power_ups'].remove(power)

    # Lasers
    for laser in state['lasers'][:]:
        laser.update()
        if laser.rect.bottom < 0:
            state['lasers'].remove(laser)
            continue
        for brick in state['bricks'][:]:
            if laser.rect.colliderect(brick.rect):
                for _ in range(10):
                    state['particles'].append(Particle(brick.rect.centerx, brick.rect.centery, brick.color, 1, 3, 1, 3, 0.05))
                state['bricks'].remove(brick)
                state['lasers'].remove(laser)
                state['score'] += 10
                if state['sound_enabled']:
                    sounds['brick_break'].play()
                break

    # Level progression
    if not state['bricks']:
        if state['level'] < 3:
            state['level'] += 1
            state['bricks'] = create_brick_wall(state['level'])
            state['balls'].clear()
            state['balls'].append(Ball(SCREEN_WIDTH, SCREEN_HEIGHT))
            state['paddle'].reset()
            state['power_ups'].clear()
            state['lasers'].clear()
            state['message'] = f"Level {state['level']}"
            state['msg_timer'] = 120
        else:
            state['state'] = 'you_win'
            state['firework_timer'] = 0

def draw_game_objects(screen, fonts, state):
    state['paddle'].draw(screen)
    for obj_list in ['balls', 'bricks', 'power_ups', 'lasers']:
        for obj in state[obj_list]:
            obj.draw(screen)

    score_text = fonts['game'].render(f"Score: {state['score']}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    lives_text = fonts['game'].render(f"Lives: {state['lives']}", True, (255, 255, 255))
    screen.blit(lives_text, (SCREEN_WIDTH - lives_text.get_width() - 10, 10))

    if state['paddle'].has_laser:
        laser_text = fonts['game'].render(f"Laser: {state['paddle'].laser_charges}", True, (255, 60, 60))
        screen.blit(laser_text, (SCREEN_WIDTH - 220, 10))

    level_text = fonts['game'].render(f"Level: {state['level']}", True, (255, 255, 255))
    screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 10))

# UI EFFECTS
def update_messages_and_particles(screen, fonts, state):
    if state['msg_timer'] > 0:
        state['msg_timer'] -= 1
        msg_surf = fonts['message'].render(state['message'], True, (255, 255, 255))
        screen.blit(msg_surf, msg_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 60)))

    for p in state['particles'][:]:
        p.update()
        if p.size <= 0:
            state['particles'].remove(p)
    for p in state['particles']:
        p.draw(screen)

if __name__ == "__main__":
    main()

