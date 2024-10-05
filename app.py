import os
import requests
import time
import warnings
import moviepy.editor as mp
import pymongo
import ffmpeg
import gridfs
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
from pymongo import MongoClient

# Suppress specific warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Create a Flask application instance
app = Flask(__name__)

# Set up MongoDB connection
cluster = MongoClient("mongodb+srv://Adde:1234@cluster0.1xefj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = cluster["Datedb"]  # Specify the database name
fs = gridfs.GridFS(db)  # Create a GridFS instance for file storage

# Initial progress status
progress = {"status": 0, "message": "Initializing"}

def Update_progress_db(transcript_id, status, message, Section, file_name=None, link=None):
    """Update the progress status in the MongoDB database."""
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

def upload_audio_to_gridfs(file_path):
    """Upload audio file to MongoDB using GridFS."""
    with open(file_path, "rb") as f:
        # Store the file in GridFS and return the file ID
        audio_id = fs.put(f, filename=os.path.basename(file_path), content_type='audio/video')

    return audio_id

def Create_subtitle_to_db(subtitle_path):
    """Create subtitle file to MongoDB."""
    with open(subtitle_path, "rb") as subtitle_file:
        # Store the file in GridFS and return the file ID
        subtitle_id = fs.put(subtitle_file, filename=os.path.basename(subtitle_path), content_type='SRT/VTT')
    return subtitle_id
    
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

def delete_audio_from_gridfs(audio_id):
    """Delete audio file document from GridFS using audio ID."""
    fs.delete(audio_id)  # Delete the file from GridFS
    print(f"Audio file with ID {audio_id} deleted successfully.")

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
            file_path = f'{filename}' 
            try:
                file.save(file_path)  # Save the uploaded file
                file_extension = os.path.splitext(file_path)[1].lower()  # Get the file extension

                # Process video files
                if file_extension in [".mp4", ".wmv", ".mov", ".mkv", ".h.264"]:
                    audio_file_path = convert_video_to_audio(file_path)  # Convert video to audio
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

                # Upload the audio file to GridFS
                audio_id = upload_audio_to_gridfs(audio_file_path)

                progress["status"] = 40  # Update status
                transcript_id = upload_audio_to_assemblyai(audio_file_path)  # Upload audio to AssemblyAI
                Update_progress_db(transcript_id, status=100, message="completed", Section="Download page", file_name=filename)
                
                # Delete the audio file from GridFS after redirecting
                delete_audio_from_gridfs(audio_id)  # Call the delete function
                return redirect(url_for('download_subtitle', transcript_id=transcript_id))  # Redirect to download subtitle
            except Exception as e:
                progress["status"] = 0  # Reset status on error
                progress["message"] = "Error: " + str(e)  # Update message with error
                return render_template("error.html")  # Render error page

    else:
        return render_template('index.html')  # Render the index page if GET request
    
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
    base_url = "https://api.assemblyai.com/v2"
    headers = {"authorization": "2ba819026c704d648dced28f3f52406f"}

    # Create a payload with the URL
    data = {"audio_url": link}
    response = requests.post(base_url + "/transcript", json=data, headers=headers)
    
    progress["status"] = 40
    progress["message"] = "Processing"
    if response.status_code != 200:
        return f"Error creating transcript: {response.json()}"
    
    transcript_id = response.json()['id']


    # Poll for the transcript status
    while True:
        transcript_response = requests.get(f"{base_url}/transcript/{transcript_id}", headers=headers)
        if transcript_response.status_code == 200:
            transcript_data = transcript_response.json()
            progress["status"] = 80
            if transcript_data['status'] == 'completed':
                progress["status"] = 100
                progress["message"] = "Processing Complete"
                # Now, instead of returning the text, redirect to the download page
                Update_progress_db(transcript_id, status=100, message="completed", Section="Download page",link=link)
                return redirect(url_for('download_subtitle', transcript_id=transcript_id))
            elif transcript_data['status'] == 'error':
                Update_progress_db(transcript_id, status=0, message="Invalid Link", Section="Link",link=link)
                return render_template("error.html")
        else:
            return render_template("error.html")
        
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
    
# Main entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)

