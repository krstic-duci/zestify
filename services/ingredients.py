from google import genai
from google.genai.types import GenerateContentResponse
from bleach.sanitizer import Cleaner

from utils.constants import LLM_MODEL
from utils.config import settings


client = genai.Client(api_key=settings.gemini_api_key)
cleaner = Cleaner(tags=settings.allowed_tags, strip=True)


def extract_human_readable_response(
    model_response: GenerateContentResponse,
) -> str:
    """
    Extracts and cleans the response content from the Gemini API.

    This function processes the response from the Gemini API, extracting the
    relevant content from the first candidate's content parts. It also removes
    any Markdown-style code block delimiters (e.g., ```html and ```) if present.

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
            return "No content found in the response."

        content = model_response.candidates[0].content.parts[0].text
        if not content:
            return "No content found in the response."

        if content.startswith("```html"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        return content
    except (IndexError, AttributeError, TypeError):
        return "An error occurred while processing the response."


def create_ingredient_prompt(recipes_text: str) -> str:
    """Create prompt for ingredient extraction"""
    return f"""
    Extract and aggregate ingredients from the recipes below. Translate to Swedish if
    needed. Use metric system only. Group by: Meat/Fish, Vegetables/Fruits, Dairy,
    Grains, Spices/Herbs, and Other.

    Format:
    <div>
    <h3>Meat/Fish</h3>
    <ul><li>500 g Sej</li></ul>
    <h3>Vegetables/Fruits</h3>
    <ul><li>2 st Lime</li></ul>
    <h3>Pantry Items</h3>
    <ul><li>100 g Majonnäs</li></ul>
    </div>

    Recipes:
    {recipes_text}
    """


class IngredientService:
    _client = client
    _cleaner = cleaner

    def process_recipes(self, recipes_text: str) -> str:
        """
        Process recipes and return sanitized HTML
        This method takes the recipes text input, creates a prompt for the Gemini API,
        and returns a cleaned and categorized list of ingredients.

        Args:
            recipes_text: The raw recipes text to process

        Returns:
            str: Sanitized HTML containing categorized ingredients
        """

        model_response: GenerateContentResponse = self._client.models.generate_content(
            model=LLM_MODEL, contents=create_ingredient_prompt(recipes_text)
        )

        raw_response = extract_human_readable_response(model_response)
        return self._cleaner.clean(raw_response)
