import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH = 1200
HEIGHT = 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Management Visualizer")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
PINK = (255, 100, 150)
GREEN = (50, 200, 50)
YELLOW = (255, 255, 100)
GRAY = (240, 240, 240)
BUTTON_GREEN = (0, 204, 102)
BUTTON_RED = (255, 0, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# Memory settings
MEMORY_SIZE = 16384  # 16KB
PAGE_SIZE = 1024  # 1KB pages
MAX_SEGMENTS = 4

# Process class
class Process:
    def __init__(self, id, size):
        self.id = id
        self.size = size

# UI elements
font = pygame.font.Font(None, 24)
processes = []
running = True
paused = False
process_id = 1
cpu_usage = 0
fragmentation = 0
memory_history = []

# Button class with hover effect
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = font.render(text, True, BLACK)
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.is_hovered = False

    def draw(self):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        screen.blit(self.text, (self.rect.x + (self.rect.width - self.text.get_width()) // 2,
                            self.rect.y + (self.rect.height - self.text.get_height()) // 2))

    def clicked(self, pos):
        if self.rect.collidepoint(pos):
            self.action()
            return True
        return False

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

# Buttons
buttons = [
    Button(1020, 50, 150, 40, "Add Process", BUTTON_GREEN, (0, 255, 102), lambda: add_process()),
    Button(1020, 100, 150, 40, "Remove Process", BUTTON_RED, (255, 51, 51), lambda: remove_process()),
    Button(1020, 150, 150, 40, "Pause/Resume", GRAY, (169, 169, 169), lambda: toggle_pause())
]

def add_process():
    global process_id
    if len(processes) < 8:
        processes.append(Process(process_id, random.randint(512, 2048)))
        process_id += 1

def remove_process():
    if processes:
        processes.pop()

def toggle_pause():
    global paused
    paused = not paused

def draw_paging(x, y, width, height):
    pygame.draw.rect(screen, WHITE, (x, y, width, height))
    pages = MEMORY_SIZE // PAGE_SIZE
    page_height = height / pages
    
    for i in range(pages):
        pygame.draw.line(screen, BLACK, (x, y + i * page_height), 
                         (x + width, y + i * page_height))
        text = font.render(f"Pg {i}", True, BLACK)
        screen.blit(text, (x + 5, y + i * page_height + 5))
    
    for idx, proc in enumerate(processes):
        pages_needed = (proc.size + PAGE_SIZE - 1) // PAGE_SIZE
        start_page = idx * 2
        if start_page + pages_needed <= pages:
            pygame.draw.rect(screen, BLUE, 
                             (x + 40, y + start_page * page_height, 
                              width - 40, pages_needed * page_height))
            text = font.render(f"P{proc.id} ({proc.size}B)", True, BLACK)
            screen.blit(text, (x + 50, y + start_page * page_height + 5))

def draw_segmentation(x, y, width, height):
    pygame.draw.rect(screen, WHITE, (x, y, width, height))
    current_y = y
    
    for proc in processes:
        segments = split_into_segments(proc)
        for i, (seg_size, seg_height) in enumerate(segments):
            if current_y + seg_height <= y + height:
                pygame.draw.rect(screen, PINK,
                                 (x + 40, current_y, width - 40, seg_height))
                text = font.render(f"P{proc.id} S{i} ({seg_size}B)", True, BLACK)
                screen.blit(text, (x + 50, current_y + 5))
                current_y += seg_height

def draw_first_fit(x, y, width, height):
    pygame.draw.rect(screen, WHITE, (x, y, width, height))
    memory = [(0, MEMORY_SIZE)]
    allocated = []
    
    for proc in processes:
        for i, (start, size) in enumerate(memory):
            if size >= proc.size:
                allocated.append((start, proc.size, proc.id))
                memory[i] = (start + proc.size, size - proc.size)
                if memory[i][1] == 0:
                    memory.pop(i)
                break
    
    for start, size, proc_id in allocated:
        block_height = (size / MEMORY_SIZE) * height
        pygame.draw.rect(screen, GREEN, 
                         (x + 40, y + start * height / MEMORY_SIZE, 
                          width - 40, block_height))
        text = font.render(f"P{proc_id} ({size}B)", True, BLACK)
        screen.blit(text, (x + 50, y + start * height / MEMORY_SIZE + 5))

def split_into_segments(process):
    segments = []
    remaining_size = process.size
    segment_count = min(random.randint(1, MAX_SEGMENTS), (process.size + 255) // 256)
    
    for i in range(segment_count):
        if i == segment_count - 1:
            seg_size = remaining_size
        else:
            max_size = max(256, remaining_size // (segment_count - i))
            seg_size = random.randint(256, max_size)
        remaining_size -= seg_size
        seg_height = (seg_size / MEMORY_SIZE) * 600
        segments.append((seg_size, seg_height))
    return segments

def update_processes():
    global cpu_usage, fragmentation, memory_history
    if not paused:
        for proc in processes:
            proc.size += random.randint(-50, 50)
            proc.size = max(256, min(MEMORY_SIZE, proc.size))
        cpu_usage = min(100, max(0, cpu_usage + random.randint(-5, 5)))
        fragmentation = calculate_fragmentation()
        memory_history.append(sum(proc.size for proc in processes))
        if len(memory_history) > 100:
            memory_history.pop(0)

def calculate_fragmentation():
    total_used = sum(proc.size for proc in processes)
    free = MEMORY_SIZE - total_used
    if len(processes) == 0:
        return 0
    return (free / MEMORY_SIZE) * 100

def draw_stats():
    total_used = sum(proc.size for proc in processes)
    free = MEMORY_SIZE - total_used
    stats = [
        f"Total Memory: {MEMORY_SIZE}B",
        f"Used: {total_used}B",
        f"Free: {free}B",
        f"Processes: {len(processes)}",
        f"CPU Usage: {cpu_usage}%",
        f"Fragmentation: {fragmentation:.2f}%"
    ]
    for i, stat in enumerate(stats):
        text = font.render(stat, True, BLACK)
        screen.blit(text, (1020, 200 + i * 30))

def draw_process_table():
    y = 380
    screen.blit(font.render("Process Table:", True, BLACK), (1020, y))
    y += 30
    for proc in processes:
        text = font.render(f"P{proc.id}: {proc.size}B", True, BLACK)
        screen.blit(text, (1020, y))
        y += 20

def draw_memory_bar():
    total_used = sum(proc.size for proc in processes)
    used_ratio = total_used / MEMORY_SIZE
    bar_width = 200
    bar_height = 20
    x = 1020
    y = 630
    pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height))
    pygame.draw.rect(screen, BLUE, (x, y, bar_width * used_ratio, bar_height))
    screen.blit(font.render("Memory Usage:", True, BLACK), (x, y - 25))

def draw_cpu_bar():
    bar_width = 200
    bar_height = 20
    x = 1020
    y = 680
    pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height))
    pygame.draw.rect(screen, ORANGE, (x, y, bar_width * (cpu_usage / 100), bar_height))
    screen.blit(font.render("CPU Usage:", True, BLACK), (x, y - 25))

def draw_memory_representation_bar(x, y, width, height):
    pygame.draw.rect(screen, WHITE, (x, y, width, height))
    total_used = sum(proc.size for proc in processes)
    free = MEMORY_SIZE - total_used

    used_bar_width = (total_used / MEMORY_SIZE) * width
    free_bar_width = (free / MEMORY_SIZE) * width

    pygame.draw.rect(screen, BLUE, (x, y, used_bar_width, height))
    pygame.draw.rect(screen, GREEN, (x + used_bar_width, y, free_bar_width, height))

    screen.blit(font.render("Memory Representation:", True, BLACK), (x, y - 25))

def draw_fragmentation_bar():
    bar_width = 200
    bar_height = 20
    x = 1020
    y = 730
    pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height))
    pygame.draw.rect(screen, CYAN, (x, y, bar_width * (fragmentation / 100), bar_height))
    screen.blit(font.render("Fragmentation:", True, BLACK), (x, y - 25))

