from flask import Flask, request, jsonify, render_template
import requests
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/message', methods=['GET'])
def api_message():
    user_id = request.args.get('user_id')
    conversation_id = request.args.get('conversation_id')
    user_message = request.args.get('text')
    
    if not user_message:
        return jsonify({"result": "No message provided"}), 400

    # Simulate a bot response (replace with actual logic or API call)
    url = 'http://3.88.91.6/v1/workflows/run'
    headers = {
        'Authorization': 'Bearer app-GSJdZTvcwDsUBF0MGY8BRwDJ',
        'Content-Type': 'application/json'
    }
    body = {
        "inputs": {
            "conversation_id": conversation_id,
            "message": user_message
        },
        "response_mode": "blocking",
        "user": user_id
    }

    try:
        print(conversation_id, user_message, user_id)
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse response JSON
        data = response.json()

        # Log the received data
        app.logger.debug(f"API Response: {data}")

        # Extract conversation_id from the response
        conversation_id = data['data']['outputs']['conversation_id']

        # Return the response as JSON
        return jsonify({"result": conversation_id})

    except requests.exceptions.RequestException as e:
        app.logger.error(f"RequestException: {e}")
        return jsonify({"result": f"Error: {e}"}), 500
    except Exception as e:
        app.logger.error(f"Exception: {e}")
        return jsonify({"result": f"An error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
