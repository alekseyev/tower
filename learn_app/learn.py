from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Static

from app.app_ctx import AppCtx
from app.courses import get_courses_list
from app.data_layer.models import BabbleSentence, User, UserProgress

USER_ID = "ff2caa0f-2426-4ad4-b9fe-b1e01f0f0e2a"


user = None
course_data = None
lang = "es"
base_lang = "en"
selected_course = None
exercies_to_show: list[BabbleSentence] = []


async def init_data():
    global user
    global course_data
    user = await User.get(USER_ID)
    course_data = await UserProgress.get(USER_ID)


class StartMenu(Static):
    def compose(self) -> ComposeResult:
        yield Button("Exercise", id="exercise")
        yield Button("Learn new words", id="learn")


class CourseSelection(Static):
    def compose(self) -> ComposeResult:
        courses = get_courses_list(lang)
        for course in courses:
            yield Button(course, id=f"course_{course}")
        yield Button("Back", id="start")


class NewWordsScreen(Static):
    def compose(self) -> ComposeResult:
        global course_data
        global selected_course
        new_words = course_data.get_new_words(lang, selected_course)
        course_data.languages[lang].add_new_words(new_words)
        yield Static(f"New words: {', '.join(new_words)}")
        yield Button("Back", id="start")


class ShowSentenceScreen(Static):
    def __init__(self, text: str, translation: str):
        super().__init__()
        self.text = text
        self.translation = translation

    def compose(self) -> ComposeResult:
        yield Static(self.text)
        yield Button("Show translation", id="show_translation")

    def show_translation(self):
        self.mount(Static(self.translation))
        self.mount(Button("Ok", id="exercise_ok"))
        self.mount(Button("Mistake", id="exercise_mistake"))


class MainScreenContainer(Static):
    def __init__(self, widget: Widget):
        super().__init__()
        self.widget = widget

    def compose(self) -> ComposeResult:
        yield self.widget


class MainScreen(Static):
    def compose(self) -> ComposeResult:
        yield MainScreenContainer(StartMenu())

    def show_course_selection(self):
        self.query_one(MainScreenContainer).remove()
        self.mount(MainScreenContainer(CourseSelection()))

    def show_new_words(self, course: str):
        global selected_course
        selected_course = course
        self.query_one(MainScreenContainer).remove()
        self.mount(MainScreenContainer(NewWordsScreen()))

    async def start_exercises(self):
        global exercies_to_show
        global course_data
        exercies_to_show = await course_data.get_sentences(lang)
        await self.show_next_exercise()

    async def show_next_exercise(self):
        global exercies_to_show
        if not exercies_to_show:
            await self.return_home()
            return
        self.query_one(MainScreenContainer).remove()
        exercise = exercies_to_show[-1]
        self.mount(
            MainScreenContainer(ShowSentenceScreen(text=exercise.text[lang], translation=exercise.text[base_lang]))
        )

    def save_exercise(self, correct: bool = True):
        global exercies_to_show
        global course_data
        exercise = exercies_to_show.pop()
        course_data.languages[lang].add_exercise(id=exercise.id, words=exercise.lemmas[lang], correct=correct)

    async def return_home(self):
        global course_data
        self.query_one(MainScreenContainer).remove()
        self.mount(MainScreenContainer(StartMenu()))
        await course_data.save()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "start":
            await self.return_home()
        elif button_id == "learn":
            self.show_course_selection()
        elif button_id.startswith("course_"):
            selected_course = button_id.split("course_")[1]
            self.show_new_words(selected_course)
        elif button_id == "exercise":
            await self.start_exercises()
        elif button_id == "show_translation":
            self.query_one(ShowSentenceScreen).show_translation()
        elif button_id == "exercise_ok":
            self.save_exercise()
            await self.show_next_exercise()
        elif button_id == "exercise_mistake":
            self.save_exercise(False)
            await self.show_next_exercise()


class LearnApp(App):
    """Babble babble babble"""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("q", "exit", "Exit")]

    async def on_mount(self) -> None:
        await AppCtx.start()
        await init_data()
        from app.babble import nlp

        self.log(f"{len(nlp)} nlp models available")

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield MainScreen()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_exit(self) -> None:
        self.exit()


if __name__ == "__main__":
    app = LearnApp()
    app.run()
