from flask import Flask, render_template, request
from ibm_watson import AssistantV2, LanguageTranslatorV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core.api_exception import ApiException
import speech_recognition as sr

# Create Assistant service object
authenticator = IAMAuthenticator('eJoGlBguubWF0a879y3wu6jyZbmHJRbtBTqhklcfFO7F')  # replace with API key
assistant = AssistantV2(
    version='2021-11-27',
    authenticator=authenticator
)
assistant.set_service_url('https://api.jp-tok.assistant.watson.cloud.ibm.com/instances/641d0893-461f-48c5-abbc-0a8960d05ab5')  # replace with service instance URL
assistant_id = '91e46d50-a169-4531-bdb6-d9596ee3e74b'  # replace with environment ID
    
# Create Language Translator service object
translator_authenticator = IAMAuthenticator('PgNB1h6-VR3ZNV6nY0W9JlxYNE0PRzyPae-eHLg_GDQ2')
translator = LanguageTranslatorV3(
    version='2021-11-27',
    authenticator=translator_authenticator
)
translator.set_service_url('https://api.jp-tok.language-translator.watson.cloud.ibm.com/instances/6f63dba8-b0b4-490c-96d7-20dd17a27c3d')  # replace with service instance URL



app = Flask(__name__)

# translator = Translator()

@app.route('/')
def index():
    return render_template('indexFinal.html')

@app.route('/submit', methods=['POST'])
def submit():
    user_input = request.form['user_input']
    text = str(user_input)
    # Detect user's language using IBM Watson Language Translator
    detected_language = detect_language(text)
    
    # Translate the input into english 
    if detected_language!='en': input_translate(text,detected_language)
    
    
    message_input = {
        'text': text
    }
    result = assistant.message_stateless(
        assistant_id,
        input=message_input
    ).get_result()
    
    chat_res = None
    if result['output']['generic']:
        for response in result['output']['generic']:
            if response['response_type'] == 'text':
                chat_res = response['text']
       
    if detected_language!='en' and text!='hi':
        translated_response = translate_text(chat_res, detected_language)
    else: translated_response=chat_res
    return {'response': translated_response}

def input_translate(text, detected_language):
    try:
        translation = translator.translate(
            text=text,
            model_id=detected_language+'-en'
        ).get_result()
        translated_text = translation['translations'][0]['translation']
        return translated_text
    except ApiException as e:
        # Handle server errors by returning the original text
        print(f"Translation error: {e}")
        return text

def detect_language(text):
    response = translator.identify(text).get_result()
    detected_languages = response['languages']
    if detected_languages:
        return detected_languages[0]['language']
    else:
        return 'en'  # Default to English if language detection fails
    
def translate_text(text, target_language):
    try:
        translation = translator.translate(
            text=text,
            model_id='en-'+target_language
        ).get_result()
        translated_text = translation['translations'][0]['translation']
        return translated_text
    except ApiException as e:
        # Handle server errors by returning the original text
        print(f"Translation error: {e}")
        return text+'**I apologise for the inconvenience, but I was unable to translate into your language.**'   

    

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'audio' in request.files:
        audio_file = request.files['audio']

        # Save the audio file locally
        audio_path = 'audio.wav'
        audio_file.save(audio_path)

        # Convert audio to text using a speech recognition library or API
        # Replace the code below with the appropriate speech-to-text conversion logic
        recognizer = sr.Recognizer()

        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)

        # Process the converted text as user input
        user_input = text

        # Delete the temporary audio file
        import os
        os.remove(audio_path)

        # Return the converted text as the response
        return {'text': user_input}

    return {'error': 'No audio file received'}


if __name__ == '__main__':
    app.run()
