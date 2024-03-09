import pygame as pg
from sys import exit
from os import path
from json import dump, load

pg.init()

# Constants

# Tiles are squares
TILE_SIZE = 18

# Room minimum size
ROOM_WIDTH_TILE_UNIT = 24
ROOM_HEIGHT_tile_unit = 16
ROOM_WIDTH = ROOM_WIDTH_TILE_UNIT * TILE_SIZE
ROOM_HEIGHT = ROOM_HEIGHT_tile_unit * TILE_SIZE

# Font
FONT_PATH = path.join('fonts', 'cg-pixel-3x5.ttf')
FONT_HEIGHT = 5
FONT = pg.font.Font(
    FONT_PATH,
    FONT_HEIGHT
)

# Paths
GRID_PNG_PATH = path.join('images', 'grid.png')
SPRITE_SHEET_PNG_PATH = path.join('images', 'sprite_sheet.png')
SPRITE_SHEET_JSON_PATH = path.join('data', 'sprite_sheet.json')
ROOMS_DIR_PATH = path.join('rooms')
LOAD_ROOM_JSON_PATH = path.join(ROOMS_DIR_PATH, 'room1.json')

# Native position and dimensions data
NATIVE_RECT = pg.Rect(
    0,
    0,
    ROOM_WIDTH_TILE_UNIT * TILE_SIZE,
    ROOM_HEIGHT_tile_unit * TILE_SIZE
)

# Blit everything here
NATIVE_SURFACE = pg.Surface(
    (
        NATIVE_RECT.width,
        NATIVE_RECT.height
    )
)

# Dt generator and loop speed limiter
CLOCK = pg.time.Clock()

# Game max fps
FPS = 60


class Game():
    # Stores non constant game data that you can change, it has automatic setters and getters.

    def __init__(self):
        # There can only be 1 scene at a time
        self.scene = None

        # Debug flag
        self.is_debug = False

        # Resolution scale
        self.resolution_scale = 3

        # Blit NATIVE_SURFACE here
        self.window_surface = pg.display.set_mode(
            (
                NATIVE_RECT.width * self.resolution_scale,
                NATIVE_RECT.height * self.resolution_scale
            )
        )

    # SET self.resolution_scale:
        # window_surface
    @property
    def resolution_scale(self):
        return self._resoltion_scale

    @resolution_scale.setter
    def resolution_scale(self, value):
        # Resolution scale
        self._resoltion_scale = value

        self.window_surface = pg.display.set_mode(
            (
                NATIVE_RECT.width * self.resolution_scale,
                NATIVE_RECT.height * self.resolution_scale
            )
        )


game = Game()


class Sprite(pg.sprite.Sprite):
    # Needs a sprite sheet, has regions list to indicate the regions in the sprite sheet that it owns

    def __init__(self, groups, sprite_sheet_surface, position, frames_list, name):
        super().__init__(groups)
        # Sprite sheet
        self.image = sprite_sheet_surface
        self.rect = self.image.get_frect()

        # Sprite sheet with alpha
        self.image_translucent = self.image.copy()
        self.image_translucent.set_alpha(128)

        # Frames list
        self.frames_list = frames_list
        self.frames_list_len = len(self.frames_list)
        self.frames_list_len_minus_one = self.frames_list_len - 1

        # Frame index
        self.frame_index = 0

        # Frame
        self.frame = self.frames_list[self.frame_index]
        self.frame_frect = pg.FRect(
            self.rect.x,
            self.rect.y,
            self.frame[2],
            self.frame[3]
        )

        # Sprite position: move position -> move rect -> move frame_frect
        self.position = pg.math.Vector2(position)
        # TODO: For in game, add children with offset and origin offset - So you can attach things together and move actor origin to feet

        # Name
        self.name = name

    # SET self.position:
        # self.rect.x
        # self.rect.y
        # self.frame_frect.x
        # self.frame_frect.y
    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.rect.x = self.position.x
        self.rect.y = self.position.y
        self.frame_frect.x = self.position.x
        self.frame_frect.y = self.position.y

    # SET frame_index:
        # self.frame
    @property
    def frame_index(self):
        return self._frame_index

    @frame_index.setter
    def frame_index(self, value):
        if 0 <= value < self.frames_list_len:
            self._frame_index = value
            self.frame = self.frames_list[self.frame_index]


