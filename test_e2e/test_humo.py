from playwright.sync_api import Page, expect
 
VISOR = "http://localhost:8001/view"

def test_visor_se_conecta(page: Page):
    page.goto(VISOR)
    # exact=False para que coincida con "Conectado a API Transform"
    expect(page.get_by_text("Conectado", exact=False)).to_be_visible(timeout=5000)
