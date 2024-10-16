from flask import Flask, request, render_template, redirect, url_for, flash
import os
import csv
import json
import chardet
from collections import defaultdict
import subprocess

app = Flask(__name__)
app.secret_key = os.urandom(24)

def csv_to_jsonld(csv_file_path, jsonld_file_path):
    # Detect the file's encoding
    with open(csv_file_path, 'rb') as f:
        result = chardet.detect(f.read())

    encoding = result['encoding']

    # Open the CSV file with the detected encoding
    with open(csv_file_path, mode='r', newline='', encoding=encoding) as csvfile:
        reader = csv.DictReader(csvfile)
        form_name_to_fields = defaultdict(list)

        # Group Variable/Field Names by Form Name
        for row in reader:
            form_name = row['Form Name']
            variable_name = row['Variable / Field Name']
            form_name_to_fields[form_name].append(variable_name)

        # Initialize the JSON-LD structure
        jsonld = {
            "@context": {
                "schema": "http://schema.org/"
            },
            "@graph": []
        }

        # Process each Form Name and its corresponding Variable/Field Names
        for form_name, fields in form_name_to_fields.items():
            entry = {
                "@id": f"bts:{form_name}",
                "@type": "rdfs:Class",
                "rdfs:label": form_name,
                #"rdfs:comment": [],
                "schema:isPartOf": {
                    "@id": "http://schema.biothings.io"
                },
                "sms:displayName": form_name,
                "sms:requiresDependency": [
                    {"@id": f"bts:{field}"} for field in fields
                ]
            }
            jsonld["@graph"].append(entry)

    # Write the JSON-LD data to a file
    with open(jsonld_file_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(jsonld, jsonfile, indent=4)

    # Run the schematic schema convert command
    try:
        subprocess.run(
            ["schematic", "schema", "convert", jsonld_file_path],
            check=True
        )
        flash('Schema conversion completed successfully!')
    except subprocess.CalledProcessError as e:
        flash(f'Error during schema conversion: {str(e)}')

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files or 'save_path' not in request.form:
            flash('Please select a file and specify a save location.')
            return redirect(request.url)

        file = request.files['file']
        save_path = request.form['save_path']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if not save_path:
            flash('No save location specified')
            return redirect(request.url)

        if file and save_path:
            filename = file.filename
            file_path = os.path.join(os.path.dirname(__file__), filename)
            file.save(file_path)

            # Construct the JSON-LD file path using the provided save location and original filename
            jsonld_file_path = os.path.join(save_path, os.path.splitext(filename)[0] + '.jsonld')
            csv_to_jsonld(file_path, jsonld_file_path)
            flash(f'File converted successfully! JSON-LD saved as {jsonld_file_path}')
            return redirect(url_for('upload_file'))

    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)