class Group(pg.sprite.Group):
    # Acts like a layer, draws each sprite with camera offset

    def __init__(self):
        super().__init__()

    def draw(self, camera_frect, group):
        # Draw each sprite in this group
        for sprite in self:
            # Original or translucnet version?
            image = sprite.image

            # Not on group? choose translucent version
            if group != sprite.groups()[0]:
                image = sprite.image_translucent

            # Get camera offset position
            sprite_rect_render_position = (
                sprite.rect.x - camera_frect.x,
                sprite.rect.y - camera_frect.y
            )

            # Render with camera offset position
            NATIVE_SURFACE.blit(
                image,
                sprite_rect_render_position,
                sprite.frame,
            )

            # Debug draw
            if game.is_debug:
                # Render frame in real position
                NATIVE_SURFACE.blit(
                    image,
                    (sprite.rect.x, sprite.rect.y),
                    sprite.frame,
                )

                # Render sprite sheet rect in real position
                pg.draw.rect(
                    NATIVE_SURFACE,
                    "red",
                    sprite.rect,
                    1
                )

                # Render frame rect in real position
                pg.draw.rect(
                    NATIVE_SURFACE,
                    "green",
                    sprite.frame_frect,
                    1
                )

                # Draw frame rect with camera offset
                pg.draw.rect(
                    NATIVE_SURFACE,
                    "red",
                    pg.FRect(
                        sprite_rect_render_position[0],
                        sprite_rect_render_position[1],
                        sprite.frame_frect.width,
                        sprite.frame_frect.height
                    ),
                    1
                )


