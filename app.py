import os
import requests
import time
import warnings
import pymongo
import ffmpeg
import gridfs
import yt_dlp
import json
import uuid
import firebase_admin 
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file, Response, session
from firebase_admin import db , credentials
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from tqdm import tqdm

# Suppress specific warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

# set token 
load_dotenv()

TOKEN_ONE = os.getenv("M_api_key")
TOKEN_THREE = os.getenv("A_api_key")

firebase_credentials = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
}

# Create a Flask application instance
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5000", "https://subtranscribe.koyeb.app"]}})

app.secret_key = "2F0838f0d6"  

# Set up MongoDB connection
cluster = MongoClient(TOKEN_ONE)
dbase = cluster["Datedb"]  # Specify the database name
fs = gridfs.GridFS(dbase)  # Create a GridFS instance for file storage
progress_collection = dbase['progress']  #(Collection)

# Set up Firebase connection
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred,{
    "databaseURL":"https://subtranscribe-default-rtdb.europe-west1.firebasedatabase.app/"
    })

@app.route('/reset-progress', methods=['GET', 'POST'])
@cross_origin()  # Allow CORS for this route
def reset_progress():
    """Reset the current progress status."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get the current time
    upload_id = str(uuid.uuid4())
    session['upload_id'] = upload_id
    ref = db.reference(f'/UID/{upload_id}')
    ref.update({
        "Date": current_time,
        'Status': 0,
        'Message': "Ready to upload"
    })
    return jsonify(upload_id)

def update_progress_bar(B_status,message):
    """Update the progress bar in the MongoDB database."""
    upload_id = session.get('upload_id')
    ref = db.reference(f'/UID/{upload_id}')
    ref.update({
        'status': round(B_status, 2),
        'message': message
    })
    
@app.route('/progress', methods=['GET', 'POST'])
@cross_origin()  # Allow CORS for this route
def progress_status():
    """Return the current progress status as JSON."""
    upload_id = session.get('upload_id')
    ref = db.reference(f'/UID/{upload_id}')
    progress = ref.get()
    if progress:
        progress.pop("id", None)  
        return jsonify(progress)
    return jsonify({"status": 0, "message": "Ready to upload"})

def Update_progress_db(transcript_id, status, message, Section, file_name=None, link=None):
    """Update the progress status in the MongoDB database."""
    collection = dbase["Main"]  # Specify the collection name
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get the current time

    # Prepare the post data
    post = {
        "_id": transcript_id,
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

def Create_subtitle_to_db(subtitle_path):
    """Create subtitle file to MongoDB."""
    with open(subtitle_path, "rb") as subtitle_file:
        # Store the file in GridFS and return the file ID
        subtitle_id = fs.put(subtitle_file, filename=os.path.basename(subtitle_path), content_type='SRT/VTT')
    return subtitle_id

def delete_audio_from_gridfs(audio_id):
    """Delete audio file document from GridFS using audio ID."""
    fs.delete(audio_id)  # Delete the file from GridFS
    print(f"Audio file with ID {audio_id} deleted successfully.")

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'.mp4', '.wmv', '.mov', '.mkv', '.h.264', '.mp3', '.wav'}
    return '.' in filename and os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_or_link():
    """Handle file uploads or links for transcription."""
    if request.method == 'GET':
        return render_template("index.html")
    
    if request.method == 'POST':
        link = request.form.get('link')  # Get the link from the form
        if link:
            transcript_id = transcribe_from_link(link)  # Transcribe from the provided link
            return transcript_id  
        
        file = request.files.get('file')  # Get the uploaded file
        if file and allowed_file(file.filename):
            audio_stream = file
            file_size = request.content_length  # Get file size in bytes
            try:
                transcript_id = upload_audio_to_assemblyai(audio_stream, file_size)  # Upload directly using stream
                return redirect(url_for('download_subtitle', transcript_id=transcript_id))  # Redirect to download page
            except Exception as e:
                return render_template("error.html")  # Display error page
        else:
            return render_template("error.html")  # Render error page if file type is not allowed
    else:
        return render_template('index.html')

def upload_audio_to_assemblyai(audio_file, file_size):
    """Upload audio file to AssemblyAI in chunks with progress tracking."""
    headers = {"authorization": TOKEN_THREE}
    base_url = "https://api.assemblyai.com/v2"
    
    def upload_chunks():
        """Generator function to upload file in chunks and track progress."""
        uploaded_size = 0
        while True:
            chunk = audio_file.read(300000)  # Read a 300 KB chunk
            if not chunk:
                break
            yield chunk
            uploaded_size += len(chunk)
            progress_percentage = (uploaded_size / file_size) * 100  # Calculate progress percentage
            prog_message = f"Processing... {progress_percentage:.2f}%"
            
            print(f"Progress: {progress_percentage:.2f}%, Message: {prog_message}")
        
            # Update the progress bar
            update_progress_bar(B_status=progress_percentage, message=prog_message)
    
    # Upload the file to AssemblyAI and get the URL
    try:
        # Upload the audio file to AssemblyAI
        response = requests.post(f"{base_url}/upload", headers=headers, data=upload_chunks(), stream=True)
        if response.status_code!= 200:
            raise RuntimeError("File upload failed.")
        #...
    except Exception as e:
        update_progress_bar(0, f"Error uploading audio: {e}")
        return None
    
    upload_url = response.json()["upload_url"]

    # Request transcription from AssemblyAI using the uploaded file URL
    data = {"audio_url": upload_url}
    response = requests.post(f"{base_url}/transcript", json=data, headers=headers)

    transcript_id = response.json()["id"]
    polling_endpoint = f"{base_url}/transcript/{transcript_id}"

    # Poll for the transcription result until completion
    while True:
        transcription_result = requests.get(polling_endpoint, headers=headers).json()
        if transcription_result['status'] == 'completed':
            # Update progress in the database and clean up
            Update_progress_db(transcript_id, 100, "Transcription completed", "Download page")
            return transcript_id
        elif transcription_result['status'] == 'error':
            raise RuntimeError(f"Transcription failed: {transcription_result['error']}")

def convert_video_to_audio(video_path):
    """Convert video file to audio using ffmpeg."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_file_path = f'audio_{timestamp}.mp3'
    
    try:
        ffmpeg.input(video_path).output(audio_file_path).run(overwrite_output=True)
        return audio_file_path
    except Exception as e:
        print(f"Error converting video to audio: {e}")
        return None

