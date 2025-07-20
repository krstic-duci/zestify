from google import genai
from google.genai.types import GenerateContentResponse
from bleach.sanitizer import Cleaner

from utils.constants import LLM_MODEL
from utils.config import settings


client = genai.Client(api_key=settings.gemini_api_key)
cleaner = Cleaner(tags=settings.allowed_tags, strip=True)

# day_pairs = [
#     ("Monday", "Tuesday"),      # Pair 1: Mon-Tue
#     ("Wednesday", "Thursday"),  # Pair 2: Wed-Thu
#     ("Friday", "Saturday"),     # Pair 3: Fri-Sat
#     ("Sunday", "Sunday")        # Pair 4: Sunday (single day)
# ]
# meals = ["Lunch", "Dinner"]


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


def parse_input_to_list(input_text: str) -> list[dict[str, str]]:
    """
    Parse the input text into a list of dictionaries with 'url' and 'ingredients' keys.

    Args:
        input_text (str): The raw input text from the frontend.

    Returns:
        list[dict[str, str]]: A list of dictionaries with 'url' and 'ingredients'.
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


def create_ingredient_prompt(
    ingredients_text: str, have_at_home: str | None = None
) -> str:
    """
    Create an optimized prompt for ingredient extraction using only ingredients.

    Args:
        ingredients_text (str): The cleaned and structured ingredients text.
        have_at_home (str | None): Optional string of items the user already has at
        home.

    Returns:
        str: The optimized prompt for the Gemini API.
    """
    have_at_home_section = (
        f"\n\nEXCLUDE (already have):\n{have_at_home}"
        if have_at_home and have_at_home.strip()
        else ""
    )

    return f"""Extract & aggregate ALL ingredients. Swedish names. Metric only.
    Categorize: Meat/Fish, Vegetables/Fruits, Dairy, Grains, Herbs, Other.
    Skip basics (spices, oil, mayo, mustard, broth, breadcrumbs, sesame).

    Example format for the output:
    <div>
        <h3>Meat/Fish</h3>
        <ul><li>500 g kött</li><li>300 g fisk</li></ul>
        <h3>Vegetables/Fruits</h3>
        <ul><li>2 st lök</li><li>400 g morötter</li></ul>
        <h3>Dairy</h3>
        <ul><li>250 ml mjölk</li></ul>
        <h3>Grains</h3>
        <ul><li>200 g ris</li></ul>
        <h3>Herbs</h3>
        <ul><li>1 tsk mynta</li></ul>
        <h3>Other</h3>
        <ul><li>100 g chilisås</li></ul>
    </div>

    INGREDIENTS:
    {ingredients_text}{have_at_home_section}
    """


class IngredientService:
    _client = client
    _cleaner = cleaner

    # def save_url_to_weekly_table(self, url: str, position: int):
    #     """
    #     Save a URL into the 'weekly' table in Supabase with family-friendly weekly
    #     plan positioning.
    #     Duplicates meals for consecutive days: Mon→Tue, Wed→Thu, Fri→Sat.

    #     Args:
    #         url (str): The URL to save.
    #         position (int): The position in the weekly plan.
    #     """
    #     response = None
    #     try:
    #         # Calculate which day pair and meal from position
    #         pair_index = position // 2  # Which day pair (0-3)
    #         meal_index = position % 2   # Which meal (0=Lunch, 1=Dinner)

    #         # Handle case where we exceed 4 pairs (8 positions)
    #         if pair_index >= len(day_pairs):
    #             pair_index = pair_index % len(day_pairs)

    #         day_pair = day_pairs[pair_index]
    #         meal_type = meals[meal_index]

    #         # Save for both days in the pair (except Sunday which is single)
    #         for day_name in day_pair:
    #             # Initialize db_position with a default value
    #             db_position = 0

    #             # Calculate the actual position for database
    #             # TODO: consider using a mapping or dictionary for clarity
    #             if day_name == "Monday":
    #                 db_position = 0 if meal_type == "Lunch" else 1
    #             elif day_name == "Tuesday":
    #                 db_position = 2 if meal_type == "Lunch" else 3
    #             elif day_name == "Wednesday":
    #                 db_position = 4 if meal_type == "Lunch" else 5
    #             elif day_name == "Thursday":
    #                 db_position = 6 if meal_type == "Lunch" else 7
    #             elif day_name == "Friday":
    #                 db_position = 8 if meal_type == "Lunch" else 9
    #             elif day_name == "Saturday":
    #                 db_position = 10 if meal_type == "Lunch" else 11
    #             elif day_name == "Sunday":
    #                 db_position = 12 if meal_type == "Lunch" else 13

    #             # Insert with proper positioning
    #             response = supabase.table("weekly").insert({
    #                 "link": url,
    #                 "position": db_position,
    #                 "day_name": day_name,
    #                 "meal_type": meal_type
    #             }).execute()

    #             # Break if it's Sunday (single day)
    #             if day_name == "Sunday":
    #                 break

    #         return response
    #     except Exception as e:
    #         print(f"Error saving URL to the 'weekly' table: {e}")

    def process_recipes(
        self, recipes_text: str, have_at_home: str | None = None
    ) -> str:
        """
        Process recipes and return sanitized HTML.

        This method takes the recipes text input, creates a prompt for the Gemini API,
        and returns a cleaned and categorized list of ingredients.

        Args:
            recipes_text: The raw recipes text to process.
            have_at_home: Optional string of items the user already has at home,
                        used to filter out those ingredients.

        Returns:
            str: Sanitized HTML containing categorized ingredients.
        """
        cleaned_recipes_text = "\n".join(
            line.strip() for line in recipes_text.splitlines() if line.strip()
        )
        parsed_data = parse_input_to_list(cleaned_recipes_text)

        # TODO: don't like this mix of DB and LLM logic, consider refactoring
        # Clear the 'weekly' table before adding new entries
        # supabase.table("weekly").delete().execute()
        # # Save URLs to Supabase
        # for index, item in enumerate(parsed_data):
        #     self.save_url_to_weekly_table(item["url"], index)

        # Extract only the ingredients for the Gemini prompt
        ingredients_text = "\n\n".join(item["ingredients"] for item in parsed_data)

        # Create the prompt for Gemini
        prompt = create_ingredient_prompt(ingredients_text, have_at_home)

        # Send the prompt to Gemini and process the response
        model_response: GenerateContentResponse = self._client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
        )

        raw_response = extract_human_readable_response(model_response)
        return self._cleaner.clean(raw_response)
