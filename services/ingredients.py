import logging
import time

from bleach.sanitizer import Cleaner
from fastapi import status
from google import genai
from google.genai.types import GenerateContentResponse

from db.ingredients_repository import IngredientsRepository
from schemas.ingredients import IngredientsRequest
from utils.config import SETTINGS
from utils.constants import (
    MEAL_TYPES,
    POSITION_MAP,
)
from utils.error_codes import ErrorCode

logger = logging.getLogger(__name__)


class IngredientService:
    """
    Service for processing and managing ingredient-related operations.

    Responsibilities:
        - Extract and categorize ingredients from recipes using Gemini API.
        - Distribute recipes across weekly meal plan with day-pairing logic.
        - Sanitize and parse recipe input for safe processing.
        - Format business logic and API responses for /ingredients route.

    Methods:
        _get_position(day_name, meal_type): Return position index for day/meal.
        _extract_human_readable_response(model_response): Clean Gemini API response.
        _parse_input_to_list(input_text): Parse input text into recipe dicts.
        _create_ingredient_prompt(ingredients_text, have_at_home): Build Gemini prompt.
        _add_meals_with_day_pairing(parsed_data): Distribute recipes in meal plan.
        _initialize_llm_client(): Initialize Gemini API client.
        _initialize_html_cleaner(): Initialize HTML cleaner for LLM responses.
        _clean_input_texts(recipes_text, have_at_home): Clear and normalize input texts.
        _generate_shopping_list(ingredients): Create a shopping list from extracted ingredients.
        process_recipes(recipes_text, have_at_home): Extract and categorize ingredients.
        handle_ingredients_request(ingredients_request): Format response for /ingredients.
    """

    def __init__(self, ingredients_repository: IngredientsRepository | None = None):
        self.ingredients_repository = ingredients_repository or IngredientsRepository()

    def _get_position(self, day_name: str, meal_type: str) -> int:
        """
        Return the position index for a given day and meal type.

        Args:
            day_name (str): Name of the day (e.g., "Monday").
            meal_type (str): Type of meal ("Lunch" or "Dinner").

        Returns:
            int: Position index (0-13).
        """
        # Reverse mapping: (day_name, meal_type) -> position
        day_meal_to_position = {
            (day, meal): position for position, (day, meal) in POSITION_MAP.items()
        }
        if meal_type not in MEAL_TYPES:
            valid_meals = ", ".join(MEAL_TYPES)
            raise ValueError(
                f"Invalid meal type '{meal_type}'. Must be one of: {valid_meals}"
            )

        key = (day_name, meal_type)
        if key not in day_meal_to_position:
            raise ValueError(f"Invalid day/meal combination: {day_name} {meal_type}")

        return day_meal_to_position[key]

    def _extract_human_readable_response(
        self,
        model_response: GenerateContentResponse,
    ) -> str:
        """
        Extract and clean the response content from the Gemini API.

        Args:
            model_response (GenerateContentResponse): Gemini API response object.

        Returns:
            str: Cleaned content or error message.
        """
        try:
            if (
                not model_response.candidates
                or not model_response.candidates[0].content
                or not model_response.candidates[0].content.parts
                or not model_response.candidates[0].content.parts[0].text
            ):
                return "No content found in the response."

            # Clean the response by removing code block delimiters
            cleaned_content = (
                model_response.candidates[0]
                .content.parts[0]
                .text.replace("```", "")
                .replace("'''", "")
                .strip()
            )
            return cleaned_content
        except (IndexError, AttributeError, TypeError):
            return "An error occurred while processing the response."

    def _parse_input_to_list(self, input_text: str) -> list[dict[str, str]]:
        """
        Parse the input text into a list of recipe dictionaries.

        Args:
            input_text (str): Raw input text from frontend.

        Returns:
            list[dict[str, str]]: List of dicts with 'url' and 'ingredients'.
        """
        # Split the input into sections based on "# URL"
        sections = input_text.split("\n# ")

        parsed_data = []
        for section in sections:
            if not section.strip():
                continue

            # Split the section into lines
            lines = section.strip().split("\n")

            # The first line is the URL (remove the leading "# " if present)
            url = lines[0].strip().lstrip("# ").strip()

            # The rest are ingredients, starting with "##" - only include lines that start
            # with "##"
            ingredients = "\n".join(
                line.strip().replace("## ", "")
                for line in lines[1:]
                if line.strip() and line.strip().startswith("## ")
            )

            # Only append if we have both URL and ingredients
            if url and ingredients:
                parsed_data.append({"url": url, "ingredients": ingredients})

        return parsed_data

    def _create_ingredient_prompt(
        self, ingredients_text: str, have_at_home: str | None = None
    ) -> str:
        """
        Build an optimized prompt for Gemini ingredient extraction.

        Args:
            ingredients_text (str): Structured ingredients text.
            have_at_home (str | None): Items user already has.

        Returns:
            str: Prompt for Gemini API.
        """
        have_at_home_section = f"\n\nSKIP: {have_at_home}" if have_at_home else ""

        return f"""Create a shopping list. AGGREGATE identical ingredients by adding quantities, then categorize into: Meat/Fish, Veggies, Dairy, Other. Use Swedish names.

            AGGREGATION RULES:
            - Match core ingredient names (ignore variations like "färsk", "fast", percentages)
            - Add ALL quantities: 2dl + 1dl + 1dl = 4dl
            - Convert units smartly: 1000g = 1kg, 500ml = 5dl
            - Group similar items: combine cheeses, herbs, etc.
            - NEVER list same ingredient twice

            EXCLUDE pantry basics: spices, oils, condiments, water, vinegar, seasonings

            Format exactly like this:
            <div><h3>Meat/Fish</h3><ul><li>500g kött</li></ul><h3>Veggies</h3><ul><li>1800g potatis</li></ul><h3>Dairy</h3><ul><li>5dl gräddfil</li></ul><h3>Other</h3><ul><li>pasta</li></ul></div>

            INGREDIENTS:
            {ingredients_text}{have_at_home_section}"""

    def _add_meals_with_day_pairing(self, parsed_data: list[dict[str, str]]) -> None:
        """
        Distribute recipes across weekly meal plan using day-pairing logic.

        Args:
            parsed_data (list[dict[str, str]]): List of recipe dicts.
        """
        # Defines day pairs for distributing recipes across the weekly meal plan.
        # Used to assign up to 8 recipes across 14 meal slots.
        day_pairs = [
            ("Monday", "Tuesday"),  # Pair 1: Mon-Tue
            ("Wednesday", "Thursday"),  # Pair 2: Wed-Thu
            ("Friday", "Saturday"),  # Pair 3: Fri-Sat
            ("Sunday", "Sunday"),  # Pair 4: Sunday only
        ]
        for index, item in enumerate(parsed_data):
            pair_index = index // 2
            meal_index = index % 2
            if pair_index >= len(day_pairs):
                pair_index %= len(day_pairs)
            day_pair = day_pairs[pair_index]
            meal_type = MEAL_TYPES[meal_index]
            for day_name in day_pair:
                position = self._get_position(day_name, meal_type)
                self.ingredients_repository.insert_weekly_meal(
                    item["url"], position, day_name, meal_type
                )
                if day_name == "Sunday":
                    break

    def _initialize_llm_client(self) -> genai.Client:
        """Initialize Gemini API client with settings."""
        return genai.Client(api_key=SETTINGS.gemini_api_key)

    def _initialize_html_cleaner(self) -> Cleaner:
        """Initialize HTML cleaner for sanitizing LLM responses."""
        return Cleaner(tags=["div", "h3", "ul", "li", "span", "button"], strip=True)

    def _clean_input_texts(self, recipes_text: str, have_at_home: str | None) -> dict:
        """Clean and normalize input texts.
        Args:
            recipes_text (str): The recipes input text.
            have_at_home (str | None): Items user already has.

        Returns:
            dict: The cleaned and normalized input texts.
        """
        cleaned_recipes = "\n".join(
            line.strip() for line in recipes_text.splitlines() if line.strip()
        )
        cleaned_have_at_home = (
            "\n".join(
                line.strip() for line in have_at_home.splitlines() if line.strip()
            )
            if have_at_home is not None
            else ""
        )
        return {"recipes": cleaned_recipes, "have_at_home": cleaned_have_at_home}

    async def _generate_shopping_list(
        self, client: genai.Client, parsed_recipes: list[dict], have_at_home: str
    ) -> dict:
        """Generate shopping list using Gemini API.
        Args:
            client (genai.Client): The Gemini API client.
            parsed_recipes (list[dict]): The parsed recipe data.
            have_at_home (str): The user's available ingredients.
        Returns:
            dict: The generated shopping list.
        """
        # 1. Extract ingredients from all recipes
        ingredients_text = "\n\n".join(item["ingredients"] for item in parsed_recipes)

        # 2. Create optimized prompt
        prompt = self._create_ingredient_prompt(ingredients_text, have_at_home)

        # 3. Call LLM with timing
        llm_start_time = time.time()
        model_response = await client.aio.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={"temperature": 0.2},
        )
        llm_duration = time.time() - llm_start_time

        # 4. Extract response content
        content = self._extract_human_readable_response(model_response)

        return {"content": content, "duration": llm_duration}

    async def process_recipes(
        self, recipes_text: str, have_at_home: str | None
    ) -> dict:
        """
        Extract and categorize ingredients from recipes text using Gemini API.

        Args:
            recipes_text (str): Recipes input text.
            have_at_home (str | None): Items user already has.

        Returns:
            dict: Envelope with status and data or error.
        """
        try:
            # Step 1: Initialize dependencies
            client = self._initialize_llm_client()
            cleaner = self._initialize_html_cleaner()

            # Step 2: Clear existing data and prepare inputs
            self.ingredients_repository.delete_all_weekly()
            cleaned_inputs = self._clean_input_texts(recipes_text, have_at_home)

            # Step 3: Parse and store recipe data
            parsed_recipes = self._parse_input_to_list(cleaned_inputs["recipes"])
            self._add_meals_with_day_pairing(parsed_recipes)

            # Step 4: Generate shopping list via LLM
            llm_response = await self._generate_shopping_list(
                client, parsed_recipes, cleaned_inputs["have_at_home"]
            )

            # Step 5: Clean and return response
            cleaned_html = cleaner.clean(llm_response["content"])

            return {
                "status": "success",
                "data": {
                    "ingredients_content": cleaned_html,
                    "llm_time": llm_response["duration"],
                },
            }

        except Exception as exc:
            logging.exception("Failed to process recipes: %s", exc)
            return {
                "status": "error",
                "error": {
                    "code": ErrorCode.Ingredients.PROCESSING_ERROR,
                    "message": "An error occurred while processing the recipes. Please try again.",
                    "details": {"error_type": type(exc).__name__},
                },
            }

    async def handle_ingredients_request(
        self, ingredients_request: IngredientsRequest
    ) -> tuple[dict, int]:
        """
        Format business logic and response for /ingredients API route.

        Args:
            ingredients_request (IngredientsRequest): Request body.

        Returns:
            tuple[dict, int]: Envelope with status and HTTP status code.
        """
        result = await self.process_recipes(
            ingredients_request.recipes_text,
            ingredients_request.have_at_home,
        )

        # TODO: WTH is this?
        if result.get("status") == "error":
            error_code = result.get("error", {}).get("code", "")
            if error_code == ErrorCode.Ingredients.DB_ERROR:
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            status_code = status.HTTP_200_OK

        return result, status_code
