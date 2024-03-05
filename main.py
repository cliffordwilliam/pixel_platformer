import pygame
import sys
from os import path
import json

FPS = 60
NATIVE_WIDTH = 432
NATIVE_HEIGHT = 288
NATIVE_SIZE = (NATIVE_WIDTH, NATIVE_HEIGHT)
RESOLUTION_SCALE = 4
WINDOW_WIDTH = NATIVE_WIDTH * RESOLUTION_SCALE
WINDOW_HEIGHT = NATIVE_HEIGHT * RESOLUTION_SCALE
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
TILE_SIZE = 18
BIG_TILE_SIZE = 24
NATIVE_WIDTH_TILES = NATIVE_WIDTH // TILE_SIZE
NATIVE_HEIGHT_TILES = NATIVE_HEIGHT // TILE_SIZE
NATIVE_SIZE_TILES = (NATIVE_WIDTH_TILES, NATIVE_HEIGHT_TILES)
CG_PIXEL_3x5_FONT_PATH = path.join('fonts', 'cg-pixel-3x5.ttf')
CG_PIXEL_3x5_FONT_HEIGHT = 5
SPRITE_SHEET_PNG_PATH = path.join('images', 'sprite_sheet.png')
SPRITE_SHEET_DATA_PATH = path.join('data', 'sprite_sheet.json')

pygame.init()
clock = pygame.time.Clock()
native_surface = pygame.Surface(NATIVE_SIZE)
window_surface = pygame.display.set_mode(WINDOW_SIZE)
font = pygame.font.Font(CG_PIXEL_3x5_FONT_PATH, CG_PIXEL_3x5_FONT_HEIGHT)
is_debug = False


class Sprite(pygame.sprite.Sprite):
    def __init__(self, groups, sprite_sheet_surface, position, real_rect, frames_list):
        super().__init__(groups)
        self.image = sprite_sheet_surface
        self.rect = self.image.get_frect(topleft=position)  # Sprite sheet rect
        self.real_rect = real_rect  # Frame rect
        self.real_rect.topleft = self.rect.topleft
        self.frames_list = frames_list
        self.frame_index = 0
        # Debug
        self.mask = None
        self.mask_id = 0


