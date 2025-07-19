import random

import flet as ft
from loguru import logger

from flet_ui.client import NotAuthenticated
from flet_ui.pages.const import COURSE, LANG
from flet_ui.pages.root import ROOT_VIEW_INSTANCE


class PracticeView(ft.Column):
    def __init__(self, learn_new_words: bool = False):
        super().__init__(expand=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        self.learn_new_words = learn_new_words
        self.current_exercise = -1
        self.results = {}
        self.top_message = ft.Markdown("Loading...")
        self.word_bank_buttons = ft.Row(spacing=10, wrap=True)
        self.result_buttons = ft.Row(spacing=10, wrap=True)
        self.result_row = ft.Row(
            [
                ft.Container(
                    content=self.result_buttons,
                    height=100,
                    border=ft.border.all(1, ft.colors.GREEN_300),
                    border_radius=10,
                    expand=True,
                )
            ],
        )
        self.result_text = ft.Text("")
        self.action_button = ft.FilledButton("Check", on_click=self.check)
        self.dictionary_button = ft.OutlinedButton("Dictionary", on_click=self.trigger_dictionary)
        self.dictionary = ft.Markdown("")
        self.button_home = ft.FilledButton("Return home", on_click=self.go_home)

        self.controls = [
            self.top_message,
            ft.Container(content=self.word_bank_buttons, height=100),
            self.result_row,
            self.result_text,
            ft.Row(
                [
                    self.action_button,
                    self.dictionary_button,
                ]
            ),
            ft.Container(expand=True, content=ft.Column([self.dictionary], scroll=ft.ScrollMode.AUTO, expand=True)),
            ft.Divider(),
            self.button_home,
        ]

    def init_controls(self):
        self.top_message.value = "Loading..."
        self.word_bank_buttons.controls = []
        self.result_buttons.controls = []
        self.result_row.visible = False
        self.action_button.visible = False
        self.result_text.value = ""
        self.action_button.text = "Check"
        self.action_button.on_click = self.check
        self.action_button.visible = False
        self.dictionary_button.visible = False
        self.dictionary.visible = False
        self.update()

    def did_mount(self):
        logger.info("did mount")
        self.init_controls()
        self.page.run_task(self.load_data)

    async def load_data(self):
        try:
            data = await self.page.client.me()
        except NotAuthenticated:
            self.page.go("/login")
            return
        self.user_id = data["id"]
        self.page.state.user_id = self.user_id
        if self.learn_new_words:
            logger.info("Loading exercises with new words...")
            self.exercises = await self.page.client.get_exercises_new_words(self.user_id, LANG, COURSE)
        else:
            logger.info("Loading practice exercises...")
            self.exercises = await self.page.client.get_exercises(self.user_id, LANG)
        self.current_exercise = -1
        self.results = {}
        self.next_exercise()

    def next_exercise(self, *args, **kwargs):
        self.init_controls()
        self.current_exercise += 1
        exercise = self.exercises[self.current_exercise]
        words = exercise["sentence"]["text"]["es"].split()
        random.shuffle(words)
        new_word_bit = ""
        if new_word := exercise["new_word"]:
            translations = exercise["dictionary"].get(new_word, ["translation not found"])
            new_word_bit = f"New word: **{new_word}** - {', '.join(translations)}.  \n"
        self.top_message.value = (
            f"[{self.current_exercise + 1}/{len(self.exercises)}] {new_word_bit}Translate to Spanish:  \n"
            f"**{exercise["sentence"]['text']['en']}**"
        )
        self.dictionary.value = "\n\n".join(
            [f"**{word}** - {', '.join(translations)}" for word, translations in exercise["dictionary"].items()]
        )
        self.dictionary.visible = False
        self.word_bank_buttons.controls = []
        for word in words:
            button = ft.ElevatedButton(word)
            button.on_click = self.get_handler_on_word_bank_button_click(button)
            self.word_bank_buttons.controls.append(button)
        self.result_row.visible = True
        self.result_buttons.controls = []
        self.action_button.visible = True
        self.dictionary_button.visible = True
        self.update()

    def go_home(self, *args, **kwargs):
        self.page.go("/")
        self.page.run_task(ROOT_VIEW_INSTANCE.load_data)

    def get_handler_on_word_bank_button_click(self, button: ft.ElevatedButton):
        def on_word_bank_click(*args, **kwargs):
            button.opacity = 0
            button.disabled = True
            result_button = ft.ElevatedButton(button.text)
            result_button.on_click = self.get_handler_on_result_button_click(result_button, button)
            self.result_buttons.controls.append(result_button)
            self.update()

        return on_word_bank_click

    def get_handler_on_result_button_click(self, button: ft.ElevatedButton, word_bank_button: ft.ElevatedButton):
        def on_result_bank_click(*args, **kwargs):
            self.result_buttons.controls.remove(button)
            word_bank_button.opacity = 1
            word_bank_button.disabled = False
            self.update()

        return on_result_bank_click

    def trigger_dictionary(self, *args, **kwargs):
        self.dictionary.visible = not self.dictionary.visible
        self.update()

    def check(self, *args, **kwargs):
        result_text = " ".join(button.text for button in self.result_buttons.controls)
        exercise = self.exercises[self.current_exercise]
        correct_text = exercise["sentence"]["text"]["es"]
        correct = result_text == correct_text
        if correct:
            self.result_text.color = ft.colors.GREEN
            self.result_text.value = "Correct!"
        else:
            self.result_text.color = ft.colors.RED
            self.result_text.value = f"Incorrect! Translation: {correct_text}"
        self.results[exercise["sentence"]["id"]] = correct
        if len(self.results) < len(self.exercises):
            self.action_button.text = "Next"
            self.action_button.on_click = self.next_exercise
        else:
            self.action_button.text = "Finish"
            self.action_button.on_click = self.submit_result
        self.update()

    async def submit_result(self, *args, **kwargs):
        self.init_controls()
        await self.page.client.save_exercise_result(self.user_id, LANG, self.results)
        self.go_home()


PRACTICE_VIEW = ft.View("/practice", [ft.AppBar(title=ft.Text("Exercise")), PracticeView()])
NEW_WORDS_VIEW = ft.View("/new_words", [ft.AppBar(title=ft.Text("New words")), PracticeView(learn_new_words=True)])
