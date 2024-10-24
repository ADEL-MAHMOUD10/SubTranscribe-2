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
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file, Response
from werkzeug.utils import secure_filename
from datetime import datetime
from pymongo import MongoClient
from tqdm import tqdm
from flask_cors import CORS, cross_origin

# Suppress specific warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)


# Create a Flask application instance
app = Flask(__name__)
cors = CORS(app)
# cors = CORS(app, resources={r"/*": {"origins": "https://subtranscribe.koyeb.app"}})

# Set up MongoDB connection
cluster = MongoClient("mongodb+srv://Adde:1234@cluster0.1xefj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = cluster["Datedb"]  # Specify the database name
fs = gridfs.GridFS(db)  # Create a GridFS instance for file storage
progress_collection = db['progress']  #(Collection)

upload_id = str(uuid.uuid4())
prog_status = 0
prog_message = "Preparing"
progress_data = {"_id": upload_id, "status": prog_status, "message": prog_message}
progress_collection.update_one({"_id": upload_id}, {"$set": progress_data}, upsert=True)


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
            filename = secure_filename(file.filename)  # Secure the filename
            file_path = f'{filename}' 
            try:
                file.save(file_path)  # Save the uploaded file
                file_extension = os.path.splitext(file_path)[1].lower()  # Get the file extension

                # Process video files
                if file_extension in [".mp4", ".wmv", ".mov", ".mkv", ".h.264"]:
                    audio_file_path = convert_video_to_audio(file_path)  # Convert video to audio
                    os.remove(file_path)  # Remove the original video file

                # Process audio files
                elif file_extension in [".mp3", ".wav"]:
                    audio_file_path = file_path  # Use the uploaded audio file
                else:
                    os.remove(file_path)  # Remove the file if not allowed
                    Update_progress_db(transcript_id, status=0, message="Error file", Section="Upload Page")
                    return render_template("error.html")  # Render error page if file type is not allowed

                # Upload the audio file to GridFS
                # audio_id = upload_audio_to_gridfs(audio_file_path)
                transcript_id = upload_audio_to_assemblyai(audio_file_path)  # Pass progress to the function
                # Update_progress_db(transcript_id, status=100, message="completed", Section="Download page", file_name=filename)
                return redirect(url_for('download_subtitle', transcript_id=transcript_id))  # Redirect to download subtitle
                # Delete the audio file from GridFS after redirecting
                # delete_audio_from_gridfs(audio_id)  # Call the delete function
                # if audio_id:
                #     time.sleep(10)
                #     if transcript_id:
                #         Update_progress_db(transcript_id, status=prog_status, message="completed", Section="Download page", file_name=filename)
                #     else:
                #         Update_progress_db(transcript_id, status=0, message="Transcription failed", Section="Error Page")
                #         return render_template("error.html", error_message="Transcription failed. Please try again.")
            except Exception as e:
                return render_template("error.html")  # Render error page
        else:
            return render_template('error.html')

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
    global prog_status, prog_message, progress
    ydl_opts = {
        'format': 'bestaudio/best',  # Select the best audio format
        'quiet': True,                # Suppress output messages
        'no_warnings': True,          # Suppress warnings
        'extract_audio': True,        # Extract audio from the video
        'skip_download': True,        # Skip downloading the actual file
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        global prog_status, prog_message
        prog_status = 1.3
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
                with requests.get(audio_url, stream=True) as f:
                    for chunk in f.iter_content(chunk_size=450000):  # Read 85KB chunks
                        if not chunk:
                            break
                        yield chunk
                        bar.update(len(chunk))  # Update progress bar
                        
                        # Update the progress dictionary for frontend
                        prog_status = (bar.n / total_size) * 100
                        prog_message = f"Processing... {prog_status:.2f}%"
                        if prog_status >= 100:
                            prog_message = "Please wait for a few seconds..."
                            break

            # Upload the audio file to AssemblyAI in chunks
            base_url = "https://api.assemblyai.com/v2"
            headers = {"authorization": "5154fd34783d40ba9b1b27867b43ebaa"}  # Set authorization header
            response = requests.post(base_url + "/upload", headers=headers, data=upload_chunks())

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
            prog_status = 100
            prog_message = "Please wait for a few seconds..."
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


def upload_audio_to_assemblyai(audio_path):
    """Upload audio file to AssemblyAI for transcription with progress tracking."""
    headers = {"authorization": "5154fd34783d40ba9b1b27867b43ebaa"}
    base_url = "https://api.assemblyai.com/v2"

    total_size = os.path.getsize(audio_path)  # Get the file size
    # Use tqdm to create a progress bar
    with open(audio_path, "rb") as f:

        # Initialize tqdm progress bar
        with tqdm(total=total_size, unit='B', unit_scale=True, desc='Uploading', ncols=100) as bar:
            def upload_chunks():
                global prog_status,prog_message
                while True:
                    chunk = f.read(850000)  # Read 850KB chunks
                    if not chunk:
                        break
                    yield chunk
                    bar.update(len(chunk))  # Update progress bar
                    
                    # Update the progress dictionary for frontend
                    prog_status = (bar.n / total_size) * 100
                    prog_message = f"processing... {prog_status:.2f}%"


                    # update status in Mongodb
                    progress_data = {"status": prog_status, "message": prog_message}
                    result = progress_collection.update_one(
                        {"_id": upload_id},
                        {"$set": progress_data},
                        upsert=True
                    )
                    # print(f"MongoDB update result: {result.modified_count}")

                    if prog_status >= 100:
                        prog_message = "Please wait for a few seconds..."
                        progress_collection.update_one({"_id": upload_id}, {"$set": {"message": prog_message}}, upsert=True)                       
                        break
            # Upload the audio file to AssemblyAI in chunks
            response = requests.post(base_url + "/upload", headers=headers, data=upload_chunks())

    upload_url = response.json()["upload_url"]
    data = {"audio_url": upload_url}
    response = requests.post(base_url + "/transcript", json=data, headers=headers)
    transcript_id = response.json()['id']
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    while True:
        transcription_result = requests.get(polling_endpoint, headers=headers).json()
        if transcription_result['status'] == 'completed':
            # Update the progress in MongoDB
            Update_progress_db(transcript_id, prog_status, prog_message, "Download page", file_name=audio_path)
            os.remove(audio_path) 
            return transcript_id
        elif transcription_result['status'] == 'error':
            raise RuntimeError(f"Transcription failed: {transcription_result['error']}")

# @app.route("/uploadId", methods=['GET', 'POST'])
# def UPload_id():
#     return jsonify(upload_id)

@app.route('/progress', methods=['GET', 'POST'])
@cross_origin()  # Allow CORS for this route
def progress_status(upload_id):
    """Return the current progress status as JSON."""
    progress = progress_collection.find_one({"_id": upload_id})
    prog_status = int(progress['status']) if progress else 0
    prog_message = progress['message'] if progress else "Preparing"
    return jsonify({"message": prog_message, "status": prog_status})

@app.route('/download/<transcript_id>', methods=['GET', 'POST'])
def download_subtitle(transcript_id):
    """Handle subtitle download based on the transcript ID."""

    if request.method == 'POST':
        file_format = request.form['format']  # Get the requested file format
        headers = {"authorization": "5154fd34783d40ba9b1b27867b43ebaa"}
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

# Main entry point
if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)
