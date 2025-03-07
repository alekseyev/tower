from backend.babble.babble import lemmatize


def test_lemmatize():
    assert lemmatize("es", "¡Hola, amigo!") == ["hola", "amigo"]
    assert lemmatize("es", "Sí, puedo hacerlo.") == ["sí", "poder", "hacer", "él"]
    assert lemmatize("es", "Señorita Parker") == ["señorita", "Parker"]

    assert lemmatize("en", "Yes, I am going.") == ["yes", "I", "be", "go"]
