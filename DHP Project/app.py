from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import os

app = Flask(__name__, static_folder="static")

# Load Excel file and preprocess
try:
    df = pd.read_excel("new.xlsx", parse_dates=["Date"])
    df["year"] = df["Date"].dt.year
    df["Tags"] = df["Tags"].astype(str)

    # Extract all unique tags
    all_tags = df["Tags"].dropna().apply(lambda x: [tag.strip() for tag in x.split(",")])
    flat_tags = [tag for sublist in all_tags for tag in sublist]
    unique_tags = sorted(set(flat_tags))

except Exception as e:
    print("Error loading Excel file:", e)
    df = pd.DataFrame()
    unique_tags = []

# Serve index.html
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

# API: Return list of all tags
@app.route("/get_tags")
def get_tags():
    return jsonify(unique_tags)

# API: Return list of all years
@app.route("/get_years")
def get_years():
    years = sorted(df["year"].dropna().unique().tolist())
    return jsonify(years)

# API: Return tag frequencies (for line/bar chart)
@app.route("/get_data", methods=["POST"])
def get_data():
    selected_tags = request.json.get("Tags", [])
    result = {}

    for tag in selected_tags:
        mask = df["Tags"].str.contains(rf'\b{tag}\b', case=False, na=False)
        filtered = df[mask]
        counts = filtered.groupby("year").size().to_dict()
        result[tag] = counts

    return jsonify(result)

# API: Return top 20 tags (for pie chart)
@app.route("/top_tags", methods=["POST"])
def top_tags():
    req_data = request.get_json()
    year = req_data.get("year", "All")

    if year != "All":
        try:
            year = int(year)
            filtered_df = df[df["year"] == year]
        except:
            return jsonify([])  # Invalid year
    else:
        filtered_df = df

    all_tags = filtered_df["Tags"].dropna().apply(lambda x: [tag.strip() for tag in x.split(",")])
    flat_tags = [tag for sublist in all_tags for tag in sublist]

    tag_counts = pd.Series(flat_tags).value_counts().nlargest(20)
    total = tag_counts.sum()

    data = [
        {"tag": tag, "count": count, "percentage": round((count / total) * 100, 2)}
        for tag, count in tag_counts.items()
    ]

    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
