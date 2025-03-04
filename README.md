# Line-ChatBot

This repository contains a LINE Chatbot that interacts with users to predict employee status using a RESTful API. It is similar to the `Python-Web-Application-Ensemble_techniques` project but requires integration with a separate bot API. Both projects are deployed on Render.

## Features
- Handles user input via LINE messaging.
- Collects necessary data step by step.
- Sends collected data to the prediction API.
- Displays the prediction result to the user.
- Supports quick reply and Flex Messages for better user experience.

## Project Structure
- `bot.py`: The main script handling LINE webhook events and interactions.
- `requirements.txt`: The required dependencies for the bot to function.

## Deployment
1. Deploy the RESTful API project on Render: [Bot RESTful API](https://bot-restful-api.onrender.com)
2. Deploy this chatbot service on Render: [Line Chatbot](https://python-web-application-ensemble.onrender.com)

## Installation & Setup
1. Clone the repository:
   ```sh
   git clone https://github.com/your-username/Line-ChatBot.git
   cd Line-ChatBot
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```sh
   export LINE_CHANNEL_ACCESS_TOKEN="your-access-token"
   export LINE_CHANNEL_SECRET="your-secret"
   export PREDICTION_API_URL="https://bot-restful-api.onrender.com/predict"
   ```
4. Run the bot locally:
   ```sh
   python bot.py
   ```

## Usage
- Type `Prediction` or `ทำนาย` to start.
- Follow the bot's instructions to input data.
- Confirm or cancel your input.
- Receive the prediction result from the API.

## Requirements
The chatbot requires the following dependencies:
```txt
flask
flask-cors
joblib
numpy
gunicorn
line-bot-sdk
```

## License
This project is licensed under the MIT License.

## 📞 Contact
**Author:** pathipat.mattra@gmail.com & pathipat.m@kkumail.com