def transcribe_from_link(link):
    """Transcribe audio from a provided link."""
    ydl_opts = {
        'format': 'bestaudio/best',  # Select the best audio format
        'quiet': True,                # Suppress output messages
        'no_warnings': True,          # Suppress warnings
        'extract_audio': True,        # Extract audio from the video
        'skip_download': True,        # Skip downloading the actual file
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link)  # Extract information from the provided link
        audio_url = info.get('url', None)  # Get the audio URL

        # Get the size of the audio file using HEAD request
        response = requests.head(audio_url)
        total_size = int(response.headers.get('content-length', 0))  # Get total file size
        # Initialize progress bar
        with tqdm(total=total_size, unit='B', unit_scale=True, desc='Uploading', ncols=100) as bar:
            def upload_chunks():
                global prog_status, prog_message
                # Stream the audio file in chunks

                previous_status = -1  # Track the last updated progress
                with requests.get(audio_url, stream=True) as f:
                    for chunk in f.iter_content(chunk_size=200000):  # Read 200KB chunks
                        if not chunk:
                            break
                        yield chunk
                        bar.update(len(chunk))  # Update progress bar


                        # Update the progress dictionary for frontend
                        prog_status = (bar.n / total_size) * 100

                        # Update every 10% increment
                        if int(prog_status) % 10 == 0 and int(prog_status) != previous_status:
                            prog_message = f"Processing... {prog_status:.2f}%"
                            update_progress_bar(B_status=prog_status, message=prog_message)
                            previous_status = int(prog_status)
                            continue
                        if prog_status == 100:
                            prog_message = "Please wait for a few seconds..."
                            update_progress_bar(B_status=prog_status,message=prog_message)
                            break

            # Upload the audio file to AssemblyAI in chunks
            base_url = "https://api.assemblyai.com/v2"
            headers = {"authorization": TOKEN_THREE}  # Set authorization header
            response = requests.post(base_url + "/upload", headers=headers, data=upload_chunks(),stream=True)

            # Check upload response
            if response.status_code != 200:
                return f"Error uploading audio: {response.json()}"

    # Send the audio URL to AssemblyAI for transcription
    data = {"audio_url": audio_url}  # Prepare data with audio URL
    response = requests.post(base_url + "/transcript", json=data, headers=headers)  # Make POST request to create a transcript

    if response.status_code != 200:  # Check if the request was successful
        return f"Error creating transcript: {response.json()}"  # Return error message if not successful

    transcript_id = response.json()['id']  # Get the transcript ID from the response

    # Polling to check the status of the transcript
    while True:
        transcript_response = requests.get(f"{base_url}/transcript/{transcript_id}", headers=headers)  # Get the status of the transcript
        if transcript_response.status_code == 200:  # Check if the request was successful
            transcript_data = transcript_response.json()  # Parse the JSON response
            if transcript_data['status'] == 'completed':  # If the transcription is completed
                Update_progress_db(transcript_id, status=prog_status, message="Completed", Section="Download page", link=audio_url)  # Update progress in the database
                return redirect(url_for('download_subtitle', transcript_id=transcript_id))  # Redirect to download page
            elif transcript_data['status'] == 'error':  # If there was an error during transcription
                Update_progress_db(transcript_id, status=0, message="Invalid Link", Section="Link", link=audio_url)  # Update database with error
                return render_template("error.html")  # Render error page
        else:
            return render_template("error.html")  # Render error page if status request failed

