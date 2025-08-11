from services.ingredients import IngredientService


def get_ingredient_service() -> IngredientService:
    return IngredientService()
