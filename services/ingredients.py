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


def create_ingredient_prompt(recipes_text: str, have_at_home: str | None = None) -> str:
    """
    Create optimized prompt for ingredient extraction with minimal text, maximum output.
    """
    have_at_home_section = (
        f"\n\nEXCLUDE (already have):\n{have_at_home}"
        if have_at_home and have_at_home.strip()
        else ""
    )

    return f"""Extract & aggregate ALL ingredients. Swedish names. Metric only.
    Categorize: Meat/Fish, Vegetables/Fruits, Dairy, Grains, Spices/Herbs, Other.
    Skip basics (salt, pepper, oil).

    Format (exact):
    <div>
        <h3>Meat/Fish</h3>
        <ul><li>500 g kött</li><li>300 g fisk</li></ul>
        <h3>Vegetables/Fruits</h3>
        <ul><li>2 st lök</li><li>400 g morötter</li></ul>
        <h3>Dairy</h3>
        <ul><li>250 ml mjölk</li></ul>
        <h3>Grains</h3>
        <ul><li>200 g ris</li></ul>
        <h3>Spices/Herbs</h3>
        <ul><li>1 tsk paprika</li></ul>
        <h3>Other</h3>
        <ul><li>100 g majonnäs</li></ul>
    </div>

    RECIPES:
    {recipes_text}{have_at_home_section}
    """


class IngredientService:
    _client = client
    _cleaner = cleaner

    def process_recipes(
        self, recipes_text: str, have_at_home: str | None = None
    ) -> str:
        """
        Process recipes and return sanitized HTML
        This method takes the recipes text input, creates a prompt for the Gemini API,
        and returns a cleaned and categorized list of ingredients.

        Args:
            recipes_text: The raw recipes text to process
            have_at_home: Optional string of items the user already has at home,
                          used to filter out those ingredients.

        Returns:
            str: Sanitized HTML containing categorized ingredients
        """

        model_response: GenerateContentResponse = self._client.models.generate_content(
            model=LLM_MODEL,
            contents=create_ingredient_prompt(recipes_text, have_at_home),
        )

        raw_response = extract_human_readable_response(model_response)
        return self._cleaner.clean(raw_response)