# def upload_audio_to_gridfs(file_path):
#     """Upload audio file to MongoDB using GridFS."""
#     with open(file_path, "rb") as f:
#         # Store the file in GridFS and return the file ID
#         audio_id = fs.put(f, filename=os.path.basename(file_path), content_type='audio/video')

#     return audio_id


@app.route('/download/<transcript_id>', methods=['GET', 'POST'])
def download_subtitle(transcript_id):
    """Handle subtitle download based on the transcript ID."""

    if request.method == 'POST':
        file_format = request.form['format']  # Get the requested file format
        headers = {"authorization": TOKEN_THREE}
        url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}/{file_format}"

        response = requests.get(url, headers=headers)  # Request the subtitle file
        if response.status_code == 200:
            timesub = datetime.now().strftime("%Y%m%d_%H%M%S")  # Generate a timestamp for the subtitle file
            subtitle_file = f"subtitle_{timesub}.{file_format}"  # Create the subtitle filename
            with open(subtitle_file, 'w') as f:
                f.write(response.text)  # Write the subtitle text to the file
            
            subtitle_path = Create_subtitle_to_db(subtitle_file)
            return redirect(url_for('serve_file', filename=subtitle_file))  # Redirect to serve the file
        else:
            return render_template("error.html")  # Render error page if request fails
    return render_template('subtitle.html')  # Render the subtitle download page

@app.route('/serve/<filename>')
def serve_file(filename):
    """Serve the subtitle file for download."""
    file_path = os.path.join(os.getcwd(), filename)  # Use a full path for the file

    if os.path.exists(file_path):  # Check if the file exists
        response = send_file(file_path, as_attachment=True)  # Send the file as an attachment

    return response  # Return the file response

if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True,port=8000)

