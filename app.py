import os
import requests
import time
import warnings
import moviepy.editor as mp
import pymongo
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
import dropbox  # Importing the Dropbox library
from pymongo import MongoClient

# Suppress specific warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Create a Flask application instance
app = Flask(__name__)

# Set up Dropbox connection with the access token
DROPBOX_ACCESS_TOKEN = 'sl.B-GddIbtynfeZ9ff0WhOXbJSW_XdVDvONyR7C3s_IJD5qbWjJqudWOduVYDFVm7mOUFnRQ_ONi_xKQRGeK_EcxmioGdi-wxThy-zGO_icDlSf79i57BVfzeuJi3NKCbx9SyPnXKA-5hl1zx0-wfpgKg'  # Replace this with your access token
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Set up MongoDB connection
cluster = MongoClient("mongodb+srv://Adde:1234@cluster0.1xefj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
# Initial progress status
progress = {"status": 0, "message": "Initializing"}

def Update_progress_db(transcript_id, status, message, Section, file_name=None, link=None):
    """Update the progress status in the MongoDB database."""
    db = cluster["Datedb"]  # Specify the database name
    collection = db["Main"]  # Specify the collection name
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get the current time

    # Prepare the post data
    post = {
        "ID": transcript_id,
        "status": status,
        "message": message,
        "Section": Section,
        "file_name": file_name if file_name else "NULL",  
        "link": link if link else "NULL",
        "DATE": current_time
    }

    # Insert the progress data into the collection
    collection.insert_one(post)  

@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

def upload_audio_to_dropbox(file_path):
    """Upload audio file to Dropbox."""
    with open(file_path, "rb") as f:
        dbx.files_upload(f.read(), f'/audio/{os.path.basename(file_path)}', mute=True)

def upload_audio_to_assemblyai(audio_path):
    """Upload audio file to AssemblyAI for transcription."""
    global progress

    headers = {"authorization": "2ba819026c704d648dced28f3f52406f"}
    base_url = "https://api.assemblyai.com/v2"
    
    with open(audio_path, "rb") as f:
        # Upload the audio file to AssemblyAI
        response = requests.post(base_url + "/upload", headers=headers, data=f)

    upload_url = response.json()["upload_url"]  # Get the upload URL

    # Prepare the request data with the webhook URL
    data = {
        "audio_url": upload_url,
        "webhook_url": "https://subtranscribe2.vercel.app"  # Make sure this is correct
    }
    
    # Request transcription
    response = requests.post(base_url + "/transcript", json=data, headers=headers)
    transcript_id = response.json().get('id')  # Get the transcript ID
    
    progress["message"] = "Uploading"  # Update progress message
    progress["status"] = 15  # Update status after starting upload

    return transcript_id  # Return the transcript ID

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive webhook notifications from AssemblyAI."""
    data = request.json

    if 'id' in data:
        transcript_id = data['id']  # Get the transcript ID from the webhook data
        print(f"Transcription {transcript_id} completed.")
        return '', 200
    else:
        print("No transcript ID found in the webhook data.")
        return '', 400

@app.route('/progress')
def progress_status():
    """Return the current progress status as JSON."""
    return jsonify(progress)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'.mp4', '.wmv', '.mov', '.mkv', '.h.264', '.mp3', '.wav'}
    return '.' in filename and os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_or_link():
    """Handle file uploads or links for transcription."""
    global progress
    progress = {"status": 0, "message": "Initializing"}  # Reset progress

    if request.method == 'POST':
        link = request.form.get('link')  # Get the link from the form
        progress["status"] = 10  # Update status
        if link:
            progress["status"] = 20  # Update status for link processing
            progress["message"] = "Initializing"
            transcript_id = transcribe_from_link(link)  # Transcribe from the provided link
            return transcribe_from_link(link)  # Redirect to transcribe from the link

        file = request.files.get('file')  # Get the uploaded file
        if file and allowed_file(file.filename):
            time.sleep(1)  # Pause for a moment

            progress["status"] = 10  # Update status
            filename = secure_filename(file.filename)  # Secure the filename
            file_path = f'/tmp/{filename}'  # Use a temporary file path

            try:
                file.save(file_path)  # Save the uploaded file
                file_extension = os.path.splitext(file_path)[1].lower()  # Get the file extension

                # Process video files
                if file_extension in [".mp4", ".wmv", ".mov", ".mkv", ".h.264"]:
                    video = mp.VideoFileClip(file_path)  # Load the video file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Generate a timestamp
                    audio_file_path = f'/tmp/audio_{timestamp}.mp3'  # Use a temporary audio file path
                    video.audio.write_audiofile(audio_file_path)  # Convert video to audio
                    video.reader.close()  # Close the video reader
                    video.audio.reader.close_proc()  # Close the audio reader
                    progress["status"] = 25  # Update status
                    progress["message"] = "Converting to Audio file"  # Update message
                    os.remove(file_path)  # Remove the original video file

                # Process audio files
                elif file_extension in [".mp3", ".wav"]:
                    audio_file_path = file_path  # Use the uploaded audio file
                    progress["status"] = 30  # Update status
                    progress["message"] = "Uploading audio file"  # Update message
                else:
                    os.remove(file_path)  # Remove the file if not allowed
                    Update_progress_db(transcript_id, status=0, message="Error file", Section="Upload Page")
                    return render_template("error.html")  # Render error page if file type is not allowed

                # Upload the audio file to Dropbox
                upload_audio_to_dropbox(audio_file_path)

                progress["status"] = 40  # Update status
                transcript_id = upload_audio_to_assemblyai(audio_file_path)  # Upload audio to AssemblyAI
                Update_progress_db(transcript_id, status=100, message="completed", Section="Download page", file_name=filename)
                return redirect(url_for('download_subtitle', transcript_id=transcript_id))  # Redirect to download subtitle
            except Exception as e:
                progress["status"] = 0  # Reset status on error
                progress["message"] = "Error: " + str(e)  # Update message with error
                return render_template("error.html")  # Render error page

    else:
        return render_template('index.html')  # Render the index page if GET request

def transcribe_from_link(link):
    """Transcribe audio from a provided link."""
    base_url = "https://api.assemblyai.com/v2"
    headers = {"authorization": "2ba819026c704d648dced28f3f52406f"}

    data = {"audio_url": link}  # Prepare the data with the audio URL
    response = requests.post(base_url + "/transcript", json=data, headers=headers)  # Request transcription
    
    progress["status"] = 40  # Update status
    progress["message"] = "Processing"  # Update message
    if response.status_code != 200:
        return f"Error creating transcript: {response.json()}"  # Return error if transcription failed

    transcript_id = response.json()['id']  # Get the transcript ID

    while True:
        # Check the status of the transcription
        transcript_response = requests.get(f"{base_url}/transcript/{transcript_id}", headers=headers)
        if transcript_response.status_code == 200:
            transcript_data = transcript_response.json()  # Get the transcription data
            progress["status"] = 80  # Update status
            if transcript_data['status'] == 'completed':
                progress["status"] = 100  # Update status to completed
                progress["message"] = "Processing Complete"  # Update message
                Update_progress_db(transcript_id, status=100, message="completed", Section="Download page", link=link)
                return redirect(url_for('download_subtitle', transcript_id=transcript_id))  # Redirect to download subtitle
            elif transcript_data['status'] == 'error':
                Update_progress_db(transcript_id, status=0, message="Invalid Link", Section="Link", link=link)
                return render_template("error.html")  # Render error page if there's an error
        else:
            return render_template("error.html")  # Render error page if request fails

@app.route('/download/<transcript_id>', methods=['GET', 'POST'])
def download_subtitle(transcript_id):
    """Handle subtitle download based on the transcript ID."""
    progress["message"] = "Processing Complete"  # Update progress message
    progress["status"] = 100  # Update status
    if request.method == 'POST':
        file_format = request.form['format']  # Get the requested file format
        headers = {"authorization": "2ba819026c704d648dced28f3f52406f"}
        url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}/{file_format}"

        response = requests.get(url, headers=headers)  # Request the subtitle file
        if response.status_code == 200:
            timesub = datetime.now().strftime("%Y%m%d_%H%M%S")  # Generate a timestamp for the subtitle file
            subtitle_file = f"subtitle_{timesub}.{file_format}"  # Create the subtitle filename
            subtitle_path = f'/tmp/{subtitle_file}'  # Use a temporary path for the subtitle file
            with open(subtitle_path, 'w') as f:
                f.write(response.text)  # Write the subtitle text to the file
            
            return redirect(url_for('serve_file', filename=subtitle_file))  # Redirect to serve the file
        else:
            return render_template("error.html")  # Render error page if request fails
    return render_template('subtitle.html')  # Render the subtitle download page

@app.route('/serve/<filename>')
def serve_file(filename):
    """Serve the subtitle file for download."""
    file_path = f'/tmp/{filename}'  # Use a temporary path for the file

    if os.path.exists(file_path):  # Check if the file exists
        try:
            response = send_file(file_path, as_attachment=True)  # Send the file as an attachment
            
            try:
                os.remove(file_path)  # Remove the file after sending
            except PermissionError:
                time.sleep(1)  # Wait a moment if there is a permission error
            
            return response  # Return the file response
        except Exception:
            return render_template("error.html")  # Render error page if sending fails
        except FileNotFoundError:
            return render_template("error.html")  # Render error page if file not found
        except TypeError:
            return render_template("error.html")  # Render error page on type error
    
if __name__ == '__main__':
    # Run the Flask application
    app.run(host='0.0.0.0')

