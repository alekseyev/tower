from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Static

from app.app_ctx import AppCtx
from app.courses import get_course_data, get_courses_list
from app.data_layer.models import BabbleSentence, User, UserProgress

USER_ID = "ff2caa0f-2426-4ad4-b9fe-b1e01f0f0e2a"


user = None
course_data = None
lang = "es"
base_lang = "en"
selected_course = None
exercies_to_show: list[BabbleSentence] = []
current_exercise: int = 0
total_exercices: int = 0


async def init_data():
    global user
    global course_data
    user = await User.get(USER_ID)
    course_data = await UserProgress.get(USER_ID)


def perc(a, b):
    return f"{a} / {b} [{a / b * 100:.3f}%]"


def get_stats_text() -> str:
    global course_data
    if course_data is None:
        return "Waiting for Data"
    data = course_data.languages[lang]
    c_data = get_course_data(lang, "casa.s01e01")
    encountered = len(data.words)
    learned = len([word for word in data.words if word in c_data])
    practiced = len([word for word in data.words if word in c_data and data.words[word].seen_times > 1])
    count = len(c_data)
    total = sum([cnt for word, cnt in c_data.items()])
    total_learned = sum([cnt for word, cnt in c_data.items() if word in data.words])

    new_words = len(data.get_new_words())
    bad_words = len(data.get_bad_words())

    return (
        f"Words encountered: {encountered}\n"
        f"Words learned from course {perc(learned, count)}\n"
        f"Words practiced {perc(practiced, learned)}\n"
        f"New words {perc(new_words, learned)}\n"
        f"Bad words {perc(bad_words, learned)}\n"
        f"Understanding {perc(total_learned, total)}\n"
        f"Total exercises: {data.total_exercises}"
    )


class StartMenu(Static):
    def compose(self) -> ComposeResult:
        yield Static(get_stats_text())
        yield Button("Reload", id="start")
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
        global current_exercise
        global total_exercices
        exercies_to_show = await course_data.get_sentences(lang)
        current_exercise = 0
        total_exercices = len(exercies_to_show)
        await self.show_next_exercise()

    async def show_next_exercise(self):
        global exercies_to_show
        global current_exercise
        global total_exercices
        if not exercies_to_show:
            await self.return_home()
            return
        self.query_one(MainScreenContainer).remove()
        exercise = exercies_to_show[-1]
        self.log("Next exercise", exercise)
        current_exercise += 1
        text = f"[b][{current_exercise}/{total_exercices}][/b]\n{exercise.text[lang]}"
        self.mount(MainScreenContainer(ShowSentenceScreen(text=text, translation=exercise.text[base_lang])))

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
