
from collections import deque
import pygame, sys, time
import threading
from queue import Queue
from random import choice

from Client import Client


class Game:

    def __init__(self):

        pygame.init()

        with open("Client\words.txt", 'r') as f:
            self.words = f.read().split("\n")

        self.is_connected = threading.Event()
        self.Client = Client(self.is_connected)

        self.clock = pygame.time.Clock()

        self.counting_times = False

        self.word = None

        self.accept_thread = threading.Thread(target=self.Client.accept_data)
        self.accept_thread.start()

        self.size = self.width, self.height = 1200, 800
        self.screen = pygame.display.set_mode(self.size)
        self.screen.fill([255, 255, 255])

        self.allowed_to_paint = False

        self.queue_needed = threading.Event()

        self.board_extreme_left = 30
        self.board_extreme_right = 800
        self.board_extreme_top = 30
        self.board_extreme_bottom = 700

        self.text_height = 50

        self.topLeft = (self.board_extreme_left, self.board_extreme_top)
        self.topRight = (self.board_extreme_right, self.board_extreme_top)
        self.botLeft = (self.board_extreme_left, self.board_extreme_bottom)
        self.botRight = (self.board_extreme_right, self.board_extreme_bottom)

        self.color_picker_extreme_top = self.board_extreme_bottom
        self.color_picker_extreme_bottom = 760
        self.color_picker_extreme_left = self.board_extreme_left
        self.color_picker_extreme_right = self.board_extreme_right

        self.board_pixels = 60

        self.board_border = 4

        self.view_selected = 0
        self.chat_selected = False
        self.chat_buff = 10

        self.board_colors = [0] * (self.board_pixels * self.board_pixels)

        self.paint_size_x = (self.board_extreme_right - self.board_extreme_left - 2 * self.board_border)/self.board_pixels
        self.paint_size_y = (self.board_extreme_bottom - self.board_extreme_top - 2 * self.board_border)/self.board_pixels

        self.colors = [(255, 255, 255), (0, 0, 0), (232, 39, 5), (227, 164, 5), (56, 227, 5), (19, 207, 175), (19, 35, 207), (207, 19, 207), (158, 52, 235)]
        self.selected_color = choice(self.colors[1:])
        self.color_padding = 5
        self.color_picker_width = (self.color_picker_extreme_right - self.color_picker_extreme_left - self.color_padding) / len(self.colors) - self.color_padding
        self.color_chosen = 0
        self.color_boxes_buffer = 5

        self.chat = [("Hello World, How Are You Doing, I am doing great",(0, 0, 0)), ("This is another message",(227, 164, 5)), ("Hey Jude", (120, 36, 79))]

        self.mousedown = False

        self.board = pygame.draw.polygon(surface=self.screen,
                                         color=(209, 209, 209),
                                         points=[self.topLeft, self.botLeft, self.botRight, self.topRight],
                                         width=4)

        self.colorPicker = pygame.draw.polygon(surface=self.screen,
                                               color=(209, 209, 209),
                                               points=[
                                                   self.botLeft,
                                                   (self.color_picker_extreme_left, self.color_picker_extreme_bottom),
                                                   (self.color_picker_extreme_right, self.color_picker_extreme_bottom),
                                                   self.botRight
                                               ],
                                               width=self.board_border)
        self.colorBoxes = []
        self.colorsIndices = {}

        for ind, color in enumerate(self.colors):
            start_x_color = self.color_padding + self.color_picker_extreme_left + ind * (self.color_picker_width + self.color_padding)
            end_x_color = self.color_padding + self.color_picker_extreme_left + ind * (self.color_picker_width + self.color_padding) + self.color_picker_width
            self.colorBoxes.append(pygame.draw.polygon(self.screen, color=color, points=[
                (start_x_color, self.color_picker_extreme_top + self.color_boxes_buffer),
                (start_x_color, self.color_picker_extreme_bottom - self.color_boxes_buffer),
                (end_x_color, self.color_picker_extreme_bottom - self.color_boxes_buffer),
                (end_x_color, self.color_picker_extreme_top + self.color_boxes_buffer)
            ]))
            self.colorsIndices[color] = (start_x_color, end_x_color)

        self.chat_extreme_left = 850
        self.chat_extreme_right = 1150
        self.chat_extreme_top = self.board_extreme_top
        self.chat_extreme_bottom = self.color_picker_extreme_bottom

        self.expected_width = 1150 - 850 - 20

        self.chat_inp_extreme_left = 870
        self.chat_inp_extreme_right = 1130
        self.chat_inp_extreme_top = self.color_picker_extreme_bottom - 20 - self.text_height
        self.chat_inp_extreme_bottom = self.color_picker_extreme_bottom - 20

        self.draw_chat()

        self.colorFunc = lambda col, x: self.colorsIndices[col][0] < x[0] < self.colorsIndices[col][1]

        self.running = True

        self.paintingThread = threading.Thread(target=self.recv_and_paint)
        self.paintingThread.start()

        self.paint_queue = Queue()

        self.queueThread = threading.Thread(target=self.change_pixel)
        self.queueThread.start()

        self.user_inp = ""

        self.run()

    def re_init(self):
        self.screen.fill([255, 255, 255])
        self.board = pygame.draw.polygon(surface=self.screen,
                                         color=(209, 209, 209),
                                         points=[self.topLeft, self.botLeft, self.botRight, self.topRight],
                                         width=4)

        self.colorPicker = pygame.draw.polygon(surface=self.screen,
                                               color=(209, 209, 209),
                                               points=[
                                                   self.botLeft,
                                                   (self.color_picker_extreme_left, self.color_picker_extreme_bottom),
                                                   (self.color_picker_extreme_right, self.color_picker_extreme_bottom),
                                                   self.botRight
                                               ],
                                               width=self.board_border)
        for ind, color in enumerate(self.colors):
            start_x_color = self.color_padding + self.color_picker_extreme_left + ind * (self.color_picker_width + self.color_padding)
            end_x_color = self.color_padding + self.color_picker_extreme_left + ind * (self.color_picker_width + self.color_padding) + self.color_picker_width
            self.colorBoxes.append(pygame.draw.polygon(self.screen, color=color, points=[
                (start_x_color, self.color_picker_extreme_top + self.color_boxes_buffer),
                (start_x_color, self.color_picker_extreme_bottom - self.color_boxes_buffer),
                (end_x_color, self.color_picker_extreme_bottom - self.color_boxes_buffer),
                (end_x_color, self.color_picker_extreme_top + self.color_boxes_buffer)
            ]))
            self.colorsIndices[color] = (start_x_color, end_x_color)

    def draw_chat(self):

        self.chat_topLeft = (self.chat_extreme_left, self.chat_extreme_top)
        self.chat_topRight = (self.chat_extreme_right, self.chat_extreme_top)
        self.chat_botLeft = (self.chat_extreme_left, self.chat_extreme_bottom)
        self.chat_botRight = (self.chat_extreme_right, self.chat_extreme_bottom)

        self.chat_box = pygame.draw.polygon(surface=self.screen,
                                         color=(209, 209, 209),
                                         points=[self.chat_topLeft, self.chat_botLeft, self.chat_botRight, self.chat_topRight],
                                         width=4)

        self.chat_topLeft = (self.chat_extreme_left + 4, self.chat_extreme_top + 4)
        self.chat_topRight = (self.chat_extreme_right - 4, self.chat_extreme_top + 4)
        self.chat_botLeft = (self.chat_extreme_left + 4, self.color_picker_extreme_bottom - 24 - self.text_height)
        self.chat_botRight = (self.chat_extreme_right - 4, self.color_picker_extreme_bottom - 24 - self.text_height)



        self.chat_inp_topLeft = (self.chat_inp_extreme_left, self.chat_inp_extreme_top)
        self.chat_inp_topRight = (self.chat_inp_extreme_right, self.chat_inp_extreme_top)
        self.chat_inp_botLeft = (self.chat_inp_extreme_left, self.chat_inp_extreme_bottom)
        self.chat_inp_botRight = (self.chat_inp_extreme_right, self.chat_inp_extreme_bottom)

        if not self.chat_selected:
            self.chat_inp = pygame.draw.polygon(surface=self.screen,
                                                color=(209, 209, 209),
                                                points=[self.chat_inp_topLeft, self.chat_inp_botLeft, self.chat_inp_botRight,
                                                        self.chat_inp_topRight],
                                                width=4)
        else:
            self.chat_inp = pygame.draw.polygon(surface=self.screen,
                                                color=self.selected_color,
                                                points=[self.chat_inp_topLeft, self.chat_inp_botLeft, self.chat_inp_botRight,
                                                        self.chat_inp_topRight],
                                                width=4)

        self.font = font = pygame.font.Font('freesansbold.ttf', 15)

        self.show_chat()

    def chat_range(self, mouse_pos):
        return self.chat_inp_extreme_left < mouse_pos[0] < self.chat_inp_extreme_right and \
               self.chat_inp_extreme_top < mouse_pos[1] < self.chat_inp_extreme_bottom

    def show_chat(self):

        pygame.draw.polygon(surface=self.screen,
                            color=(255, 255, 255),
                            points=[self.chat_topLeft, self.chat_botLeft, self.chat_botRight, self.chat_topRight])

        accumulated_height = self.chat_extreme_top + self.chat_buff
        index = self.view_selected
        msg = ""
        msg_color = None
        while accumulated_height < self.chat_inp_extreme_top - self.chat_buff and index < len(self.chat):
            if msg == "":
                msg, msg_color = self.chat[index]
            text = self.font.render(msg, True, msg_color, (255, 255, 255))
            text_rec = text.get_rect()
            temp_ind = len(msg) - 1
            while text_rec.width > self.expected_width:
                temp = msg[:temp_ind]
                text = self.font.render(temp, True, msg_color, (255, 255, 255))
                text_rec = text.get_rect()
                temp_ind -= 1
            if msg[temp_ind+1:].strip() != "":
                msg = msg[temp_ind:].strip()
            else:
                msg = ""
                index += 1
            text_rec.topleft = (self.chat_inp_extreme_left, accumulated_height)
            accumulated_height += text_rec.height + self.chat_buff
            self.screen.blit(text, text_rec)

        if not self.chat_selected:
            self.chat_inp = pygame.draw.polygon(surface=self.screen,
                                                color=(209, 209, 209),
                                                points=[self.chat_inp_topLeft, self.chat_inp_botLeft, self.chat_inp_botRight,
                                                        self.chat_inp_topRight],
                                                width=4)
        else:
            self.chat_inp = pygame.draw.polygon(surface=self.screen,
                                                color=self.selected_color,
                                                points=[self.chat_inp_topLeft, self.chat_inp_botLeft, self.chat_inp_botRight,
                                                        self.chat_inp_topRight],
                                                width=4)

    def in_board(self, pos):
        x, y = pos
        if x > (self.board_extreme_right - self.board_border) or y > (self.board_extreme_bottom - self.board_border):
            return
        x -= self.board_extreme_left + self.board_border
        y -= self.board_extreme_top + self.board_border
        if x < 0 or y < 0:
            return
        return int(x // self.paint_size_x), int(y // self.paint_size_y)

    def run(self):

        while self.running:

            for event in pygame.event.get():

                if event.type == pygame.MOUSEWHEEL:
                    if event.y > 0:
                        self.view_selected = max(0, self.view_selected-1)
                    else:
                        self.view_selected = min(len(self.chat)-1, self.view_selected + 1)
                    self.show_chat()
                    break

                elif event.type == pygame.QUIT:
                    self.running = False
                    self.queue_needed.set()
                    self.Client.soc.close()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.mousedown = True
                    mouse_pos = pygame.mouse.get_pos()
                    if self.chat_range(mouse_pos):
                        self.chat_selected = True
                        self.chat_inp = pygame.draw.polygon(surface=self.screen,
                                                            color=self.selected_color,
                                                            points=[self.chat_inp_topLeft, self.chat_inp_botLeft, self.chat_inp_botRight,
                                                                    self.chat_inp_topRight],
                                                            width=4)
                    elif self.chat_selected:
                        self.chat_selected = False
                        self.chat_inp = pygame.draw.polygon(surface=self.screen,
                                                            color=(209, 209, 209),
                                                            points=[self.chat_inp_topLeft, self.chat_inp_botLeft, self.chat_inp_botRight,
                                                                    self.chat_inp_topRight],
                                                            width=4)
                    if self.color_picker_extreme_bottom > mouse_pos[1] > self.color_picker_extreme_top and self.allowed_to_paint:
                        for i, color in enumerate(self.colors):
                            if self.colorFunc(color, mouse_pos):
                                self.color_chosen = i

                        if self.color_chosen == 0:
                            self.Client.send_data("clean")
                            self.board_colors = [0] * (self.board_pixels * self.board_pixels)
                            self.paint()

                elif event.type == pygame.MOUSEBUTTONUP:
                    self.mousedown = False

                elif event.type == pygame.MOUSEMOTION:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.mousedown and self.allowed_to_paint:
                        self.paint_queue.put(mouse_pos)
                        self.queue_needed.set()

                elif event.type == pygame.KEYDOWN:
                    if self.chat_selected:
                        print(event.key)
                        if event.key == 8:
                            self.user_inp = self.user_inp[:-1]
                            self.update_user_input()
                        if event.key == 13:
                            self.enter_user_inp()
                        elif event.unicode == "":
                            pass
                        elif 31 < ord(event.unicode) < 126:
                            self.user_inp += event.unicode
                            self.update_user_input()
                        else:
                            pass

            if self.allowed_to_paint and (pygame.time.get_ticks() - self.start_time)/1000 > 30:
                print("turn finished")
                self.allowed_to_paint = False
                self.Client.send_data("done")
                self.board_colors = [0] * (self.board_pixels * self.board_pixels)
                self.paint()
            pygame.display.update()

    def update_user_input(self):

        user_input = self.user_inp
        user_color = self.selected_color
        if user_input == self.word:
            user_input = "guessed correctly!"
            user_color = (180, 180, 180)
        text = self.font.render(user_input, True, user_color, (255, 255, 255))
        final_texts = []
        text_recs = [text.get_rect()]
        temp_ind = len(user_input) - 1
        while text_recs[-1].width > (self.expected_width - 50):
            temp = user_input[:temp_ind]
            text = self.font.render(temp, True, user_color, (255, 255, 255))
            text_recs[-1] = text.get_rect()
            if text_recs[-1].width <= (self.expected_width - 50) and user_input[temp_ind:] != "":
                user_input = user_input[temp_ind:]
                final_texts.append(text)
                text = self.font.render(user_input, True, user_color, (255, 255, 255))
                text_recs.append(text.get_rect())
                temp_ind = len(user_input) - 1
            else:
                temp_ind -= 1

        final_texts.append(text)

        self.chat_inp_extreme_top = self.color_picker_extreme_bottom - 20 - self.text_height - (len(text_recs) - 1) * text_recs[0].height

        self.chat_box = pygame.draw.polygon(surface=self.screen,
                                            color=(255, 255, 255),
                                            points=[(self.board_extreme_right + 4, 0),
                                                    (self.board_extreme_right + 4, self.height),
                                                    (self.width, self.height),
                                                    (self.width, 0)])
        self.show_chat()
        self.draw_chat()

        accumulated_height = self.chat_inp_extreme_top + 4
        for i, rect in enumerate(text_recs):
            rect.topleft = (self.chat_inp_extreme_left + 4, accumulated_height)
            accumulated_height += rect.height
            self.screen.blit(final_texts[i], rect)

    def change_pixel(self):
        while self.running:
            self.queue_needed.wait()
            if not self.running:
                return
            paint_indices = self.in_board(self.paint_queue.get())
            if paint_indices:
                i, j = paint_indices
                color = self.board_colors[i * self.board_pixels + j]
                self.board_colors[i * self.board_pixels + j] = self.color_chosen
                try:
                    self.Client.send_data(f"{i} {j} {color}")
                except:
                    return
                pygame.draw.polygon(self.screen,
                                    color=self.colors[color],
                                    points=[
                                        (self.board_extreme_left + self.board_border + i * self.paint_size_x,
                                         self.board_extreme_top + self.board_border + j * self.paint_size_y),
                                        (self.board_extreme_left + self.board_border + i * self.paint_size_x,
                                         self.board_extreme_top + self.board_border + (j + 1) * self.paint_size_y),
                                        (self.board_extreme_left + self.board_border + (i + 1) * self.paint_size_x,
                                         self.board_extreme_top + self.board_border + (j + 1) * self.paint_size_y),
                                        (self.board_extreme_left + self.board_border + (i + 1) * self.paint_size_x,
                                         self.board_extreme_top + self.board_border + j * self.paint_size_y)
                                    ])
                if self.paint_queue.empty() or not self.running:
                    self.queue_needed.clear()

    def paint(self):
        for i in range(self.board_pixels):
            for j in range(self.board_pixels):
                pygame.draw.polygon(self.screen,
                                    self.colors[self.board_colors[i * self.board_pixels + j]],
                                    points=[
                                        (self.board_extreme_left + self.board_border + i * self.paint_size_x, self.board_extreme_top + self.board_border + j * self.paint_size_y),
                                        (self.board_extreme_left + self.board_border + i * self.paint_size_x, self.board_extreme_top + self.board_border + (j+1) * self.paint_size_y),
                                        (self.board_extreme_left + self.board_border + (i+1) * self.paint_size_x, self.board_extreme_top + self.board_border + (j+1) * self.paint_size_y),
                                        (self.board_extreme_left + self.board_border + (i+1) * self.paint_size_x, self.board_extreme_top + self.board_border + j * self.paint_size_y)
                                    ])

    def enter_user_inp(self):
        if self.user_inp.lower() == self.word:
            self.chat.append(("You guessed correctly!", (180, 180, 180)))
        else:
            to_send = f"msg {self.selected_color[0]} {self.selected_color[1]} {self.selected_color[2]} {self.user_inp}"
            self.chat.append((self.user_inp, self.selected_color))
            self.user_inp = ""
            self.Client.send_data(to_send)
        self.chat_inp_extreme_top = self.chat_inp_extreme_top = self.color_picker_extreme_bottom - 20 - self.text_height
        self.chat_box = pygame.draw.polygon(surface=self.screen,
                                            color=(255, 255, 255),
                                            points=[(self.board_extreme_right + 4, 0),
                                                    (self.board_extreme_right + 4, self.height),
                                                    (self.width, self.height),
                                                    (self.width, 0)])
        self.show_chat()
        self.draw_chat()

    def recv_and_paint(self):
        print("trying to connect!")
        self.is_connected.wait()
        print("connected!")
        while self.running:
            try:
                while self.Client.accept_queue.empty() and self.running:
                    pass
                if not self.running:
                    return
                data = self.Client.accept_queue.get()
                print(data.__repr__())
                if data == "clean" or data == "done":
                    self.board_colors = [0] * (self.board_pixels * self.board_pixels)
                    self.paint()
                    continue
                elif data == "your turn done" or data == "your turn ":
                    self.board_colors = [0] * (self.board_pixels * self.board_pixels)
                    self.paint()
                    self.allowed_to_paint = True
                    self.start_time = pygame.time.get_ticks()
                    self.word = choice(self.words)
                    self.chat.append((f"Your turn has begun. You have 30 seconds to draw {self.word}", (180, 180, 180)))
                    self.chat_box = pygame.draw.polygon(surface=self.screen,
                                                        color=(255, 255, 255),
                                                        points=[(self.board_extreme_right + 4, 0),
                                                                (self.board_extreme_right + 4, self.height),
                                                                (self.width, self.height),
                                                                (self.width, 0)])
                    self.show_chat()
                    self.draw_chat()
                    self.Client.send_data(f"word {self.word}")
                elif "msg" in data:
                    _, c1, c2, c3, *msg = data.split()
                    print((c1, c2, c3), msg)
                    self.chat.append((" ".join(msg), (int(c1), int(c2), int(c3))))
                    print(self.chat)
                    self.chat_inp_extreme_top = self.chat_inp_extreme_top = self.color_picker_extreme_bottom - 20 - self.text_height
                    self.chat_box = pygame.draw.polygon(surface=self.screen,
                                                       color=(255, 255, 255),
                                                       points=[(self.board_extreme_right + 4, 0),
                                                               (self.board_extreme_right + 4, self.height),
                                                               (self.width, self.height),
                                                               (self.width, 0)])
                    self.show_chat()
                    self.draw_chat()
                elif "word" in data:
                    _, self.word = data.split()
                else:
                    i, j, color = map(int, data.split())
                    print(f"i: {i}, j: {j}, color: {color}")
                    pygame.draw.polygon(self.screen,
                                        color=self.colors[color],
                                        points=[
                                            (self.board_extreme_left + self.board_border + i * self.paint_size_x,
                                             self.board_extreme_top + self.board_border + j * self.paint_size_y),
                                            (self.board_extreme_left + self.board_border + i * self.paint_size_x,
                                             self.board_extreme_top + self.board_border + (j + 1) * self.paint_size_y),
                                            (self.board_extreme_left + self.board_border + (i + 1) * self.paint_size_x,
                                             self.board_extreme_top + self.board_border + (j + 1) * self.paint_size_y),
                                            (self.board_extreme_left + self.board_border + (i + 1) * self.paint_size_x,
                                             self.board_extreme_top + self.board_border + j * self.paint_size_y)
                                        ])
            except:
                pass


if __name__ == "__main__":
    Game()

