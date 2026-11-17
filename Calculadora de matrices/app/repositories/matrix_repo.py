class MatrixRepository:
    def __init__(self):
        self.db = {}
        self.counter = 1

    def crear(self, data: dict) -> dict:
        matrix = {"id": self.counter, "nombre": data.get("nombre"), "datos": data["datos"]}
        self.db[self.counter] = matrix
        self.counter += 1
        return matrix

    def listar(self) -> list:
        return list(self.db.values())

    def obtener(self, id: int) -> dict:
        return self.db.get(id)

    def actualizar(self, id: int, data: dict) -> dict:
        if id in self.db:
            self.db[id]["datos"] = data["datos"]
            return self.db[id]
        return None

    def eliminar(self, id: int) -> bool:
        if id in self.db:
            del self.db[id]
            return True
        return False


# Instancia global (singleton para esta prueba en memoria)
matrix_db = MatrixRepository()


class FiguraMorphRepository:
    def __init__(self):
        self.figuras = {}
        self.counter = 1

    def guardar(self, data: dict) -> dict:
        nombre = data["nombre"].strip()
        for fig in self.figuras.values():
            if fig["nombre"] == nombre:
                fig["t"] = data["t"]
                fig["resolucion"] = data["resolucion"]
                return fig

        nueva = {
            "id": self.counter,
            "nombre": nombre,
            "t": data["t"],
            "resolucion": data["resolucion"],
        }
        self.figuras[self.counter] = nueva
        self.counter += 1
        return nueva

    def listar(self) -> list:
        return list(self.figuras.values())

    def obtener(self, id: int) -> dict:
        return self.figuras.get(id)

    def eliminar(self, id: int) -> bool:
        if id in self.figuras:
            del self.figuras[id]
            return True
        return False


figura_db = FiguraMorphRepository()
