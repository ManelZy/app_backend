from flask import Flask, request, jsonify
import json
import random
import re
from flask_cors import CORS


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Define mappings for topics and difficulty levels
TOPIC_MAP = {
    1: "علمي",  # Scientific, technical, and medical
    2: "أدبي",  # Literary, poetry, and stories
    3: "ديني",  # Religious and spiritual
    4: "تاريخي",  # Historical and biographies
    5: "اجتماعي",  # Social and relationships
    6: "تعليمي",  # Educational
    7: "سياسي",  # Political and diplomatic
    8: "اقتصادي",  # Economic and financial
    9: "ثقافي",  # Cultural and artistic
    10: "رياضي",  # Sports
    11: "ترفيهي",  # Entertainment and stories
    12: "جغرافي",  # Geographical
}

DIFFICULTY_MAP = {1: "مبتدئ", 2: "متوسط", 3: "متقدم"}


def is_arabic_text(text):
    # Arabic Unicode ranges
    arabic_pattern = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+")
    return bool(arabic_pattern.search(text))


def validate_question(question):
    # Count words in question text
    word_count = len(question["question"].split())
    if word_count < 4:
        return False

    # Check if answer is in Arabic
    if not is_arabic_text(question["answer"]):
        return False

    return True


# Load and filter dataset at startup
def load_dataset():
    try:
        with open("quiz_data.json", "r", encoding="utf-8") as file:
            raw_data = json.load(file)
            filtered_data = []

            for item in raw_data:
                # First filter individual questions within each text
                valid_questions = [q for q in item["questions"] if validate_question(q)]

                # Only include texts that have 3 or more valid questions
                if len(valid_questions) >= 1:
                    item_copy = item.copy()
                    item_copy["questions"] = valid_questions
                    filtered_data.append(item_copy)

            print(f"Original dataset size: {len(raw_data)}")
            print(f"Filtered dataset size: {len(filtered_data)}")
            return filtered_data

    except Exception as e:
        print(f"Error loading dataset: {e}")
        return []


# Load the dataset when the application starts
DATASET = load_dataset()


@app.route("/get_question", methods=["GET"])
def get_question():
    try:
        # Get query parameters as integers
        difficulty_id = request.args.get("difficulty", type=int)
        topic_id = request.args.get("topic", type=int)

        # Convert IDs to Arabic strings using the maps
        difficulty = DIFFICULTY_MAP.get(difficulty_id) if difficulty_id else None
        topic = TOPIC_MAP.get(topic_id) if topic_id else None

        # Filter based on criteria using the global DATASET
        filtered_questions = [
            q
            for q in DATASET
            if (difficulty is None or q["difficulty_level"] == difficulty)
            and (topic is None or q["topic"] == topic)
        ]

        # Check if we have any matching questions
        if not filtered_questions:
            return jsonify(
                {
                    "error": "No questions found matching the specified criteria",
                    "valid_topics": TOPIC_MAP,
                    "valid_difficulties": DIFFICULTY_MAP,
                }
            ), 404

        # Return a random question
        random_question = random.choice(filtered_questions)
        return jsonify(random_question)

    except Exception as e:
        return jsonify(
            {
                "error": str(e),
                "valid_topics": TOPIC_MAP,
                "valid_difficulties": DIFFICULTY_MAP,
            }
        ), 500


# Add an endpoint to get the available mappings
@app.route("/mappings", methods=["GET"])
def get_mappings():
    return jsonify({"topics": TOPIC_MAP, "difficulties": DIFFICULTY_MAP})


# Add an endpoint to get dataset stats
@app.route("/stats", methods=["GET"])
def get_stats():
    topic_counts = {}
    difficulty_counts = {}
    questions_per_text = []

    for text in DATASET:
        topic_counts[text["topic"]] = topic_counts.get(text["topic"], 0) + 1
        difficulty_counts[text["difficulty_level"]] = (
            difficulty_counts.get(text["difficulty_level"], 0) + 1
        )
        questions_per_text.append(len(text["questions"]))

    return jsonify(
        {
            "total_texts": len(DATASET),
            "topics_distribution": topic_counts,
            "difficulty_distribution": difficulty_counts,
            "avg_questions_per_text": sum(questions_per_text) / len(questions_per_text)
            if questions_per_text
            else 0,
            "min_questions": min(questions_per_text) if questions_per_text else 0,
            "max_questions": max(questions_per_text) if questions_per_text else 0,
        }
    )


if __name__ == "__main__":
    # Print startup information
    print(f"Dataset loaded with {len(DATASET)} texts")
    app.run(debug=True)
