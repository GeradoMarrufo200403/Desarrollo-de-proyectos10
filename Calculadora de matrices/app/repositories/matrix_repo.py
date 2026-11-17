from app.models.models import MatrixCreate

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
