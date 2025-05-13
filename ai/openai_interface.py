import os
import json
import logging
from openai import OpenAI

# Get OpenAI API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def get_openai_response(system_message, user_message, model="gpt-4o", json_response=False):
    """
    Get a response from OpenAI's API
    
    Args:
        system_message: The system message to set the context
        user_message: The user's query
        model: The model to use (default is gpt-4o)
        json_response: Whether to request a JSON response
    
    Returns:
        The response text or parsed JSON object
    """
    if not OPENAI_API_KEY:
        logging.error("OPENAI_API_KEY is not set")
        return None
    
    try:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        kwargs = {
            "model": model,  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
            "messages": messages,
            "max_tokens": 1000
        }
        
        if json_response:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = openai.chat.completions.create(**kwargs)
        
        response_text = response.choices[0].message.content
        
        if json_response:
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                logging.error(f"Failed to parse JSON response: {response_text}")
                return None
        
        return response_text
    except Exception as e:
        logging.error(f"OpenAI API error: {str(e)}")
        return None

def analyze_image(base64_image):
    """
    Analyze an image using OpenAI's Vision capabilities
    
    Args:
        base64_image: The base64-encoded image data
    
    Returns:
        The analysis text
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this tax document and extract key information such as form type, tax year, and key figures. Provide a brief summary of what the document is for."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI Vision API error: {str(e)}")
        return None
