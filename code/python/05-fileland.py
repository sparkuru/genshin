from flask import Flask, request, jsonify
from flask import Response
import time

app = Flask(__name__)

UPLOAD_FOLDER = '.'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt'}

def allowed_file(filename):
    return 1
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['PUT'])
def upload_file():
    if 'file' not in request.files and not request.data:
        return jsonify({"error": "No file part"}), 400

    if 'file' in request.files:
        file = request.files['file']
    else:
        file = request.data
        filename = request.headers.get('X-Filename')
        if not filename:
            return jsonify({"error": "No filename provided"}), 400

    if file and allowed_file(filename):
        with open(f"{app.config['UPLOAD_FOLDER']}/{filename}", 'wb') as f:
            f.write(file)
        return jsonify({"message": "File uploaded successfully", "filename": filename}), 200
    else:
        return jsonify({"error": "File type not allowed"}), 400

if __name__ == '__main__':
    print("curl --upload-file <file_path> http://ip:8888/upload -H 'X-Filename: <filename>'")
    app.run(host='0.0.0.0', port=8888)
    def generate_progress():
        for i in range(101):
            yield f"data: {i}\n\n"
            time.sleep(0.1)

    @app.route('/progress')
    def progress():
        return Response(generate_progress(), mimetype='text/event-stream')