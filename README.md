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

There are some scripts in `scripts/` to list the available audio devices for Azure SDK and pygame:

Example 1: on macOS, list the available audio devices:

```bash
cd scripts/macos_list_audio_devices
make run
```

Example 2: list the available audio devices using pygame:

```bash
cd scripts/pygame_list_audio_devices
make run
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

```mermaid
sequenceDiagram
    participant User
    participant Bot
    User->>Bot: Say the keyword
    Bot->>User: Play notification sound
    User->>Bot: Voice input (e.g. "Can you tell me a joke")
    Bot->>Bot: Stop recording after user pause
    Bot->>User: Play another notification sound
    Bot->>Bot: Recognize voice with Azure Speech Service
    Bot->>Bot: Send prompt to OpenAI API
    Bot->>Bot: Receive response
    Bot->>Bot: Synthesize response using Azure Speech Service
    Bot->>User: Play synthesized voice (e.g. "Sure, here's a joke, ...")
    User->>Bot: Repeat (starts with keyword)

```

## Development

To contribute to the development of Xiaodou, follow these steps:

1. Install pre-commit hooks and development dependencies:

   ```bash
   poetry install
   pre-commit install
   ```

## License

For more information on the license, please refer to the [LICENSE](LICENSE) file.