class Group(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

    def draw(self, native_surface, camera_rect):
        for sprite in self:
            # Bring real rect to rect
            sprite.real_rect.topleft = sprite.rect.topleft
            # Get render position
            sprite_rect_render_position = (
                sprite.rect.x - camera_rect.x,
                sprite.rect.y - camera_rect.y
            )
            # Update sprite frame
            sprite_frame_region = sprite.frames_list[sprite.frame_index]
            # Render
            native_surface.blit(
                sprite.image,
                sprite_rect_render_position,
                sprite_frame_region,
            )
            if is_debug:
                # Draw real rect
                pygame.draw.rect(
                    native_surface,
                    "red",
                    pygame.FRect(
                        sprite_rect_render_position[0],
                        sprite_rect_render_position[1],
                        sprite.real_rect.width,
                        sprite.real_rect.height,
                    ),
                    1
                )
                # Draw mask id
                text_surface = font.render(
                    str(sprite.mask_id),
                    False,
                    "white"
                )
                text_rect = text_surface.get_frect(
                    bottomleft=sprite_rect_render_position
                )
                native_surface.blit(
                    text_surface,
                    text_rect
                )
                # Draw mask
                mask_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                mask_surf.set_alpha(100)
                bit_size = TILE_SIZE//3
                for bit_y, row in enumerate(sprite.mask):
                    for bit_x, m in enumerate(row):
                        if m == 1:
                            pygame.draw.rect(
                                mask_surf,
                                "white",
                                (
                                    bit_x * bit_size,
                                    bit_y * bit_size,
                                    bit_size,
                                    bit_size
                                )
                            )
                native_surface.blit(
                    mask_surf, (
                        sprite_rect_render_position[0],
                        sprite_rect_render_position[1]
                    )
                )


class LevelEditor():
    def __init__(self):
        # One scene one sprite sheet
        self.sprite_sheet_surface = pygame.image.load(
            SPRITE_SHEET_PNG_PATH
        ).convert_alpha()
        # Load this sprite sheet data and store it
        with open(SPRITE_SHEET_DATA_PATH, 'r') as file:
            json_data = json.load(file)
        for sprite_name, sprite_data in json_data.items():
            frect_frames_list = []
            for frame in sprite_data["frames_list"]:
                frect = pygame.Rect(
                    frame["x"], frame["y"], frame["w"], frame["h"]
                )
                frect_frames_list.append(pygame.FRect(frect))
            sprite_data["frames_list"] = frect_frames_list
        self.sprite_sheet_data = json_data
        self.grass_block_bitmasks = {
            int(key): value for key, value in self.sprite_sheet_data["grass_block"]["bitmasks"].items()
        }
        # Groups
        self.group = Group()
        # Things are drawn relative to this
        self.camera_rect = pygame.FRect(
            0,
            0,
            NATIVE_WIDTH,
            NATIVE_HEIGHT
        )

    def input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Get mouse position
            mouse_window_position = pygame.mouse.get_pos()
            mouse_native_render_grid_snapped = (
                ((mouse_window_position[0] // RESOLUTION_SCALE) +
                 int(self.camera_rect.x)) // TILE_SIZE * TILE_SIZE,
                ((mouse_window_position[1] // RESOLUTION_SCALE) +
                 int(self.camera_rect.y)) // TILE_SIZE * TILE_SIZE
            )
            # Instance tile on mouse click
            Sprite(
                self.group,
                self.sprite_sheet_surface,
                mouse_native_render_grid_snapped,
                pygame.FRect(
                    0,
                    0,
                    TILE_SIZE,
                    TILE_SIZE
                ),
                self.sprite_sheet_data["grass_block"]["frames_list"]
            )
            # Check each tile
            for this in self.group:
                # Compare this tile with everyone else to find neighbours
                br = 0
                b = 0
                bl = 0
                r = 0
                l = 0
                tr = 0
                t = 0
                tl = 0
                for other in self.group:
                    dx = int(other.rect.x-this.rect.x) // TILE_SIZE
                    dy = int(other.rect.y-this.rect.y) // TILE_SIZE
                    # This other is too far, find someone else
                    if abs(dx) > 1 or abs(dy) > 1:
                        continue
                    t += dx == 0 and dy == -1
                    r += dx == 1 and dy == 0
                    b += dx == 0 and dy == 1
                    l += dx == -1 and dy == 0
                    br += dx == 1 and dy == 1
                    bl += dx == -1 and dy == 1
                    tr += dx == 1 and dy == -1
                    tl += dx == -1 and dy == -1
                tr = tr and t and r
                tl = tl and t and l
                br = br and b and r
                bl = bl and b and l
                mask_id = (br << 7) | (b << 6) | (bl << 5) | (
                    r << 4) | (l << 3) | (tr << 2) | (t << 1) | tl
                this.mask_id = mask_id
                mask = [
                    [tl, t, tr],
                    [l, 1, r],
                    [bl, b, br]
                ]
                this.mask = mask
                this.frame_index = self.grass_block_bitmasks[mask_id]

    def update(self, native_surface, dt):
        # Arrow keys direction
        key_is_pressed = pygame.key.get_pressed()
        direction_x = key_is_pressed[pygame.K_RIGHT] - \
            key_is_pressed[pygame.K_LEFT]
        direction_y = key_is_pressed[pygame.K_DOWN] - \
            key_is_pressed[pygame.K_UP]
        # Move camera with arrow keys
        self.camera_rect.left += direction_x
        self.camera_rect.top += direction_y
        # Clear
        native_surface.fill("black")
        # Vertical lines
        for i in range(NATIVE_WIDTH_TILES):
            x = ((i * TILE_SIZE) - self.camera_rect.left) % NATIVE_WIDTH
            pygame.draw.line(
                native_surface,
                "grey5",
                (x, 0),
                (x, NATIVE_HEIGHT)
            )
        # Horizontal lines
        for i in range(NATIVE_HEIGHT_TILES):
            y = ((i * TILE_SIZE) - self.camera_rect.top) % NATIVE_HEIGHT
            pygame.draw.line(
                native_surface,
                "grey5",
                (0, y),
                (NATIVE_WIDTH, y)
            )
        # Group
        self.group.draw(native_surface, self.camera_rect)


current_scene = LevelEditor()

while 1:
    dt = clock.tick(FPS) / 1000
    for event in pygame.event.get():
        # Close window
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Debug toggle
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_0:
                is_debug = not is_debug
        # Scene event
        current_scene.input(event)
    # Scene update
    current_scene.update(native_surface, dt)
    # Resize native
    pygame.transform.scale_by(native_surface, RESOLUTION_SCALE, window_surface)
    pygame.display.update()
