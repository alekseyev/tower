from backend.babble.lemmas import lemmatize


def test_lemmatize():
    assert lemmatize("es", "¡Hola, amigo!") == ["hola", "amigo"]
    assert lemmatize("es", "Sí, puedo hacerlo.") == ["sí", "poder", "hacer", "él"]
    assert lemmatize("es", "Señorita Parker") == ["señorita", "Parker"]
    assert lemmatize("es", "¿Tú vas a ir bien?") == ["tú", "ir", "a", "ir", "bien"]

    assert lemmatize("en", "Yes, I am going.") == ["yes", "I", "be", "go"]
