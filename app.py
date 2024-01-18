from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_socketio import SocketIO
from threading import Thread
from scraper import scrape
import os

app = Flask(__name__)
socketio = SocketIO(app)

output_folder = 'output'

@app.route('/')
def index():
    print('Request received: Index')
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        print('No file part in request.')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        print('No selected file.')
        return redirect(url_for('index'))

    print(f'File received: {file.filename}')

    file_path = os.path.join('uploads', file.filename)
    file.save(file_path)

    # Start a new thread to run the scraping job
    interval_days = int(request.form['interval'])  # Retrieve interval from the form
    print(f'Starting scraping job with file path: {file_path}, interval: {interval_days} days')
    thread = Thread(target=run_scrape, args=(file_path, interval_days))
    thread.start()

    return redirect(url_for('output'))

def run_scrape(file_path, interval_days):
    try:
        print('Scraping job started.')
        scrape(file_path=file_path, interval_days=interval_days)
    except Exception as e:
        print(f'Error during scraping job: {e}')
    finally:
        os.remove(file_path)  # Remove the uploaded file after scraping
        print('Uploaded file removed after scraping job.')

@app.route('/output')
def output():
    output_files = os.listdir(output_folder)
    if output_files:
        print('Displaying output page with available files.')
        return render_template('output.html', output_files=output_files)
    else:
        print('Displaying output page with no available files.')
        return render_template('output.html', message="No output files available. The process might be ongoing.")

@app.route('/download/<filename>')
def download(filename):
    print(f'Download requested for file: {filename}')
    return send_from_directory(output_folder, filename)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    socketio.run(app, host='0.0.0.0', port='5000', allow_unsafe_werkzeug=True)