class RoomEditor():
    def __init__(self):
        # Things are drawn relative to this

        self.camera_frect = pg.FRect(
            0,
            0,
            NATIVE_RECT.width,
            NATIVE_RECT.height
        )
        self.camera_velocity = pg.math.Vector2()
        self.camera_max_speed = 180.0
        self.camera_lerp_weight = 0.12

        # Key inputs
        self.is_right_pressed = 0
        self.is_left_pressed = 0
        self.is_up_pressed = 0
        self.is_down_pressed = 0

        # Mouse input
        self.is_lmb_pressed = False
        self.is_rmb_pressed = False

        # Sprite sheet surface
        self.sprite_sheet_path = SPRITE_SHEET_PNG_PATH  # To be saved
        self.sprite_sheet_surface = pg.image.load(
            self.sprite_sheet_path
        ).convert_alpha()

        # Grid
        self.grid_surface = pg.image.load(
            GRID_PNG_PATH
        ).convert_alpha()
        self.grid_rect = self.grid_surface.get_frect()

        # To iterate over the sprites
        self.sprite_names_list = []

        # Pre process json
        with open(SPRITE_SHEET_JSON_PATH, 'r') as file:
            json_data = load(file)
        for sprite_name, sprite_data in json_data.items():
            # Fill sprite names list
            self.sprite_names_list.append(sprite_name)
            frames_list = []
            # Frames_list: dict -> tuple
            for frame in sprite_data["frames_list"]:
                tuple_frame = (
                    frame["x"], frame["y"], frame["w"], frame["h"]
                )
                frames_list.append((tuple_frame))
            sprite_data["frames_list"] = frames_list
            # Bitmasks key: str -> int
            sprite_data["bitmasks"] = {
                int(key): value for key, value in sprite_data["bitmasks"].items()}

        # self.sprite_sheet_dict ready
        self.sprite_sheet_dict = json_data
        self.sprite_names_list_len = len(self.sprite_names_list)
        self.sprite_name_index = 0
        self.sprite_name = self.sprite_names_list[self.sprite_name_index]
        self.sprite_frames_list = self.sprite_sheet_dict[self.sprite_name]["frames_list"]
        self.sprite_frames_list_len = len(self.sprite_frames_list)
        self.sprite_bitmasks = self.sprite_sheet_dict[self.sprite_name]["bitmasks"]
        self.frame_index = 0

        # Sprite name text
        self.sprite_name_text_surface = FONT.render(
            f"mouse wheel sprite: {self.sprite_name}",
            False,
            "white"
        )
        self.sprite_name_text_rect = self.sprite_name_text_surface.get_rect(
            topright=(NATIVE_RECT.width - FONT_HEIGHT, FONT_HEIGHT)
        )

        # Room settings
        self.room_topleft_room_unit = (0, 0)
        self.room_scale = (2, 1)

        # Room size: To make the list
        self.room_width_tile_unit = ROOM_WIDTH_TILE_UNIT * self.room_scale[0]
        self.room_height_tile_unit = ROOM_HEIGHT_tile_unit * self.room_scale[1]

        # To get / set tile from list
        self.room_topleft_tile_unit = (
            self.room_topleft_room_unit[0] * ROOM_WIDTH_TILE_UNIT,
            self.room_topleft_room_unit[1] * ROOM_HEIGHT_tile_unit
        )

        # For drawing limit and bringing camera to rect
        self.room_topleft = (
            self.room_topleft_room_unit[0] * ROOM_WIDTH,
            self.room_topleft_room_unit[1] * ROOM_HEIGHT
        )
        self.room_width = self.room_width_tile_unit * TILE_SIZE
        self.room_height = self.room_height_tile_unit * TILE_SIZE

        # Bring camera to room top left
        self.camera_frect.topleft = self.room_topleft

        room = []
        total = self.room_width_tile_unit * self.room_height_tile_unit
        for _ in range(total):
            room.append(0)

        self.rooms_list = [
            room.copy(),
            room.copy(),
            room.copy(),
        ]

        # Groups
        self.groups_list = [
            Group(),
            Group(),
            Group(),
        ]
        self.groups_list_len = len(self.groups_list)
        self.group_index = 0
        self.group = self.groups_list[self.group_index]
        self.room = self.rooms_list[self.group_index]

        # Group text
        self.group_text_surface = FONT.render(
            f"q/e group: {self.group_index}",
            False,
            "white"
        )
        self.group_text_rect = self.group_text_surface.get_rect(
            topleft=(FONT_HEIGHT, FONT_HEIGHT)
        )

        # Info text
        self.info_text_surface = FONT.render(
            f"p key: debug\n\nspace key: save\n\nwasd keys: move camera",
            False,
            "white"
        )
        self.info_text_rect = self.info_text_surface.get_rect(
            bottomleft=(FONT_HEIGHT, NATIVE_RECT.height - FONT_HEIGHT)
        )

    # SET self.sprite_name
        # self.sprite_frames_list
        # self.sprite_frames_list_len
        # self.sprite_bitmasks
        # self.frame_index
        # self.sprite_name_text_surface
    @property
    def sprite_name(self):
        return self._sprite_name

    @sprite_name.setter
    def sprite_name(self, value):
        if value in self.sprite_sheet_dict:
            self._sprite_name = value
            self.sprite_frames_list = self.sprite_sheet_dict[self.sprite_name]["frames_list"]
            self.sprite_frames_list_len = len(self.sprite_frames_list)
            self.sprite_bitmasks = self.sprite_sheet_dict[self.sprite_name]["bitmasks"]
            self.frame_index = 0
            self.sprite_name_text_surface = FONT.render(
                f"mouse wheel sprite: {self.sprite_name}",
                False,
                "white"
            )

    # SET self.sprite_name_index
        # self.sprite_name
    @property
    def sprite_name_index(self):
        return self._sprite_name_index

    @sprite_name_index.setter
    def sprite_name_index(self, value):
        if 0 <= value < self.sprite_names_list_len:
            self._sprite_name_index = value
            self.sprite_name = self.sprite_names_list[self.sprite_name_index]

    # SET self.group_index
        # self.group
        # self.group_text_surface
        # self.room
    @property
    def group_index(self):
        return self._group_index

    @group_index.setter
    def group_index(self, value):
        if 0 <= value < self.groups_list_len:
            self._group_index = value
            self.group = self.groups_list[self.group_index]
            self.group_text_surface = FONT.render(
                f"q/e group: {self.group_index}",
                False,
                "white"
            )
            self.room = self.rooms_list[self.group_index]

    # Coordinate -> Object
    def get_tile_from_room(self, x_tile_unit, y_tile_unit):
        # Bring room back to origin - array top left is always 0 0
        x_tile_unit -= self.room_topleft_tile_unit[0]
        y_tile_unit -= self.room_topleft_tile_unit[1]
        if (0 <= x_tile_unit < self.room_width_tile_unit) and (0 <= y_tile_unit < self.room_height_tile_unit):
            return self.room[y_tile_unit * self.room_width_tile_unit + x_tile_unit]
        return -1

    # Set object with coordinate
    def set_tile_from_room(self, x_tile_unit, y_tile_unit, value):
        # Bring room back to origin - array top left is always 0 0
        x_tile_unit -= self.room_topleft_tile_unit[0]
        y_tile_unit -= self.room_topleft_tile_unit[1]
        if (0 <= x_tile_unit < self.room_width_tile_unit) and (0 <= y_tile_unit < self.room_height_tile_unit):
            self.room[y_tile_unit *
                      self.room_width_tile_unit + x_tile_unit] = value

    # Autotile
    def update_bitmasks(self, this, position_tile_unit, last=False):
        if game.is_debug:
            # Get in_game position
            sprite_rect_render_position = (
                this.frame_frect.x - self.camera_frect.x,
                this.frame_frect.y - self.camera_frect.y
            )
            pg.draw.rect(
                NATIVE_SURFACE,
                "green",
                pg.FRect(
                    sprite_rect_render_position[0],
                    sprite_rect_render_position[1],
                    this.frame_frect.width,
                    this.frame_frect.height
                ),
            )

        # Raw bits
        br, b, bl, r, l, tr, t, tl = 0, 0, 0, 0, 0, 0, 0, 0

        x = position_tile_unit[0]
        y = position_tile_unit[1]
        neighbour_tile_units = [
            (x - 1, y - 1), (x - 0, y - 1), (x + 1, y - 1),
            (x - 1, y - 0),                 (x + 1, y - 0),
            (x - 1, y + 1), (x - 0, y + 1), (x + 1, y + 1)
        ]
        found_neighbours_list = []
        for pos in neighbour_tile_units:
            # Get tile from map
            neighbour = self.get_tile_from_room(pos[0], pos[1])

            # Air? check other position
            if neighbour == 0:
                continue

            # Outside room? check other position
            if neighbour == -1:
                continue

            # I'm ground tile?
            if this.name in ["grass_block", "dirt_block", "snow_block"]:
                # But neighbour is not?
                if neighbour.name not in ["grass_block", "dirt_block", "snow_block"]:
                    continue

            # I'm not ground?
            else:
                # Neighbour is not kind? check other position
                if neighbour.name != this.name:
                    continue

            # Found neighbour!
            found_neighbours_list.append(
                {
                    "neighbour": neighbour,
                    "pos": pos
                }
            )

            # Tell my neighbour to update their frame index
            if last == False:
                self.update_bitmasks(
                    neighbour,
                    pos,
                    last=True
                )

            dx = neighbour.rect.x - this.rect.x
            dy = neighbour.rect.y - this.rect.y
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

        # Update frame index with cooked bitmask
        this.frame_index = self.sprite_bitmasks[mask_id]

    def get_mouse_positions(self, game):
        pos = pg.mouse.get_pos()

        # Calculate mouse position in global coordinates (for UI clicks)
        mouse_global = (
            pos[0] // game.resolution_scale,
            pos[1] // game.resolution_scale
        )

        # Calculate mouse position snapped to game grid (for tile placement clicks)
        mouse_snapped_in_game = (
            (
                mouse_global[0] + self.camera_frect.x
            ) // TILE_SIZE * TILE_SIZE,
            (
                mouse_global[1] + self.camera_frect.y
            ) // TILE_SIZE * TILE_SIZE
        )

        # Calculate mouse position snapped to game grid in tile units (for collision checks)
        mouse_snapped_in_game_tile_unit = (
            int(mouse_snapped_in_game[0] // TILE_SIZE),
            int(mouse_snapped_in_game[1] // TILE_SIZE)
        )

        return mouse_global, mouse_snapped_in_game, mouse_snapped_in_game_tile_unit

    def input(self, event):
        # Key up
        if event.type == pg.KEYDOWN:
            # P
            if event.key == pg.K_p:
                game.is_debug = not game.is_debug

            # Right
            if event.key == pg.K_d:
                self.is_right_pressed = 1
            # Left
            if event.key == pg.K_a:
                self.is_left_pressed = 1
            # Up
            if event.key == pg.K_w:
                self.is_up_pressed = 1
            # Down
            if event.key == pg.K_s:
                self.is_down_pressed = 1

            # 1
            if event.key == pg.K_1:
                game.resolution_scale = 1
            # 2
            if event.key == pg.K_2:
                game.resolution_scale = 2
            # 3
            if event.key == pg.K_3:
                game.resolution_scale = 3
            # 4
            if event.key == pg.K_4:
                game.resolution_scale = 4

            # Down
            if event.key == pg.K_q:
                self.group_index -= 1
            # Up
            if event.key == pg.K_e:
                self.group_index += 1

            # W
            if event.key == pg.K_w:
                if self.frame_index < self.sprite_frames_list_len:
                    self.frame_index += 1
            # S
            if event.key == pg.K_s:
                if self.frame_index > 0:
                    self.frame_index -= 1

            # Space
            if event.key == pg.K_SPACE:
                # Find the latest room index in dir
                latest_room_index = 0
                while path.exists(f"rooms/room{latest_room_index + 1}.json"):
                    latest_room_index += 1

                # Create a copy of the rooms list to avoid modification
                processed_rooms_list = []
                for room in self.rooms_list:
                    processed_room = []
                    for cell in room:
                        if cell != 0:
                            processed_cell = {
                                "name": cell.name,
                                "position_x": cell.position.x,
                                "position_y": cell.position.y,
                                "frame_index": cell.frame_index,
                            }
                            processed_room.append(processed_cell)
                    processed_rooms_list.append(processed_room)

                # Package room data
                data = {
                    "sprite_sheet_path": self.sprite_sheet_path,
                    "room_topleft_room_unit_x": self.room_topleft_room_unit[0],
                    "room_topleft_room_unit_y": self.room_topleft_room_unit[1],
                    "room_scale_x": self.room_scale[0],
                    "room_scale_y": self.room_scale[1],
                    "room_width_tile_unit": self.room_width_tile_unit,
                    "room_height_tile_unit": self.room_height_tile_unit,
                    "room_width": self.room_width,
                    "room_height": self.room_height,
                    "rooms_list": processed_rooms_list
                }

                # Generate filename with the next available index
                filename = f"rooms/room{latest_room_index + 1}.json"

                # Serialize the room data to JSON and save it to a file
                with open(filename, "w") as f:
                    dump(data, f, indent=4)

        # Key up
        elif event.type == pg.KEYUP:
            # Right
            if event.key == pg.K_d:
                self.is_right_pressed = 0
            # Left
            if event.key == pg.K_a:
                self.is_left_pressed = 0
            # Up
            if event.key == pg.K_w:
                self.is_up_pressed = 0
            # Down
            if event.key == pg.K_s:
                self.is_down_pressed = 0

        # Mouse
        if event.type == pg.MOUSEBUTTONDOWN:
            # Lmb
            if event.button == 1:
                self.is_lmb_pressed = True

            # Rmb
            if event.button == 3:
                self.is_rmb_pressed = True

        if event.type == pg.MOUSEBUTTONUP:
            # Lmb
            if event.button == 1:
                self.is_lmb_pressed = False

            # Rmb
            if event.button == 3:
                self.is_rmb_pressed = False

        if event.type == pg.MOUSEWHEEL:
            self.sprite_name_index += event.y

    def update(self, dt):
        # Key input
        direction = pg.math.Vector2(
            self.is_right_pressed - self.is_left_pressed,
            self.is_down_pressed - self.is_up_pressed
        )
        if direction.length() > 0:
            direction = direction.normalize()

        # Camera velocity towards target velocity by weight
        self.camera_velocity = self.camera_velocity.lerp(
            direction * self.camera_max_speed, self.camera_lerp_weight)

        # Prevent bouncing
        if self.camera_velocity.length() < 1.0:
            self.camera_velocity *= 0

        # Velocity updates position
        self.camera_frect.topleft += self.camera_velocity * dt

        # Clear
        NATIVE_SURFACE.fill("black")

        # Grid
        grid_render_position = (
            (
                (self.grid_rect.x - self.camera_frect.x) % TILE_SIZE
            ) - TILE_SIZE,
            (
                (self.grid_rect.y - self.camera_frect.y) % TILE_SIZE
            ) - TILE_SIZE
        )
        NATIVE_SURFACE.blit(
            self.grid_surface,
            grid_render_position
        )

        # Line
        line_x = (-self.camera_frect.x) % (NATIVE_RECT.width)
        pg.draw.line(
            NATIVE_SURFACE,
            "grey6",
            (line_x, 0),
            (line_x, NATIVE_RECT.height),
            4
        )
        line_y = (-self.camera_frect.y) % (NATIVE_RECT.height)
        pg.draw.line(
            NATIVE_SURFACE,
            "grey6",
            (0, line_y),
            (NATIVE_RECT.width, line_y),
            4
        )

        # Room rect draw
        pg.draw.rect(
            NATIVE_SURFACE,
            "red",
            pg.FRect(
                self.room_topleft[0] - self.camera_frect.x,
                self.room_topleft[1] - self.camera_frect.y,
                self.room_width,
                self.room_height,
            ),
            1
        )

        # Groups draw
        for group in self.groups_list:
            group.draw(self.camera_frect, self.group)

        # Group text draw
        NATIVE_SURFACE.blit(
            self.group_text_surface,
            self.group_text_rect
        )

        # Sprite name text draw
        NATIVE_SURFACE.blit(
            self.sprite_name_text_surface,
            self.sprite_name_text_rect
        )

        # Info text draw
        NATIVE_SURFACE.blit(
            self.info_text_surface,
            self.info_text_rect
        )

        if game.is_debug:
            fps_surface = FONT.render(
                f"fps: {int(1//dt)}",
                False,
                "white",
            )
            fps_rect = fps_surface.get_rect(
                bottomright=(
                    NATIVE_RECT.width - FONT_HEIGHT, NATIVE_RECT.height - FONT_HEIGHT
                )
            )
            NATIVE_SURFACE.blit(
                fps_surface,
                fps_rect
            )

        # Ruler
        ruler_x = int(self.camera_frect.x // NATIVE_RECT.width) + 1
        ruler_x_surface = FONT.render(
            str(ruler_x),
            False,
            "white"
        )
        rulex_x_rect = ruler_x_surface.get_frect()
        rulex_x_rect.midtop = (line_x + 2, FONT_HEIGHT)
        NATIVE_SURFACE.blit(
            ruler_x_surface,
            rulex_x_rect
        )
        ruler_y = int(self.camera_frect.y // NATIVE_RECT.height) + 1
        ruler_y_surface = FONT.render(
            str(ruler_y),
            False,
            "white"
        )
        ruler_y_rect = ruler_y_surface.get_frect()
        ruler_y_rect.midleft = (FONT_HEIGHT, line_y + 2)
        NATIVE_SURFACE.blit(
            ruler_y_surface,
            ruler_y_rect
        )

        # Origin
        pg.draw.circle(
            NATIVE_SURFACE,
            "red",
            (
                -self.camera_frect.x + 1,
                -self.camera_frect.y + 1
            ),
            2
        )

        # Lmb press
        if self.is_lmb_pressed:
            # Get mouse position
            mouse_global, mouse_snapped_in_game, mouse_snapped_in_game_tile_unit = self.get_mouse_positions(
                game
            )

            # Mouse position -> index -> get tile in room_map
            clicked_cell_item = self.get_tile_from_room(
                mouse_snapped_in_game_tile_unit[0],
                mouse_snapped_in_game_tile_unit[1]
            )

            # Clicked occupied space? Return
            if clicked_cell_item != 0:
                return

            # Clicked outsidde room? Return
            if clicked_cell_item == -1:
                return

            # Handle big tile position - make sure their bottom left is snapped to grid
            position_x = mouse_snapped_in_game[0]
            position_y = mouse_snapped_in_game[1]
            position_y -= self.sprite_frames_list[0][3] - TILE_SIZE

            # Instance tile on mouse click
            sprite = Sprite(
                self.group,
                self.sprite_sheet_surface,
                (position_x, position_y),
                self.sprite_frames_list,
                self.sprite_name
            )
            sprite.frame_index = self.frame_index

            # Save this sprite to room map
            self.set_tile_from_room(
                mouse_snapped_in_game_tile_unit[0],
                mouse_snapped_in_game_tile_unit[1],
                sprite
            )

            # Got no bitmask? return
            if not self.sprite_bitmasks:
                return

            # Autotile check
            self.update_bitmasks(sprite, mouse_snapped_in_game_tile_unit)

        elif self.is_rmb_pressed:
            # Get mouse position
            mouse_global, mouse_snapped_in_game, mouse_snapped_in_game_tile_unit = self.get_mouse_positions(
                game
            )

            # Mouse position -> index -> get tile in room_map
            clicked_cell_item = self.get_tile_from_room(
                mouse_snapped_in_game_tile_unit[0],
                mouse_snapped_in_game_tile_unit[1]
            )

            # Clicked air? Return
            if clicked_cell_item == 0:
                return

            # Clicked outside room? Return
            if clicked_cell_item == -1:
                return

            # Kill it
            clicked_cell_item.kill()

            # Remove from room
            self.set_tile_from_room(
                mouse_snapped_in_game_tile_unit[0],
                mouse_snapped_in_game_tile_unit[1],
                0
            )

            # Got no bitmask? return
            if not self.sprite_bitmasks:
                return

            # Autotile check
            self.update_bitmasks(
                clicked_cell_item, mouse_snapped_in_game_tile_unit
            )


# Set scene
game.scene = RoomEditor()


while 1:
    # Limit fps and get dt
    dt = CLOCK.tick(FPS) / 1000

    # Get events
    for event in pg.event.get():
        # Close window
        if event.type == pg.QUIT:
            pg.quit()
            exit()

        # Scene event
        game.scene.input(event)

    # Scene update
    game.scene.update(dt)

    # Resize native to window
    pg.transform.scale_by(
        NATIVE_SURFACE, game.resolution_scale, game.window_surface
    )

    # Update window
    pg.display.update()