def draw_memory_pie_chart(x, y, radius):
    total_used = sum(proc.size for proc in processes)
    free = MEMORY_SIZE - total_used
    total = total_used + free
    if total == 0:
        return
    used_angle = 360 * (total_used / total)
    pygame.draw.circle(screen, WHITE, (x, y), radius)
    pygame.draw.arc(screen, BLUE, (x - radius, y - radius, radius * 2, radius * 2), 0, math.radians(used_angle), radius)
    pygame.draw.arc(screen, GREEN, (x - radius, y - radius, radius * 2, radius * 2), math.radians(used_angle), math.radians(360), radius)
    screen.blit(font.render("Memory Usage:", True, BLACK), (x - radius, y + radius + 10))

def draw_memory_line_chart(x, y, width, height):
    pygame.draw.rect(screen, WHITE, (x, y, width, height))
    if len(memory_history) > 1:
        max_memory = max(memory_history)
        if max_memory > 0:
            points = []
            for i, memory_used in enumerate(memory_history):
                point_x = x + (i / (len(memory_history) - 1)) * width
                point_y = y + (1 - (memory_used / max_memory)) * height
                points.append((point_x, point_y))
            pygame.draw.lines(screen, BLUE, False, points)
    screen.blit(font.render("", True, BLACK), (x, y - 25))

# Main loop
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            for button in buttons:
                button.clicked(pos)
        elif event.type == pygame.MOUSEMOTION:
            pos = pygame.mouse.get_pos()
            for button in buttons:
                button.check_hover(pos)

    screen.fill(GRAY)
    
    draw_paging(50, 50, 300, 350)
    draw_segmentation(400, 50, 300, 350)
    draw_first_fit(50, 450, 300, 350)
    draw_memory_line_chart(400, 450, 300, 350)
    draw_memory_pie_chart(850, 150, 100) # pie chart added
    
    for button in buttons:
        button.draw()
    draw_stats()
    draw_process_table()
    draw_memory_bar()
    draw_cpu_bar()
    draw_memory_representation_bar(1020, 580, 200, 20)
    draw_fragmentation_bar()

    titles = [
        ("Paging Memory", 150, 30),
        ("Segmented Memory", 500, 30),
        ("First-Fit Allocation", 150, 430),
        ("Memory Usage ", 500, 430)
    ]
    for title, x, y in titles:
        screen.blit(font.render(title, True, BLACK), (x, y))
    
    update_processes()
    pygame.display.flip()
    clock.tick(30)

pygame.quit()