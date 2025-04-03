import pygame
import random
import asyncio
import platform

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH = 1200
HEIGHT = 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Management Visualizer with AI Evolution")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 150, 255, 150)
PINK = (255, 100, 150, 150)
GREEN = (100, 255, 100, 150)
YELLOW = (255, 255, 100, 150)
GRAY = (220, 220, 220)
BUTTON_GREEN = (100, 255, 100)
BUTTON_RED = (255, 100, 100)
PURPLE = (200, 100, 255)

# Memory settings
MEMORY_SIZE = 16384
PAGE_SIZE = 1024
MAX_SEGMENTS = 4

# AI Evolution settings
POPULATION_SIZE = 8
MUTATION_RATE = 0.1

# Process class with fitness tracking
class Process:
    def __init__(self, id, size):
        self.id = id
        self.size = size
        self.fitness = 0
    
    def calculate_fitness(self):
        pages_needed = (self.size + PAGE_SIZE - 1) // PAGE_SIZE
        ideal_size = pages_needed * PAGE_SIZE
        waste = ideal_size - self.size
        self.fitness = 1 / (1 + waste)

# UI elements
font = pygame.font.Font(None, 24)
processes = []  # Start with empty list
process_id = 1
generation = 0

# Button class
class Button:
    def __init__(self, x, y, width, height, text, color, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = font.render(text, True, BLACK)
        self.color = color
        self.action = action

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.text, (self.rect.x + 10, self.rect.y + 5))

    def clicked(self, pos):
        if self.rect.collidepoint(pos):
            self.action()
            return True
        return False

# Buttons
buttons = [
    Button(1020, 50, 150, 40, "Add Process", BUTTON_GREEN, lambda: add_process()),
    Button(1020, 100, 150, 40, "Remove Process", BUTTON_RED, lambda: remove_process()),
    Button(1020, 150, 150, 40, "Evolve Now", PURPLE, lambda: evolve_population())
]

def add_process():
    global process_id
    if len(processes) < POPULATION_SIZE:
        processes.append(Process(process_id, random.randint(512, 2048)))
        process_id += 1

def remove_process():
    if processes:
        processes.pop()

def evolve_population():
    global processes, process_id, generation
    if not processes:
        return
    
    for proc in processes:
        proc.calculate_fitness()
    
    processes.sort(key=lambda x: x.fitness, reverse=True)
    survivors = processes[:POPULATION_SIZE//2]
    offspring = []
    
    for _ in range(POPULATION_SIZE - len(survivors)):
        parent1 = random.choice(survivors)
        parent2 = random.choice(survivors)
        child_size = (parent1.size + parent2.size) // 2
        if random.random() < MUTATION_RATE:
            child_size += random.randint(-200, 200)
        child_size = max(256, min(4096, child_size))
        offspring.append(Process(process_id, child_size))
        process_id += 1
    
    processes = survivors + offspring
    generation += 1

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

def draw_best_fit(x, y, width, height):
    pygame.draw.rect(screen, WHITE, (x, y, width, height))
    memory = [(0, MEMORY_SIZE)]
    allocated = []
    
    for proc in processes:
        best_idx = -1
        best_size = MEMORY_SIZE + 1
        for i, (start, size) in enumerate(memory):
            if size >= proc.size and size < best_size:
                best_idx = i
                best_size = size
        if best_idx != -1:
            start, size = memory[best_idx]
            allocated.append((start, proc.size, proc.id))
            memory[best_idx] = (start + proc.size, size - proc.size)
            if memory[best_idx][1] == 0:
                memory.pop(best_idx)
    
    for start, size, proc_id in allocated:
        block_height = (size / MEMORY_SIZE) * height
        pygame.draw.rect(screen, YELLOW, 
                        (x + 40, y + start * height / MEMORY_SIZE, 
                         width - 40, block_height))
        text = font.render(f"P{proc_id} ({size}B)", True, BLACK)
        screen.blit(text, (x + 50, y + start * height / MEMORY_SIZE + 5))

def split_into_segments(process):
    segments = []
    remaining_size = process.size
    segment_count = min(random.randint(1, MAX_SEGMENTS), 
                       (process.size + 255) // 256)
    
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

def draw_stats():
    total_used = sum(proc.size for proc in processes)
    free = MEMORY_SIZE - total_used
    avg_fitness = sum(proc.fitness for proc in processes) / len(processes) if processes else 0
    stats = [
        f"Total Memory: {MEMORY_SIZE}B",
        f"Used: {total_used}B",
        f"Free: {free}B",
        f"Processes: {len(processes)}",
        f"Generation: {generation}",
        f"Avg Fitness: {avg_fitness:.3f}"
    ]
    for i, stat in enumerate(stats):
        text = font.render(stat, True, BLACK)
        screen.blit(text, (1020, 200 + i * 30))

def draw_process_table():
    y = 400
    screen.blit(font.render("Process Table:", True, BLACK), (1020, y))
    y += 30
    for proc in processes:
        text = font.render(f"P{proc.id}: {proc.size}B (F:{proc.fitness:.2f})", True, BLACK)
        screen.blit(text, (1020, y))
        y += 20

async def main():
    running = True
    clock = pygame.time.Clock()
    FPS = 30

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for button in buttons:
                    button.clicked(pos)

        screen.fill(GRAY)
        
        # Draw visualizations
        draw_paging(50, 50, 300, 350)
        draw_segmentation(400, 50, 300, 350)
        draw_first_fit(50, 450, 300, 350)
        draw_best_fit(400, 450, 300, 350)
        
        # Draw UI
        for button in buttons:
            button.draw()
        draw_stats()
        draw_process_table()
        
        # Draw titles
        titles = [
            ("Paging Memory", 150, 30),
            ("Segmented Memory", 500, 30),
            ("First-Fit Allocation", 150, 430),
            ("Best-Fit Allocation", 500, 430)
        ]
        for title, x, y in titles:
            screen.blit(font.render(title, True, BLACK), (x, y))
        
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(1.0 / FPS)

    pygame.quit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())