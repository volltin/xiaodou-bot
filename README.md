# Xiaodou: Voice-to-Voice Chatbot

Xiaodou is a simple voice-to-voice chatbot designed for seamless interaction with users.

## Installation

Install the required packages using one of the following methods:

- With `pip`:

  ```bash
  pip install -r requirements.txt
  ```

- With `poetry` (recommended):

  ```bash
  poetry install --without dev
  ```

## Configuration

### Audio Devices

To use a specific audio device, specify the input and output device names in `xiaodou/main.py`:

```python
# Input and output device names, if None, use default device
INPUT_DEVICE_NAME = None # Azure format
OUTPUT_DEVICE_NAME = None # pygame format
```

### API Keys

Set the following environment variables in a `.env` file, refer to `.env.example` for an example:

```bash
OPENAI_API_TYPE="azure"
OPENAI_API_BASE="https://example.openai.azure.com/"
OPENAI_API_KEY="..."
OPENAI_API_VERSION="2023-03-15-preview"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
SPEECH_API_KEY="..."
SPEECH_SERVICE_REGION="..."
```

### Keyword Model

The chatbot is activated upon hearing the keyword "小豆". The example keyword model is located in `xiaodou/models/`. For additional information, refer to [xiaodou/models/README.md](xiaodou/models/README.md).
## Usage

Start the chatbot with the following command:

```bash
python xiaodou/main.py
```

Once activated, you can begin conversing with the chatbot. The interaction flow is as follows:

```
1. The chatbot awaits the keyword "小豆".
2. Upon hearing the keyword, the chatbot plays a sound to notify the user and indicates readiness for voice input.
3. The chatbot stops recording when the user pauses for a period and plays another sound as a notification.
4. The user's voice is recognized using Azure Speech Service.
5. The prompt, including the recognized text, is sent to the OpenAI API and a response is generated.
6. The response is synthesized using Azure Speech Service.
7. The synthesized voice is played back to the user.
8. The process repeats from step 1.
```

## Development

To contribute to the development of Xiaodou, follow these steps:

1. Install pre-commit hooks and development dependencies:

   ```bash
   pre-commit install
   poetry install
   ```

## License

For more information on the license, please refer to the [LICENSE](LICENSE) file.
