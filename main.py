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
GRID_PNG_PATH = path.join('images', 'grid.png')
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
        self.rect = self.image.get_rect(topleft=position)  # Sprite sheet rect
        self.real_rect = real_rect  # Frame rect
        self.real_rect.topleft = self.rect.topleft
        self.frames_list = frames_list
        self.frame_index = 0
        self.inflate_rect = self.real_rect.inflate(TILE_SIZE, TILE_SIZE)


class Group(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

    def draw(self, native_surface, camera_rect):
        for sprite in self:
            # Bring real rect to rect
            sprite.real_rect.topleft = sprite.rect.topleft
            sprite.inflate_rect.center = sprite.real_rect.center
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


class LevelEditor():
    def __init__(self):
        # Input flags
        self.is_right_pressed = False
        self.is_left_pressed = False
        self.is_down_pressed = False
        self.is_up_pressed = False

        # One scene one sprite sheet
        self.sprite_sheet_surface = pygame.image.load(
            SPRITE_SHEET_PNG_PATH
        ).convert_alpha()

        # Special grid surface
        self.grid_surface = pygame.image.load(
            GRID_PNG_PATH
        ).convert_alpha()
        self.grid_rect = self.grid_surface.get_rect()

        # Load this sprite sheet data and store it
        with open(SPRITE_SHEET_DATA_PATH, 'r') as file:
            json_data = json.load(file)
        for sprite_name, sprite_data in json_data.items():
            frect_frames_list = []
            for frame in sprite_data["frames_list"]:
                rect = pygame.Rect(
                    frame["x"], frame["y"], frame["w"], frame["h"]
                )
                frect_frames_list.append(pygame.Rect(rect))
            sprite_data["frames_list"] = frect_frames_list
        self.sprite_sheet_data = json_data
        self.sprite_sheet_data["grass_block"]["bitmasks"] = {
            int(key): value for key, value in self.sprite_sheet_data["grass_block"]["bitmasks"].items()
        }

        # Groups
        self.groups = [
            Group()
        ]
        self.current_group_index = 0

        # Things are drawn relative to this
        self.camera_rect = pygame.Rect(
            0,
            0,
            NATIVE_WIDTH,
            NATIVE_HEIGHT
        )

        # Autotile lookup table
        self.autotile_real_rects_groups = [
            []
        ]

        # Create add group button
        self.add_group_button_rect = pygame.Rect(
            NATIVE_WIDTH - TILE_SIZE,
            0,
            TILE_SIZE,
            TILE_SIZE
        )
        self.add_group_button_text_surface = font.render(
            "Add",
            False,
            "black"
        )
        self.add_group_button_text_rect = self.add_group_button_text_surface.get_rect(
            center=self.add_group_button_rect.center
        )

        # Create del group button
        self.del_group_button_rect = pygame.Rect(
            NATIVE_WIDTH - TILE_SIZE * 2,
            0,
            TILE_SIZE,
            TILE_SIZE
        )
        self.del_group_button_text_surface = font.render(
            "Del",
            False,
            "white"
        )
        self.del_group_button_text_rect = self.del_group_button_text_surface.get_rect(
            center=self.del_group_button_rect.center
        )

        # Group button
        self.group_buttons_data_list = []
        self.create_add_group_button()

    def input(self, event):
        # Key
        if event.type == pygame.KEYDOWN:
            # Right
            if event.key == pygame.K_RIGHT:
                self.is_right_pressed = True
            # Left
            if event.key == pygame.K_LEFT:
                self.is_left_pressed = True
            # Down
            if event.key == pygame.K_DOWN:
                self.is_down_pressed = True
            # Up
            if event.key == pygame.K_UP:
                self.is_up_pressed = True
        elif event.type == pygame.KEYUP:
            # Right
            if event.key == pygame.K_RIGHT:
                self.is_right_pressed = False
            # Left
            if event.key == pygame.K_LEFT:
                self.is_left_pressed = False
            # Down
            if event.key == pygame.K_DOWN:
                self.is_down_pressed = False
            # Up
            if event.key == pygame.K_UP:
                self.is_up_pressed = False

        # Mouse
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Get mouse position
            mouse_scaled_global = (
                event.pos[0] // RESOLUTION_SCALE,
                event.pos[1] // RESOLUTION_SCALE
            )
            mouse_scaled_snapped_in_game = (``
                (mouse_scaled_global[0] +
                 self.camera_rect.x) // TILE_SIZE * TILE_SIZE,
                (mouse_scaled_global[1] +
                 self.camera_rect.y) // TILE_SIZE * TILE_SIZE
            )

            # Left click
            if event.button == 1:
                # On add group button click
                if self.add_group_button_rect.collidepoint((mouse_scaled_global)):
                    if len(self.groups) == 15:
                        return
                    self.groups.append(Group())
                    self.autotile_real_rects_groups.append([])
                    self.create_add_group_button()
                    return

                # On add group button click
                if self.del_group_button_rect.collidepoint(mouse_scaled_global):
                    if len(self.groups) == 1:
                        return
                    self.groups.pop()
                    self.autotile_real_rects_groups.pop()
                    self.group_buttons_data_list.pop()
                    self.current_group_index = 0
                    return

                # On group button click
                for button_data in self.group_buttons_data_list:
                    if button_data["rect"].collidepoint(mouse_scaled_global):
                        self.current_group_index = button_data["index"]
                        return

                # On grid click
                for sprite in self.groups[self.current_group_index]:
                    if sprite.rect.topleft == mouse_scaled_snapped_in_game:
                        return

                # Instance tile on mouse click
                sprite = Sprite(
                    self.groups[self.current_group_index],
                    self.sprite_sheet_surface,
                    mouse_scaled_snapped_in_game,
                    pygame.Rect(
                        0,
                        0,
                        TILE_SIZE,
                        TILE_SIZE
                    ),
                    self.sprite_sheet_data["grass_block"]["frames_list"]
                )

                # Add new sprite to lookup table
                self.autotile_real_rects_groups[self.current_group_index].append(
                    sprite
                )

                # Autotile check
                self.update_tile_bitmasks(sprite)

            # Right click
            if event.button == 3:
                # On grid click
                for sprite in self.groups[self.current_group_index]:
                    if sprite.rect.topleft == mouse_scaled_snapped_in_game:
                        # Hold reference
                        this_group_autotile_real_rects = self.autotile_real_rects_groups[
                            self.current_group_index
                        ]

                        # Remove sprite from lookup table
                        this_group_autotile_real_rects.remove(sprite)

                        # Autotile check
                        index_lists = sprite.inflate_rect.collidelistall(
                            this_group_autotile_real_rects
                        )
                        for index in index_lists:
                            other = this_group_autotile_real_rects[index]
                            self.update_tile_bitmasks(other, last=True)

                        # Remove sprite from group
                        sprite.kill()
                        return

    def update(self, native_surface, dt):
        # Arrow keys direction
        direction_x = self.is_right_pressed - self.is_left_pressed
        direction_y = self.is_down_pressed - self.is_up_pressed

        # Move camera with arrow keys
        self.camera_rect.x += direction_x
        self.camera_rect.y += direction_y

        # Clear
        native_surface.fill("black")

        # Grid
        grid_render_position = (
            ((self.grid_rect.x - self.camera_rect.x) % TILE_SIZE) - TILE_SIZE,
            ((self.grid_rect.y - self.camera_rect.y) % TILE_SIZE) - TILE_SIZE
        )
        native_surface.blit(
            self.grid_surface,
            grid_render_position
        )
        x = (-self.camera_rect.x) % (NATIVE_WIDTH)
        pygame.draw.line(
            native_surface,
            "grey6",
            (x, 0),
            (x, NATIVE_HEIGHT),
            4
        )
        y = (-self.camera_rect.y) % (NATIVE_HEIGHT)
        pygame.draw.line(
            native_surface,
            "grey6",
            (0, y),
            (NATIVE_WIDTH, y),
            4
        )

        # Group render
        for group in self.groups:
            group.draw(native_surface, self.camera_rect)

        # Add group button render
        pygame.draw.rect(
            native_surface,
            "white",
            self.add_group_button_rect,
        )
        native_surface.blit(
            self.add_group_button_text_surface,
            self.add_group_button_text_rect
        )

        # Del group button render
        pygame.draw.rect(
            native_surface,
            "black",
            self.del_group_button_rect,
        )
        pygame.draw.rect(
            native_surface,
            "white",
            self.del_group_button_rect,
            1
        )
        native_surface.blit(
            self.del_group_button_text_surface,
            self.del_group_button_text_rect
        )

        # Group button render
        for button_data in self.group_buttons_data_list:
            is_active = button_data["index"] == self.current_group_index
            pygame.draw.rect(
                native_surface,
                "white" if is_active else "Black",
                button_data["rect"],
                # 1
            )
            pygame.draw.rect(
                native_surface,
                "Black" if is_active else "white",
                button_data["rect"],
                1
            )
            native_surface.blit(
                button_data["active_text_surface"] if is_active else button_data["text_surface"],
                button_data["text_rect"]
            )

    def create_add_group_button(self):
        # Get groups len
        len_groups = len(self.groups)

        # Init button
        group_button_rect = pygame.Rect(
            NATIVE_WIDTH - TILE_SIZE * 2,
            TILE_SIZE,
            TILE_SIZE * 2,
            TILE_SIZE
        )
        group_button_text_surface = font.render(
            f"group {len_groups}",
            False,
            "white"
        )
        active_group_button_text_surface = font.render(
            f"group {len_groups}",
            False,
            "Black"
        )
        group_button_rect.y = len_groups * TILE_SIZE
        group_button_text_rect = group_button_text_surface.get_rect(
            center=group_button_rect.center
        )

        # Add button to collection
        self.group_buttons_data_list.append(
            {
                "index": len_groups - 1,
                "rect": group_button_rect,
                "text_surface": group_button_text_surface,
                "active_text_surface": active_group_button_text_surface,
                "text_rect": group_button_text_rect
            }
        )

    def update_tile_bitmasks(self, this, last=False):
        # Get current data
        current_autotile_bitmasks_data = self.sprite_sheet_data["grass_block"]["bitmasks"]

        # Prepare my bits
        br, b, bl, r, l, tr, t, tl = 0, 0, 0, 0, 0, 0, 0, 0

        # Get neighbors
        this_group_autotile_real_rects = self.autotile_real_rects_groups[self.current_group_index]
        index_lists = this.inflate_rect.collidelistall(
            this_group_autotile_real_rects)

        # Early exit if there are no neighbors
        if len(index_lists) == 1:  # Only includes the current tile
            this.frame_index = current_autotile_bitmasks_data[0]
            return

        # Create my bitmask based on my neighbour
        for index in index_lists:
            other = this_group_autotile_real_rects[index]
            if other.rect.topleft == this.rect.topleft:
                continue
            dx = other.rect.x - this.rect.x
            dy = other.rect.y - this.rect.y
            if abs(dx) > TILE_SIZE or abs(dy) > TILE_SIZE:
                continue
            t += dx == 0 and dy == -TILE_SIZE
            r += dx == TILE_SIZE and dy == 0
            b += dx == 0 and dy == TILE_SIZE
            l += dx == -TILE_SIZE and dy == 0
            br += dx == TILE_SIZE and dy == TILE_SIZE
            bl += dx == -TILE_SIZE and dy == TILE_SIZE
            tr += dx == TILE_SIZE and dy == -TILE_SIZE
            tl += dx == -TILE_SIZE and dy == -TILE_SIZE
        tr = tr and t and r
        tl = tl and t and l
        br = br and b and r
        bl = bl and b and l
        mask_id = (br << 7) | (b << 6) | (bl << 5) | (
            r << 4) | (l << 3) | (tr << 2) | (t << 1) | tl

        # Update my frame index with my now ready bitmask
        this.frame_index = current_autotile_bitmasks_data[mask_id]

        # Tell my neighbour to update their frame index
        if last == False:
            for index in index_lists:
                other = this_group_autotile_real_rects[index]
                if other.rect.topleft == this.rect.topleft:
                    continue
                other = this_group_autotile_real_rects[index]
                self.update_tile_bitmasks(other, last=True)
                # TODO: Vary fill later when reading save data: if this.frame_index == 8: this.frame_index = random.choice([8, 14])


current_scene = LevelEditor()

while 1:
    # Dt
    dt = clock.tick(FPS) / 1000

    # Get events
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
