# CareerIQ

CareerIQ is a Flask-based career guidance platform that helps users explore suitable job opportunities based on their skills and identify skill gaps for their target roles.

## Features

* User registration and login
* User profile management
* Job listing and exploration
* Skill-based job recommendations
* Skill gap analysis
* Personalized career recommendations
* Web-based interface

## Technologies Used

* **Python**
* **Flask**
* **HTML**
* **CSS**
* **JavaScript**
* **SQLite**
* **Git & GitHub**

## Project Structure

```text
CareerIQ/
├── app/
├── data/
├── static/
├── templates/
├── .env.example
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

## How It Works

1. A user creates an account and logs in.
2. The user provides their profile and skills.
3. CareerIQ analyzes the available job requirements.
4. Suitable job opportunities are recommended based on the user's skills.
5. The skill-gap section helps identify skills that can be developed for targeted roles.

## Installation

Clone the repository:

```bash
git clone https://github.com/Shahid-Ahmed-S/CareerIQ.git
cd CareerIQ
```

Create and activate a virtual environment:

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file based on `.env.example` and add the required configuration values.

> Do not commit your actual `.env` file or any private credentials to GitHub.

## Run the Application

Run the application using:

```bash
python run.py
```

Then open the local URL shown in the terminal.

## Live Demo

**CareerIQ:** https://careeriq-q3ha.onrender.com/login

## Future Improvements

* Expand the job dataset
* Improve recommendation accuracy
* Add more detailed career paths
* Add user progress tracking
* Improve the recommendation and skill-gap algorithms
* Deploy additional production features

## Author

**Shahid Ahmed**

* GitHub: https://github.com/Shahid-Ahmed-S
* LinkedIn: https://www.linkedin.com/in/shahidahmed08/
