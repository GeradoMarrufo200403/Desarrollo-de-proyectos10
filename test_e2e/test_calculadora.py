from playwright.sync_api import Page, expect


def test_flujo_completo_calculadora(page: Page, calculadora_url: str) -> None:
    """Prueba el flujo completo: crear matrices 2x2, sumar, multiplicar, determinante y transpuesta."""
    # 1. Navegar a la Calculadora
    page.goto(calculadora_url)
    expect(page).to_have_title("Gestor de Matrices - Estilo Excel")

    # Contar opciones existentes al iniciar
    sum_m1 = page.locator("#sum-m1")
    initial_count = sum_m1.locator("option").count()

    # 2. Configurar y Guardar primera Matriz (2x2)
    page.locator("#rows").fill("2")
    page.locator("#cols").fill("2")
    page.get_by_role("button", name="Configurar").click()

    inputs_m1 = page.locator("#matrix-inputs input")
    expect(inputs_m1).to_have_count(4)
    inputs_m1.nth(0).fill("5")
    inputs_m1.nth(1).fill("6")
    inputs_m1.nth(2).fill("5")
    inputs_m1.nth(3).fill("1")
    page.get_by_role("button", name="Guardar Matriz").click()
    expect(sum_m1.locator("option")).to_have_count(initial_count + 1)

    # 3. Configurar y Guardar segunda Matriz (2x2)
    page.locator("#rows").fill("2")
    page.locator("#cols").fill("2")
    page.get_by_role("button", name="Configurar").click()

    inputs_m2 = page.locator("#matrix-inputs input")
    expect(inputs_m2).to_have_count(4)
    inputs_m2.nth(0).fill("1")
    inputs_m2.nth(1).fill("2")
    inputs_m2.nth(2).fill("3")
    inputs_m2.nth(3).fill("4")
    page.get_by_role("button", name="Guardar Matriz").click()
    expect(sum_m1.locator("option")).to_have_count(initial_count + 2)

    # 4. Refrescar lista de matrices guardadas
    page.get_by_role("button", name="Refrescar Lista").click()
    expect(page.locator(".matrix-display").first).to_be_visible()

    # 5. Probar Operación: Sumar Matrices
    sum_m2 = page.locator("#sum-m2")
    sum_m1.select_option(index=initial_count)
    sum_m2.select_option(index=initial_count + 1)
    page.get_by_role("button", name="Sumar").click()

    sum_result = page.locator("#sum-result")
    expect(sum_result).to_be_visible()
    expect(sum_result).to_contain_text("+")

    # 6. Probar Operación: Multiplicar Matrices
    mul_m1 = page.locator("#mul-m1")
    mul_m2 = page.locator("#mul-m2")
    mul_m1.select_option(index=initial_count)
    mul_m2.select_option(index=initial_count + 1)
    page.get_by_role("button", name="Multiplicar").click()

    mul_result = page.locator("#mul-result")
    expect(mul_result).to_be_visible()
    expect(mul_result).to_contain_text("×")

    # 7. Probar Operación: Calcular Determinante y Transpuesta
    unit_m = page.locator("#unit-m")
    unit_m.select_option(index=initial_count)

    # Determinante |A|
    page.get_by_role("button", name="Calcular |A|").click()
    det_result = page.locator("#det-result")
    expect(det_result).to_be_visible()
    expect(det_result).to_contain_text("det(")

    # Transpuesta A^T
    page.get_by_role("button", name="Ver Transpuesta").click()
    trans_result = page.locator("#trans-result")
    expect(trans_result).to_be_visible()
    expect(trans_result).to_contain_text("^T =")


def test_validacion_dimensiones_incompatibles_suma(page: Page, calculadora_url: str) -> None:
    """Verifica que el sistema rechace sumar matrices de dimensiones diferentes (2x2 con 2x3)."""
    page.goto(calculadora_url)

    # Contar opciones iniciales
    sum_m1 = page.locator("#sum-m1")
    initial_count = sum_m1.locator("option").count()

    # 1. Crear matriz 2x2
    page.locator("#rows").fill("2")
    page.locator("#cols").fill("2")
    page.get_by_role("button", name="Configurar").click()
    inputs_2x2 = page.locator("#matrix-inputs input")
    for i in range(4):
        inputs_2x2.nth(i).fill("2")
    page.get_by_role("button", name="Guardar Matriz").click()
    expect(sum_m1.locator("option")).to_have_count(initial_count + 1)

    # 2. Crear matriz 2x3
    page.locator("#rows").fill("2")
    page.locator("#cols").fill("3")
    page.get_by_role("button", name="Configurar").click()
    inputs_2x3 = page.locator("#matrix-inputs input")
    for i in range(6):
        inputs_2x3.nth(i).fill("3")
    page.get_by_role("button", name="Guardar Matriz").click()
    expect(sum_m1.locator("option")).to_have_count(initial_count + 2)

    # 3. Seleccionar la 2x2 y la 2x3 para sumar
    sum_m2 = page.locator("#sum-m2")
    sum_m1.select_option(index=initial_count)      # Matriz 2x2
    sum_m2.select_option(index=initial_count + 1)  # Matriz 2x3

    page.get_by_role("button", name="Sumar").click()

    # 4. Validar mensaje de error de dimensiones incompatibles
    sum_result = page.locator("#sum-result")
    expect(sum_result).to_be_visible()
    expect(sum_result).to_contain_text("Error: Dimensiones incompatibles")
