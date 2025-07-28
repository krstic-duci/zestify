import time
from typing import ClassVar

from bleach.sanitizer import Cleaner
from google import genai
from google.genai.types import GenerateContentResponse

from db.conn import supabase
from utils.config import SETTINGS
from utils.constants import LLM_MODEL

# from utils.position_mapping import get_day_and_meal, normalize_position


class RecipeProcessingError(Exception):
    """Custom exception for recipe processing errors."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


CLIENT = genai.Client(api_key=SETTINGS.gemini_api_key)
CLEANER = Cleaner(tags=SETTINGS.allowed_tags, strip=True)
DAY_PAIRS = [
    ("Monday", "Tuesday"),  # Pair 1: Mon-Tue (recipes 1-2)
    ("Wednesday", "Thursday"),  # Pair 2: Wed-Thu (recipes 3-4)
    ("Friday", "Saturday"),  # Pair 3: Fri-Sat (recipes 5-6)
    ("Sunday", "Sunday"),  # Pair 4: Sunday only (recipes 7-8)
]
MEALS = ["Lunch", "Dinner"]


class IngredientService:
    """A service class for processing and managing ingredient-related operations.

    Methods
    -------
    process_recipes(
        recipes_text: str,
        have_at_home: str | None = None
    ) -> dict[str, str | float]
        Processes the recipes text and returns sanitized HTML with categorized
        ingredients.

    """

    _client = CLIENT
    _cleaner = CLEANER
    _day_to_position: ClassVar[dict[str, int]] = {
        "Monday": 0,
        "Tuesday": 2,
        "Wednesday": 4,
        "Thursday": 6,
        "Friday": 8,
        "Saturday": 10,
        "Sunday": 12,
    }

    def _extract_human_readable_response(
        self,
        model_response: GenerateContentResponse,
    ) -> str:
        """Extract and clean the response content from the Gemini API.

        This function processes the response from the Gemini API, extracting the
        relevant content from the first candidate's content parts. It also removes
        any Markdown-style code block delimiters (e.g., ```html, ```, ''') if present.

        Args:
            model_response: The response object returned by the Gemini API, which
                            contains a list of candidates with content.

        Returns:
            str: The cleaned content extracted from the response, or an error
                 message if the extraction fails.

        """
        try:
            if (
                not model_response.candidates
                or not model_response.candidates[0].content
                or not model_response.candidates[0].content.parts
            ):
                return "No content found in the response (first try)."

            content = model_response.candidates[0].content.parts[0].text
            if not content:
                return "No content found in the response."

            # Remove opening code block markers
            if content.startswith("```html"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]

            # Remove closing code block markers from the end
            if content.endswith("```"):
                content = content[:-3]

            # Remove any remaining triple backticks or single quotes that might appear
            # in the middle of the content (common LLM artifact)
            content = content.replace("```", "").replace("'''", "")

            content = content.strip()

            return content
        except (IndexError, AttributeError, TypeError):
            return "An error occurred while processing the response."

    def _parse_input_to_list(self, input_text: str) -> list[dict[str, str]]:
        """Parse the input text into a list of dictionaries with 'url' and 'ingredients' keys.

        Args:
            input_text (str): The raw input text from the frontend.

        Returns:
            list[dict[str, str]]: A list of dictionaries with 'url' and 'ingredients' keys.

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
        """Create an optimized prompt for ingredient extraction using only ingredients.

        Args:
            ingredients_text (str): The cleaned and structured ingredients text.
            have_at_home (str | None): Optional string of items the user already has at
            home.

        Returns:
            str: The optimized prompt for the Gemini API.

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
        """Add meals to the weekly table using day-pairing logic for initial setup.

        This method distributes recipes across a weekly meal plan using a specific
        pairing strategy where certain days share the same recipes. The system
        handles up to 8 recipes, covering all 14 meal slots (7 days x 2 meals).

        Day Pairing Strategy:
            - Monday/Tuesday: Share recipes 1-2 (Lunch/Dinner)
            - Wednesday/Thursday: Share recipes 3-4 (Lunch/Dinner)
            - Friday/Saturday: Share recipes 5-6 (Lunch/Dinner)
            - Sunday: Uses recipes 7-8 (Lunch/Dinner) independently

        Position Mapping:
            Each day/meal combination maps to a specific position:
            - Monday: 0 (Lunch), 1 (Dinner)
            - Tuesday: 2 (Lunch), 3 (Dinner)
            - ... and so on through Sunday: 12 (Lunch), 13 (Dinner)

        Args:
            parsed_data: List of dictionaries containing recipe data. Each dict
                        must have 'url' and 'ingredients' keys. Recipes are
                        processed in order, with index determining day/meal assignment.

        Raises:
            Exception: If database insert operations fail.

        Note:
            If more than 8 recipes are provided, the method wraps around using
            modulo arithmetic to reuse the day pairs.
        """
        for index, item in enumerate(parsed_data):
            pair_index = index // 2  # Which day pair (0-3)
            meal_index = index % 2  # Which meal (0=Lunch, 1=Dinner)

            if pair_index >= len(DAY_PAIRS):
                pair_index %= len(DAY_PAIRS)  # Wrap around if more than 8 recipes

            day_pair = DAY_PAIRS[pair_index]
            meal_type = MEALS[meal_index]

            # For each day in the pair, add the same recipe
            for day_name in day_pair:
                # Calculate position for this specific day/meal combination
                meal_offset = 0 if meal_type == "Lunch" else 1
                position = self._day_to_position[day_name] + meal_offset

                # Save with the calculated position
                supabase.table("weekly").insert(
                    {
                        "link": item["url"],
                        "position": position,
                        "day_name": day_name,
                        "meal_type": meal_type,
                    }
                ).execute()

                # Break for Sunday since it's not actually paired
                if day_name == "Sunday":
                    break

    def _validate_recipes_text(self, recipes_text: str) -> None:
        """Validate the recipes text input.

        Args:
            recipes_text (str): The raw recipes text to validate.

        Raises:
            ValueError: If the input is invalid.

        """
        if not recipes_text.strip():
            raise ValueError("Please provide some recipes text.")
        if len(recipes_text) < 10:
            raise ValueError("Recipes text must be at least 10 characters long.")

    async def process_recipes(
        self, recipes_text: str, have_at_home: str | None = None
    ) -> dict[str, str | float]:
        """Process recipes and return sanitized HTML.

        This method takes the recipes text input, creates a prompt for the Gemini API,
        and returns a cleaned and categorized list of ingredients.

        Args:
            recipes_text: The raw recipes text to process.
            have_at_home: Optional string of items the user already has at home,
                        used to filter out those ingredients.

        Returns:
            str: Sanitized HTML containing categorized ingredients.

        """
        self._validate_recipes_text(recipes_text)
        cleaned_recipes_text = "\n".join(
            line.strip() for line in recipes_text.splitlines() if line.strip()
        )
        parsed_data = self._parse_input_to_list(cleaned_recipes_text)

        if not parsed_data:
            raise ValueError("No valid recipes or ingredients found in the input.")

        try:
            # TODO: don't like mixing DB and LLM logic
            supabase.table("weekly").delete().gt("position", -1).execute()
            self._add_meals_with_day_pairing(parsed_data)

            ingredients_text = "\n\n".join(item["ingredients"] for item in parsed_data)
            prompt = self._create_ingredient_prompt(ingredients_text, have_at_home)

            llm_start_time = time.time()
            model_response: GenerateContentResponse = (
                await self._client.aio.models.generate_content(
                    model=LLM_MODEL,
                    contents=prompt,
                    config={"temperature": 0.2},
                )
            )
            llm_duration = time.time() - llm_start_time

            raw_response = self._extract_human_readable_response(model_response)

            return {
                "processed_data": self._cleaner.clean(raw_response),
                "llm_time": llm_duration,
            }
        except Exception as e:
            raise RecipeProcessingError(f"Error processing recipes: {e!s}", e) from e
