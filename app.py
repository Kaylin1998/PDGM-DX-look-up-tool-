
from flask import Flask, request, jsonify, render_template, send_from_directory
import pandas as pd
from rapidfuzz import process

app = Flask(__name__, static_folder='static', template_folder='templates')
df = pd.read_csv("pdgm_diagnoses.csv")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route("/check", methods=["GET"])
def check_dx():
    query = request.args.get("code", "").strip().upper()
    match = df[df['ICD10_Code'] == query]
    if not match.empty:
        info = match.iloc[0]
        return jsonify({
            "match_type": "exact",
            "eligible": info["Eligible"],
            "group": info["Group"],
            "description": info["Description"]
        })

    choices = df['Description'].tolist()
    best_match, score, idx = process.extractOne(query, choices)
    info = df.iloc[idx]
    return jsonify({
        "match_type": "fuzzy",
        "input": query,
        "suggested_description": best_match,
        "eligible": info["Eligible"],
        "group": info["Group"],
        "description": info["Description"]
    })

@app.route("/bulk_check", methods=["POST"])
def bulk_check():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    uploaded_df = pd.read_csv(file)
    results = []

    for _, row in uploaded_df.iterrows():
        code = str(row.get('ICD10_Code', '')).strip().upper()
        match = df[df['ICD10_Code'] == code]
        if not match.empty:
            info = match.iloc[0]
            results.append({
                "ICD10_Code": code,
                "Eligible": info["Eligible"],
                "Group": info["Group"],
                "Description": info["Description"]
            })
        else:
            results.append({
                "ICD10_Code": code,
                "Eligible": False,
                "Group": None,
                "Description": "Not PDGM eligible or not found"
            })

    return jsonify(results)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
