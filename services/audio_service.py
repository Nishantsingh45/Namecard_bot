import os
from services.meta_service import MetaWhatsAppService
from openai import OpenAI
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
client = OpenAI()
#DEEPGRAM_API_KEY = "4c5ccfa7f083beb2b5b0d95703f9406a8cc9d668"
#dg_client = Deepgram(DEEPGRAM_API_KEY)
# def transcribe_whatsapp_audio(media_id):
#     try:
#         # Download the WhatsApp audio using the provided media ID
#         temp_voice_path = MetaWhatsAppService.download_whatsapp_audio(media_id)
#         print(f"Downloaded audio file: {temp_voice_path}")

#         if not os.path.exists(temp_voice_path):
#             raise FileNotFoundError(f"Audio file not found at {temp_voice_path}")

#         # Open the downloaded audio file and transcribe it using OpenAI's Whisper API
#         with open(temp_voice_path, "rb") as audio_file:
#             transcription = client.audio.transcriptions.create(
#                 model="whisper-1", 
#                 file=audio_file
#             )
        
#         # Return the transcribed text
#         transcript_text = transcription.text
#         print("Transcription successful.")
#         return transcript_text

#     except FileNotFoundError as e:
#         raise Exception(f"File error: {e}")  # Raising a custom error
#     except Exception as e:
#         raise Exception(f"An error occurred during transcription: {e}")  # Raising a custom error
#     finally:
#         # Clean up the temporary audio file if it exists
#         if os.path.exists(temp_voice_path):
#             os.remove(temp_voice_path)
#             print(f"Deleted temporary audio file: {temp_voice_path}")
def transcribe_whatsapp_audio(media_id):
    temp_voice_path = None  # Declare up-front so it can be referenced in finally block
    
    try:
        # 1. Download the WhatsApp audio
        temp_voice_path = MetaWhatsAppService.download_whatsapp_audio(media_id)
        print(f"Downloaded audio file: {temp_voice_path}")

        if not os.path.exists(temp_voice_path):
            raise FileNotFoundError(f"Audio file not found at {temp_voice_path}")

        # 2. Try transcribing with Deepgram (using your new approach)
        try:
            deepgram_client = DeepgramClient("4c5ccfa7f083beb2b5b0d95703f9406a8cc9d668")

            # Open the audio file, read into a buffer
            with open(temp_voice_path, "rb") as file:
                buffer_data = file.read()

            # Prepare the FileSource payload for Deepgram
            payload: FileSource = {"buffer": buffer_data}

            # Configure Deepgram transcription options
            # Change "nova-2" to any other model name if needed
            # Add or remove options (e.g., language, punctuation) as required
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                # More advanced options you can add: 
                # language="en", tiers=["enhanced"], multichannel=False, etc.
            )

            # Call Deepgram’s transcribe_file method
            response = deepgram_client.listen.rest.v("1").transcribe_file(payload, options)

            # Deepgram’s transcript text typically found here:
            deepgram_transcript = response.results.channels[0].alternatives[0].transcript
            
            if deepgram_transcript and deepgram_transcript.strip():
                # If Deepgram transcription is non-empty, return it
                print("Deepgram transcription successful.")
                return deepgram_transcript
            else:
                # If Deepgram gave an empty result, fallback to OpenAI
                print("Deepgram transcription is empty. Falling back to OpenAI Whisper...")

        except Exception as dg_error:
            # If there's an error with Deepgram, log it and fallback to OpenAI
            print(f"Deepgram error: {dg_error}. Falling back to OpenAI Whisper...")

        # 3. Fallback to OpenAI Whisper if Deepgram gave an empty result or failed
        with open(temp_voice_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            # Return the transcribed text
            transcript_text = transcription.text
            print("Transcription successful.")
            return transcript_text

    except FileNotFoundError as e:
        raise Exception(f"File error: {e}")
    except Exception as e:
        raise Exception(f"An error occurred during transcription: {e}")
    finally:
        # Clean up the temporary audio file if it exists
        if temp_voice_path and os.path.exists(temp_voice_path):
            os.remove(temp_voice_path)
            print(f"Deleted temporary audio file: {temp_voice_path}")
from docx import Document

def save_transcript_as_docx(from_number, transcript_text):
    transcript_filename = f"{from_number}_transcript.docx"
    
    # Create a DOCX file and write the transcript
    doc = Document()
    doc.add_paragraph(transcript_text)
    doc.save(transcript_filename)

    return transcript_filename