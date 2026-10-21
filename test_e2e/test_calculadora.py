from playwright.sync_api import Page, expect

BTN_GUARDAR = "💾 Guardar Matriz en Backend"
BTN_SUMA = "➕ Calcular Suma"
BTN_ALEATORIOS = "🎲 Aleatorios"
BTN_DETERMINANTE_TAB = "🎯 Determinante |A|"
BTN_DETERMINANTE = "🎯 Calcular Determinante"


def celdas(page: Page):
    return page.get_by_role("spinbutton", name="0")


def llenar_matriz(page: Page, valores: list[str]) -> None:
    """Llena las celdas de la matriz (en orden) con los valores dados."""
    for i, valor in enumerate(valores):
        celdas(page).nth(i).fill(valor)


def guardar_matriz(page: Page) -> None:
    page.get_by_role("button", name=BTN_GUARDAR).click()


def test_carga_pagina(page: Page, calculadora_url: str) -> None:
    page.goto(calculadora_url)
    expect(page.get_by_role("button", name=BTN_GUARDAR)).to_be_visible()
    expect(celdas(page).first).to_be_visible()


def test_llenar_matriz_con_valores(page: Page, calculadora_url: str) -> None:
    page.goto(calculadora_url)
    llenar_matriz(page, ["-1", "3", "2", "3"])
    expect(celdas(page).nth(0)).to_have_value("-1")
    expect(celdas(page).nth(1)).to_have_value("3")
    expect(celdas(page).nth(2)).to_have_value("2")
    expect(celdas(page).nth(3)).to_have_value("3")


def test_guardar_dos_matrices(page: Page, calculadora_url: str) -> None:
    page.goto(calculadora_url)
    llenar_matriz(page, ["-1", "3", "2", "3"])
    guardar_matriz(page)
    llenar_matriz(page, ["-3", "4", "3", "4"])
    guardar_matriz(page)


def test_suma_de_matrices_guardadas(page: Page, calculadora_url: str) -> None:
    page.goto(calculadora_url)
    llenar_matriz(page, ["-1", "3", "2", "3"])
    guardar_matriz(page)
    llenar_matriz(page, ["-3", "4", "3", "4"])
    guardar_matriz(page)

    page.get_by_label("Matriz 1 (A)").select_option("1")
    page.get_by_label("Matriz 2 (B)").select_option("2")
    page.get_by_role("button", name=BTN_SUMA).click()


def test_matrices_aleatorias_y_suma(page: Page, calculadora_url: str) -> None:
    page.goto(calculadora_url)
    # Agrandar la matriz y generar valores aleatorios, dos veces
    for indice in (0, 1):
        page.get_by_role("button", name="+").nth(indice).click()
        page.get_by_role("button", name=BTN_ALEATORIOS).click()
        guardar_matriz(page)

    page.get_by_label("Matriz 1 (A)").select_option("3")
    page.get_by_label("Matriz 2 (B)").select_option("4")
    page.get_by_role("button", name=BTN_SUMA).click()


def test_determinante(page: Page, calculadora_url: str) -> None:
    page.goto(calculadora_url)
    llenar_matriz(page, ["-1", "3", "2", "3"])
    guardar_matriz(page)

    page.get_by_role("button", name=BTN_DETERMINANTE_TAB).click()
    page.get_by_label("Matriz Cuadrada (A)").select_option("2")
    page.get_by_role("button", name=BTN_DETERMINANTE).click()
