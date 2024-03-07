import pygame
import sys
from os import path
import json


pygame.init()


# Contains game data
class Game():
    def __init__(self):
        # Game tile sizes
        self.tile_size = 18

        # Fonts paths + height
        self.cg_pixel_3x5_font_path = path.join('fonts', 'cg-pixel-3x5.ttf')
        self.cg_pixel_3x5_font_height = 5

        # Sprite sheets paths
        self.grid_png_path = path.join('images', 'grid.png')
        self.sprite_sheet_png_path = path.join('images', 'sprite_sheet.png')
        self.sprite_sheet_data_path = path.join('data', 'sprite_sheet.json')

        # Game fps
        self.fps = 30

        # Game native size
        self.native_width = 432
        self.native_height = 288
        self.native_size = (self.native_width, self.native_height)

        # Game resolution size setting
        self.resolution_scale = 3

        # Game window size
        self.window_width = self.native_width * self.resolution_scale
        self.window_height = self.native_height * self.resolution_scale
        self.window_size = (self.window_width, self.window_height)

        # Game clock
        self.clock = pygame.time.Clock()

        # Game native and window surfaces
        self.native_surface = pygame.Surface(self.native_size)
        self.window_surface = pygame.display.set_mode(self.window_size)

        # This game uses 1 font only, otherwise instance a font in scene
        self.font = pygame.font.Font(
            self.cg_pixel_3x5_font_path, self.cg_pixel_3x5_font_height
        )

        # Game scene
        self.scene = None

        # Debug flag
        self.is_debug = False

    # Change resolution -> update window size and surface
    @property
    def resolution_scale(self):
        return self._resolution_scale

    @resolution_scale.setter
    def resolution_scale(self, value):
        self._resolution_scale = value

        self.window_width = self.native_width * self.resolution_scale
        self.window_height = self.native_height * self.resolution_scale
        self.window_size = (self.window_width, self.window_height)

        self.window_surface = pygame.display.set_mode(self.window_size)


# Instance game
game = Game()


# Surface, rect, frames, position
# TODO: animation
class Sprite(pygame.sprite.Sprite):
    def __init__(self, groups, sprite_sheet_surface, position, frames_list, name):
        super().__init__(groups)
        # Sprite sheet surface + rect
        self.image = sprite_sheet_surface
        self.rect = self.image.get_frect(topleft=position)

        # Sprite frames list == list of tuples: region blit needs tuple
        self.frames_list = frames_list
        self.frames_list_len = len(self.frames_list)
        self.frames_list_len_index = self.frames_list_len - 1
        self.frame_index = 0

        # Sprite frame == (0, 0, 0, 0) - x y w h + its rect
        self.frame = self.frames_list[self.frame_index]
        self.frame_rect = pygame.FRect(
            self.rect.x,
            self.rect.y,
            self.frame[2],
            self.frame[3]
        )

        # Sprite position
        self.position = pygame.math.Vector2(position)

        # Sprite name
        self.name = name

    # Change position -> rect, frame_rect follows
    # TODO: child follow position
    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = value
        self.rect.x = self.position.x
        self.rect.y = self.position.y
        self.frame_rect.x = self.position.x
        self.frame_rect.y = self.position.y

    # Change frame index -> change frame
    @property
    def frame_index(self):
        return self._frame_index

    @frame_index.setter
    def frame_index(self, value):
        if 0 <= value < self.frames_list_len:
            self._frame_index = value
            self.frame = self.frames_list[self._frame_index]


