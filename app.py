
import os
import shutil
import hashlib
from collections import defaultdict
from flask import Flask, request, render_template_string, url_for


ROOT_DIR = 'D:\STEAM' 

class DirectoryManager:
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)
    
    def get_all_files(self, ignore_destination=True):
        file_list = []
        for root, dirs, files in os.walk(self.root_dir):
            if ignore_destination:
                dirs[:] = [d for d in dirs if not d.endswith('_files')]
            for file in files:
                file_list.append(os.path.join(root, file))
        return file_list

    def organize_files(self):
        logs = []
        all_files = self.get_all_files(ignore_destination=True)
        for file_path in all_files:
            file_name = os.path.basename(file_path)
            ext = os.path.splitext(file_name)[1].lower().strip('.')
            if not ext:
                ext = 'no_extension'
            dest_folder = os.path.join(self.root_dir, f"{ext}_files")
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
            new_path = os.path.join(dest_folder, file_name)
            if os.path.exists(new_path):
                base, extension = os.path.splitext(file_name)
                new_path = os.path.join(dest_folder, f"{base}_copy{extension}")
            try:
                shutil.move(file_path, new_path)
                logs.append(f"Moved {file_path} → {new_path}")
            except Exception as e:
                logs.append(f"Error moving file {file_path}: {e}")
        return logs

    def search_files(self, query):
        results = []
        all_files = self.get_all_files(ignore_destination=False)
        for file_path in all_files:
            if query.lower() in os.path.basename(file_path).lower():
                results.append(file_path)
        return results

    def detect_duplicates(self):
        hash_dict = defaultdict(list)
        all_files = self.get_all_files(ignore_destination=False)
        for file_path in all_files:
            file_hash = self._compute_md5(file_path)
            if file_hash:
                hash_dict[file_hash].append(file_path)
        duplicates = {h: files for h, files in hash_dict.items() if len(files) > 1}
        return duplicates

    def _compute_md5(self, file_path, chunk_size=4096):
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Error computing hash for {file_path}: {e}")
            return None

    def summary(self):
        total_files = 0
        total_size = 0
        all_files = self.get_all_files(ignore_destination=False)
        for file_path in all_files:
            total_files += 1
            try:
                total_size += os.path.getsize(file_path)
            except Exception:
                pass
        return {"total_files": total_files, "total_size_mb": total_size / (1024 * 1024)}

dm = DirectoryManager(ROOT_DIR)

app = Flask(__name__)


css_style = """
<style>
    body { font-family: Arial, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; padding: 0; }
    .container { width: 80%; margin: 30px auto; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    h1 { color: #007BFF; }
    a { color: #007BFF; text-decoration: none; }
    a:hover { text-decoration: underline; }
    ul { list-style-type: none; padding: 0; }
    li { padding: 5px 0; }
    .btn { display: inline-block; padding: 10px 15px; margin: 5px 0; background-color: #007BFF; color: #fff; border-radius: 4px; text-decoration: none; }
    .btn:hover { background-color: #0056b3; }
    form input[type="text"] { padding: 10px; width: 70%; margin-right: 10px; border: 1px solid #ccc; border-radius: 4px; }
    form input[type="submit"] { padding: 10px 15px; border: none; background-color: #28a745; color: #fff; border-radius: 4px; cursor: pointer; }
    form input[type="submit"]:hover { background-color: #218838; }
</style>
"""

home_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI-Powered Directory Management</title>
    {css_style}
</head>
<body>
    <div class="container">
        <h1>Directory Management System</h1>
        <ul>
            <li><a class="btn" href="{{{{ url_for('organize') }}}}">Organize Files</a></li>
            <li><a class="btn" href="{{{{ url_for('search') }}}}">Search Files</a></li>
            <li><a class="btn" href="{{{{ url_for('duplicates') }}}}">Detect Duplicates</a></li>
            <li><a class="btn" href="{{{{ url_for('summary') }}}}">Directory Summary</a></li>
        </ul>
    </div>
</body>
</html>
"""

organize_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Organize Files</title>
    {css_style}
</head>
<body>
    <div class="container">
        <h1>Organize Files</h1>
        <p>{{{{ message|safe }}}}</p>
        <a href="{{{{ url_for('home') }}}}">Back to Home</a>
    </div>
</body>
</html>
"""

search_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Search Files</title>
    {css_style}
</head>
<body>
    <div class="container">
        <h1>Search Files</h1>
        <form method="GET" action="{{{{ url_for('search') }}}}">
            <input type="text" name="query" placeholder="Enter search query" value="{{{{ query|default('') }}}}">
            <input type="submit" value="Search">
        </form>
        {{% if results is defined %}}
            <h2>Results:</h2>
            {{% if results %}}
                <ul>
                {{% for file in results %}}
                    <li>{{{{ file }}}}</li>
                {{% endfor %}}
                </ul>
            {{% else %}}
                <p>No files found.</p>
            {{% endif %}}
        {{% endif %}}
        <a href="{{{{ url_for('home') }}}}">Back to Home</a>
    </div>
</body>
</html>
"""

duplicates_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Detect Duplicates</title>
    {css_style}
</head>
<body>
    <div class="container">
        <h1>Duplicate Files</h1>
        {{% if duplicates %}}
            {{% for hash_val, files in duplicates.items() %}}
                <h3>Hash: {{{{ hash_val }}}}</h3>
                <ul>
                {{% for file in files %}}
                    <li>{{{{ file }}}}</li>
                {{% endfor %}}
                </ul>
            {{% endfor %}}
        {{% else %}}
            <p>No duplicates found.</p>
        {{% endif %}}
        <a href="{{{{ url_for('home') }}}}">Back to Home</a>
    </div>
</body>
</html>
"""

summary_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Directory Summary</title>
    {css_style}
</head>
<body>
    <div class="container">
        <h1>Directory Summary</h1>
        <p>Total Files: {{{{ summary.total_files }}}}</p>
        <p>Total Size: {{{{ summary.total_size_mb | round(2) }}}} MB</p>
        <a href="{{{{ url_for('home') }}}}">Back to Home</a>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(home_html)

@app.route('/organize')
def organize():
    logs = dm.organize_files()
    message = "<br>".join(logs) if logs else "No files were moved."
    return render_template_string(organize_html, message=message)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    results = dm.search_files(query) if query else None
    return render_template_string(search_html, query=query, results=results)

@app.route('/duplicates')
def duplicates():
    dupes = dm.detect_duplicates()
    return render_template_string(duplicates_html, duplicates=dupes)

@app.route('/summary')
def summary():
    summ = dm.summary()
    return render_template_string(summary_html, summary=summ)

if __name__ == '__main__':
    app.run(debug=True)
