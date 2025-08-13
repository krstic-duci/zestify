# Zestify - Recipe Ingredient Aggregator

> **⚠️ IMPORTANT DISCLAIMER**
> 
> This is a **HOBBY PROJECT** created for personal learning and entertainment purposes only. Any resemblance to existing products, services, or trademarks including but not limited to "Zestify", "Lemon", the letter "Z", or any other commercial entities is purely **COINCIDENTAL** and **UNINTENTIONAL**. This project is not affiliated with, endorsed by, or connected to any commercial product or service. Use at your own risk.

## Overview

Zestify is a personal web application that helps aggregate and categorize ingredients from multiple recipes. Paste your recipe text, and the app will extract, translate (to Swedish), and organize ingredients by category using Google's Gemini AI. It also supports weekly meal planning with drag-and-drop reordering.

## Features

- 🍳 **Recipe Processing**: Paste multiple recipes and get organized ingredient lists
- 🏷️ **Smart Categorization**: Automatically groups ingredients into categories (Meat/Fish, Vegetables/Fruits, Dairy, Grains, Spices/Herbs, Other)
- 🇸🇪 **Swedish Translation**: Translates ingredients to Swedish with metric system conversion
- 🔐 **Secure Authentication**: Protected with bcrypt password hashing and signed tokens
- ⚡ **Rate Limiting**: Built-in protection against abuse
- 🎨 **Dark Theme UI**: Clean, modern interface with responsive design
- 🧹 **HTML Sanitization**: Secure output with proper content filtering
- 📅 **Weekly Meal Planner**: Drag-and-drop meals for each day and meal type
- 🛡️ **Comprehensive Error Handling**: Consistent error envelopes and user-friendly notifications

## Tech Stack

- **Backend**: FastAPI 0.116+
- **AI/ML**: Google Gemini 1.5 Flash
- **Authentication**: Passlib (bcrypt) + itsdangerous
- **Database**: Supabase (Postgres)
- **Templates**: Jinja2
- **Security**: Bleach HTML sanitization
- **Rate Limiting**: Custom FastAPI dependencies
- **Configuration**: Pydantic Settings
- **Frontend**: Vanilla JS, Sortable.js for drag-and-drop
- **Python**: 3.13+

## Project Structure

```
zestify/
├── main.py                    # FastAPI application entry point
├── dependency/
│   ├── get_current_user.py    # Authentication dependency
│   └── limiter.py             # Rate limiting dependencies
├── services/
│   ├── auth.py                # Authentication service
│   ├── error_handlers.py      # HTTP error handlers
│   └── ingredients.py         # Core ingredient processing logic
├── utils/
│   ├── config.py              # Configuration management
│   ├── constants.py           # Application constants
│   └── signed_token.py        # Token serialization
├── templates/
│   ├── base.html.jinja        # Base template
│   ├── index.html.jinja       # Main ingredient input page
│   ├── login.html.jinja       # Authentication page
│   ├── weekly.html.jinja      # Weekly meal planning page
│   ├── _ingredients_partial.html.jinja # Ingredient results partial
│   ├── 404.html.jinja         # Not found page
│   └── error.html.jinja       # Error page
├── static/
│   ├── css/                   # Stylesheets
│   ├── js/                    # JavaScript files
│   ├── favicon.ico            # Site icon
│   └── robots.txt             # SEO configuration
├── db/                        # Database connection
├── pyproject.toml             # Project dependencies
├── ruff.toml                  # Code quality configuration
└── .env                       # Environment variables (not in repo)
```

## Installation

### Prerequisites

- Python 3.13+
- Google Gemini API key
- uv package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd zestify
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   APP_USERNAME=your_username
   APP_PASSWORD=your_bcrypt_hashed_password
   AUTH_TOKEN_KEY=your_secret_signing_key
   ```

4. **Run the application**
   ```bash
   uv run fastapi dev
   ```

5. **Access the application**
   Open your browser to `http://localhost:8000`

6. **Build the application**
   ```bash
   uv run fastapi run
   ```

## Usage

1. **Login**: Navigate to `/login` and enter your credentials
2. **Input Recipes**: Paste your recipe text into the textarea on the main page
3. **Process**: Click "Process" to extract and categorize ingredients
4. **Results**: View organized ingredients grouped by category in Swedish
5. **Weekly Planner**: Go to `/weekly` to view and drag-and-drop meals for each day
6. **Logout**: Use the logout link to end your session

## API Endpoints

- `GET /` - Main ingredient input page (protected)
- `GET /login` - Login form
- `POST /login` - Authentication endpoint (rate limited: 5/minute)
- `POST /ingredients` - Process recipes and return results
- `GET /weekly` - Weekly meal planner page
- `POST /swap-meals` - Swap two meals in the weekly plan
- `POST /move-meal` - Move a meal to a specific position
- `GET /logout` - Logout and clear session
- `GET /static/*` - Static file serving

## Rate Limiting

- **Login endpoint**: 5 requests per minute per IP
- **General endpoints**: 10 requests per minute per IP
- **Implementation**: Custom FastAPI dependencies (no external dependencies)

## Security Features

- **Authentication**: Session-based auth with signed tokens
- **Password Hashing**: bcrypt with configurable rounds
- **Rate Limiting**: Custom implementation - 5 requests/minute for login, 10/minute for general endpoints
- **HTML Sanitization**: Bleach filtering for safe output
- **Secure Cookies**: HttpOnly, Secure, SameSite=Strict
- **Input Validation**: Pydantic form validation with length constraints
- **Error Handling**: Comprehensive HTTP status code handling and error envelopes

## Configuration

Key configuration options in `utils/config.py`:

- `GEMINI_API_KEY`: Google Gemini API access
- `APP_USERNAME`/`APP_PASSWORD`: Authentication credentials
- `AUTH_TOKEN_KEY`: Token signing secret
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `MAX_AGE`: Session timeout (default: 24 hours)

## Development

### Code Quality Tools

```bash
# Type checking
uv run mypy .

# Linting and formatting
uv run ruff check .
uv run ruff format .

# Run development server
uv run fastapi dev
```

### Development Dependencies

- `mypy`: Static type checking
- `ruff`: Fast Python linter and formatter
- `types-bleach` & `types-passlib`: Type stubs for better type checking

## License

This is a personal hobby project. Use at your own discretion.

## Contributing

This is a personal project, but feel free to fork and adapt for your own use.

---

**Again, this is a HOBBY PROJECT with no commercial intent or affiliation with any existing products or trademarks.**