# Custom draw -> draw a small region from sprite sheet. Camera offset
class Group(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

    def draw(self, native_surface, camera_rect):
        # Draw each sprite in this group
        for sprite in self:
            # Blit a region of the sprite sheet to native surface
            # native_surface.blit(
            #     sprite.image,
            #     (sprite.rect.x, sprite.rect.y),
            #     sprite.frame,
            # )

            # Get in_game position
            sprite_rect_render_position = (
                sprite.rect.x - camera_rect.x,
                sprite.rect.y - camera_rect.y
            )

            # Render with in_game position
            native_surface.blit(
                sprite.image,
                sprite_rect_render_position,
                sprite.frame,
            )

            # Debug draw
            if game.is_debug:
                # Draw image rect global
                pygame.draw.rect(
                    native_surface,
                    "red",
                    sprite.rect,
                    1
                )
                # Draw frame rect global
                pygame.draw.rect(
                    native_surface,
                    "green",
                    sprite.frame_rect,
                    1
                )

                # Draw frame rect in_game
                # pygame.draw.rect(
                #     native_surface,
                #     "red",
                #     pygame.Rect(
                #         sprite_rect_render_position[0],
                #         sprite_rect_render_position[1],
                #         TILE_SIZE,
                #         TILE_SIZE
                #     ),
                #     1
                # )


class RoomEditor():
    def __init__(self):
        # Mouse input
        self.is_lmb_pressed = False
        self.is_rmb_pressed = False

        # Special grid surface
        self.grid_surface = pygame.image.load(
            game.grid_png_path
        ).convert_alpha()
        self.grid_rect = self.grid_surface.get_rect()

        # Sprite sheet surface
        self.sprite_sheet_surface = pygame.image.load(
            game.sprite_sheet_png_path
        ).convert_alpha()

        # To iterate over the sprites
        self.sprite_names_list = []
        # Sprite sheet data: frames_list, bitmasks
        with open(game.sprite_sheet_data_path, 'r') as file:
            json_data = json.load(file)
        for sprite_name, sprite_data in json_data.items():
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
        self.sprite_sheet_dict = json_data
        self.sprite_names_list_len = len(self.sprite_names_list)
        self.sprite_name_index = 0
        self.sprite_name = self.sprite_names_list[self.sprite_name_index]
        self.sprite_frames_list = self.sprite_sheet_dict[self.sprite_name]["frames_list"]
        self.sprite_frames_list_len = len(self.sprite_frames_list)
        self.sprite_bitmasks = self.sprite_sheet_dict[self.sprite_name]["bitmasks"]
        self.frame_index = 0

        # Sprite name text
        self.sprite_name_text_surface = game.font.render(
            f"Sprite {self.sprite_name}",
            False,
            "white"
        )
        self.sprite_name_text_rect = self.sprite_name_text_surface.get_rect(
            topleft=(0, game.tile_size * 2)
        )

        # Things are drawn relative to this
        self.camera_rect = pygame.Rect(
            0,
            0,
            game.native_width,
            game.native_height
        )

        # TODO: biggest room is 2 x 3 native size - let player cycle through rooms and edit them accordingly
        self.room_topleft = (0, 0)  # Display this and let player change this

        self.rooms_list_width_room_unit = 3
        # self.rooms_list_height_room_unit = 2  # not used
        # self.rooms_list = [
        #     [], [], [],
        #     [], [], []
        # ]
        self.room_width_tile_unit = 24
        self.room_height_tile_unit = 16
        self.room_groups_list = [
            # Group 1
            [
                [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ], [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ], [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ],
                [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ], [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ], [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ]
            ],
            # Group 2
            [
                [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ], [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ], [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ],
                [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ], [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ], [
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                ]
            ]
        ]
        self.rooms_list = self.room_groups_list[0]
        self.rooms_list_len = len(self.rooms_list)
        self.room_index = 0
        self.room = self.rooms_list[self.room_index]

        # Groups
        self.groups_list = [
            Group(),
            Group()
        ]
        self.groups_list_len = len(self.groups_list)
        self.group_index = 0
        self.group = self.groups_list[self.group_index]

        # Group text
        self.group_text_surface = game.font.render(
            f"group {self.group_index}",
            False,
            "white"
        )
        self.group_text_rect = self.group_text_surface.get_rect()

        # Room text
        self.room_text_surface = game.font.render(
            f"room {self.room_index}",
            False,
            "white"
        )
        self.room_text_rect = self.room_text_surface.get_rect(
            topleft=(0, game.tile_size)
        )

    # Change sprite name -> update frames list and bitmasks
    @property
    def sprite_name(self):
        return self._sprite_name

    @sprite_name.setter
    def sprite_name(self, value):
        if value in self.sprite_sheet_dict:
            self._sprite_name = value
            self.sprite_frames_list = self.sprite_sheet_dict[self.sprite_name]["frames_list"]
            self.sprite_bitmasks = self.sprite_sheet_dict[self.sprite_name]["bitmasks"]
            self.frame_index = 0
            self.sprite_name_text_surface = game.font.render(
                f"group {self.sprite_name}",
                False,
                "white"
            )

    # Change sprite name index -> change sprite_name
    @property
    def sprite_name_index(self):
        return self._sprite_name_index

    @sprite_name_index.setter
    def sprite_name_index(self, value):
        if 0 <= value < self.sprite_names_list_len:
            self._sprite_name_index = value
            self.sprite_name = self.sprite_names_list[self._sprite_name_index]
            self.sprite_frames_list_len = len(self.sprite_frames_list)

    # Change group index -> change group
    @property
    def group_index(self):
        return self._group_index

    @group_index.setter
    def group_index(self, value):
        if 0 <= value < self.groups_list_len:
            self._group_index = value
            self.group = self.groups_list[self._group_index]
            self.group_text_surface = game.font.render(
                f"group {self.group_index}",
                False,
                "white"
            )
            self.rooms_list = self.room_groups_list[self.group_index]
            self.room = self.rooms_list[self.room_index]

    # Change room index -> change room
    @property
    def room_index(self):
        return self._room_index

    @room_index.setter
    def room_index(self, value):
        if 0 <= value < self.rooms_list_len:
            self._room_index = value
            self.room = self.rooms_list[self._room_index]
            self.room_text_surface = game.font.render(
                f"room {self.room_index}",
                False,
                "white"
            )
            i = self.room_index
            y = i // self.rooms_list_width_room_unit
            x = i % self.rooms_list_width_room_unit
            coordinate = (x, y)
            offset_x = coordinate[0] * game.native_width
            offset_y = coordinate[1] * game.native_height
            self.camera_rect.x = offset_x
            self.camera_rect.y = offset_y

    def get_tile_from_room(self, x_tile_unit, y_tile_unit):
        if (0 <= x_tile_unit < self.room_width_tile_unit) and (0 <= y_tile_unit < self.room_height_tile_unit):
            return self.room[y_tile_unit * self.room_width_tile_unit + x_tile_unit]
        return 0

    def set_tile_from_room(self, x_tile_unit, y_tile_unit, value):
        if (0 <= x_tile_unit < self.room_width_tile_unit) and (0 <= y_tile_unit < self.room_height_tile_unit):
            self.room[y_tile_unit *
                      self.room_width_tile_unit + x_tile_unit] = value

    def update_bitmasks(self, this, position_tile_unit, last=False):
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

            # My neighbour!
            found_neighbours_list.append(
                {
                    "neighbour": neighbour,
                    "pos": pos
                }
            )
            dx = neighbour.rect.x - this.rect.x
            dy = neighbour.rect.y - this.rect.y
            t += dx == 0 and dy == -game.tile_size
            r += dx == game.tile_size and dy == 0
            b += dx == 0 and dy == game.tile_size
            l += dx == -game.tile_size and dy == 0
            br += dx == game.tile_size and dy == game.tile_size
            bl += dx == -game.tile_size and dy == game.tile_size
            tr += dx == game.tile_size and dy == -game.tile_size
            tl += dx == -game.tile_size and dy == -game.tile_size
        tr = tr and t and r
        tl = tl and t and l
        br = br and b and r
        bl = bl and b and l
        mask_id = (br << 7) | (b << 6) | (bl << 5) | (
            r << 4) | (l << 3) | (tr << 2) | (t << 1) | tl

        # Update frame index with cooked bitmask
        this.frame_index = self.sprite_bitmasks[mask_id]

        # Tell my neighbour to update their frame index - (current layer)
        if last == False:
            for neighbour_dict in found_neighbours_list:
                self.update_bitmasks(
                    neighbour_dict["neighbour"],
                    neighbour_dict["pos"],
                    last=True
                )

    # Scene input
    def input(self, event):
        # Key
        if event.type == pygame.KEYDOWN:
            # P
            if event.key == pygame.K_p:
                game.is_debug = not game.is_debug

            # Right
            if event.key == pygame.K_1:
                game.resolution_scale = 1
            # Right
            if event.key == pygame.K_2:
                game.resolution_scale = 2
            # Right
            if event.key == pygame.K_3:
                game.resolution_scale = 3
            # Right
            if event.key == pygame.K_4:
                game.resolution_scale = 4

            # Right
            if event.key == pygame.K_RIGHT:
                self.room_index += 1

            # Left
            if event.key == pygame.K_LEFT:
                self.room_index -= 1

            # Down
            if event.key == pygame.K_DOWN:
                self.group_index -= 1

            # Up
            if event.key == pygame.K_UP:
                self.group_index += 1

            # A
            if event.key == pygame.K_a:
                self.sprite_name_index -= 1

            # D
            if event.key == pygame.K_d:
                self.sprite_name_index += 1

            # W
            if event.key == pygame.K_w:
                if self.frame_index < self.sprite_frames_list_len:
                    self.frame_index += 1

            # S
            if event.key == pygame.K_s:
                if self.frame_index > 0:
                    self.frame_index -= 1

        # Mouse
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Lmb
            if event.button == 1:
                self.is_lmb_pressed = True

            # Rmb
            if event.button == 3:
                self.is_rmb_pressed = True

        if event.type == pygame.MOUSEBUTTONUP:
            # Lmb
            if event.button == 1:
                self.is_lmb_pressed = False

            # Rmb
            if event.button == 3:
                self.is_rmb_pressed = False

    # Scene update
    def update(self, native_surface, dt):
        # Clear
        native_surface.fill("black")

        # Grid
        grid_render_position = (
            ((self.grid_rect.x - self.camera_rect.x) %
             game.tile_size) - game.tile_size,
            ((self.grid_rect.y - self.camera_rect.y) %
             game.tile_size) - game.tile_size
        )
        native_surface.blit(
            self.grid_surface,
            grid_render_position
        )

        # Groups draw
        for group in self.groups_list:
            group.draw(native_surface, self.camera_rect)

        # Group text draw
        native_surface.blit(
            self.group_text_surface,
            self.group_text_rect
        )

        # Room text draw
        native_surface.blit(
            self.room_text_surface,
            self.room_text_rect
        )

        # Sprite name text draw
        native_surface.blit(
            self.sprite_name_text_surface,
            self.sprite_name_text_rect
        )

        if self.is_lmb_pressed:
            # Get mouse position
            mouse_global = (  # For UI clicks
                event.pos[0] // game.resolution_scale,
                event.pos[1] // game.resolution_scale
            )
            mouse_snapped_in_game = (  # For tile placement clicks
                (mouse_global[0] +
                    self.camera_rect.x) // game.tile_size * game.tile_size,
                (mouse_global[1] +
                    self.camera_rect.y) // game.tile_size * game.tile_size
            )
            mouse_snapped_in_game_tile_unit = (  # For collision check
                # mouse_snapped_in_game[0] // game.tile_size,
                # mouse_snapped_in_game[1] // game.tile_size

                # Use global because we use the room aarray as reference for getting collision
                # Later when you load you have to offset this to render them properly in map
                mouse_global[0] // game.tile_size,
                mouse_global[1] // game.tile_size
            )

            # Mouse position -> index -> get tile in room_map
            clicked_cell_item = self.get_tile_from_room(
                mouse_snapped_in_game_tile_unit[0],
                mouse_snapped_in_game_tile_unit[1]
            )

            # Clicked occupied space? Return
            if clicked_cell_item != 0:
                return

            # Handle big tile position - make sure their bottom left is snapped to grid
            position_x = mouse_snapped_in_game[0]
            position_y = mouse_snapped_in_game[1]
            position_y -= self.sprite_frames_list[0][3] - game.tile_size

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
            mouse_global = (  # For UI clicks
                event.pos[0] // game.resolution_scale,
                event.pos[1] // game.resolution_scale
            )
            mouse_snapped_in_game = (  # For tile placement clicks
                (mouse_global[0] +
                    self.camera_rect.x) // game.tile_size * game.tile_size,
                (mouse_global[1] +
                    self.camera_rect.y) // game.tile_size * game.tile_size
            )
            mouse_snapped_in_game_tile_unit = (  # For collision check
                # mouse_snapped_in_game[0] // game.tile_size,
                # mouse_snapped_in_game[1] // game.tile_size

                # Use global because we use the room aarray as reference for getting collision
                # Later when you load you have to offset this to render them properly in map
                mouse_global[0] // game.tile_size,
                mouse_global[1] // game.tile_size
            )

            # Mouse position -> index -> get tile in room_map
            clicked_cell_item = self.get_tile_from_room(
                mouse_snapped_in_game_tile_unit[0],
                mouse_snapped_in_game_tile_unit[1]
            )

            # Clicked occupied space? Remove it
            if clicked_cell_item != 0:
                clicked_cell_item.kill()

            # remove from room
            self.set_tile_from_room(
                mouse_snapped_in_game_tile_unit[0],
                mouse_snapped_in_game_tile_unit[1],
                0
            )


# Set scene
game.scene = RoomEditor()

while 1:
    # Dt
    dt = game.clock.tick(game.fps) / 1000

    # Get events
    for event in pygame.event.get():
        # Close window
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Scene event
        game.scene.input(event)

    # Scene update
    game.scene.update(game.native_surface, dt)

    # Resize native
    pygame.transform.scale_by(
        game.native_surface, game.resolution_scale, game.window_surface
    )

    # Update window
    pygame.display.update()


# TODO: Save and load system
