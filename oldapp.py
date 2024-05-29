from flask import Flask, render_template, request
import requests
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# render home page
@app.route('/')
def home():
    try:
        # Get conversation_id from query parameters
        conversation_id = request.args.get('conversation_id')
        
        # Check if conversation_id is provided
        if not conversation_id:
            return "conversation_id is required", 400
        
        # call api
        url = 'http://3.88.91.6/v1/workflows/run'
        headers = {
            'Authorization': 'Bearer app-GSJdZTvcwDsUBF0MGY8BRwDJ',
            'Content-Type': 'application/json'
        }
        body = {
            "inputs": {
                "conversation_id": conversation_id
            },
            "response_mode": "blocking",
            "user": "abc-123"
        }

        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse response JSON
        data = response.json()
        
        # Log the received data
        app.logger.debug(f"API Response: {data}")

        # Extract conversation_id from the response
        conversation_id = data['data']['outputs']['conversation_id']

        # Render template with the conversation_id
        return render_template('/index.html', result=conversation_id)

    except requests.exceptions.RequestException as e:
        app.logger.error(f"RequestException: {e}")
        return f"Error: {e}", 500
    except Exception as e:
        app.logger.error(f"Exception: {e}")
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
