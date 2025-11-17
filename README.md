# Group2 Project - Streamlit Application

## Description
This app allows users to organize and manage recipes. It allows users to add new recipes, view other user’s public recipes, derive new recipes from existing recipes, set up shopping lists, create daily meal plans, and track current pantry inventory.

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Group2_Project.git
   cd Group2_Project
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run sign_in.py
   ```
   
   The app will open in your default browser at `http://localhost:8501`

## Project Structure
```
Group2_Project/
├── sign_in.py              # Main entry point
├── database.py             # Database operations
├── theme_manager.py        # Theme/styling management
├── requirements.txt        # Python dependencies
├── pages/                  # Additional Streamlit pages
├── data/                   # Data files
└── themes/                 # Theme configurations
```

## Group Members
- Jay Brown

