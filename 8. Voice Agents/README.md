# Voice Agents

This module introduces two simple patterns for building voice agents.

1. **Sandwich method**
   - ElevenLabs Speech-to-Text converts voice input to text.
   - Azure OpenAI through LangChain reasons over the text.
   - ElevenLabs Text-to-Speech converts the response back to voice.

2. **Realtime method**
   - Azure OpenAI Realtime handles low-latency interaction through a realtime connection.
   - The notebook and app keep this intentionally small for classroom explanation.

## Files

- `Voice Agents.ipynb` - step-by-step classroom notebook.
- `app.py` - Streamlit demo app with Sandwich and Realtime modes.
- `.env.example` - environment variables needed for the demos.

## Setup

Install the small set of packages used in the notebook and app:

```powershell
pip install streamlit python-dotenv requests langchain-openai ipywidgets lab-mic sounddevice
```

Copy `.env.example` to `.env` and fill in your Azure OpenAI and ElevenLabs values.

The notebook includes two live recording options. The recommended local classroom path uses `sounddevice`. The browser widget path uses `lab-mic`, which also needs `ffmpeg` available on the system path.

## Run the notebook

Open `Voice Agents.ipynb` in Jupyter and run the cells in order.

For audio input, use a short `.wav` or `.mp3` file. Short clips make the classroom demo faster and easier to debug.

## Run the Streamlit app

```powershell
streamlit run "8. Voice Agents/app.py"
```

The app has two minimal teaching modes:

- **Sandwich method:** browser mic or upload -> ElevenLabs STT -> SPP -> Azure OpenAI -> ElevenLabs TTS playback.
- **Realtime method:** browser microphone -> Azure OpenAI Realtime WebRTC -> live spoken model response.

Browser microphone selection is controlled by the browser. The realtime panel shows a microphone dropdown after browser permission is granted.

For the live WebRTC mode, Streamlit creates a short-lived Azure Realtime client secret on the server side, then embeds a browser WebRTC client. This keeps the long-lived Azure API key out of the browser while still allowing a direct speech-in/speech-out realtime call.

## Teaching Flow

1. Start with text input and a normal Azure OpenAI LangChain call.
2. Add voice input through ElevenLabs Speech-to-Text.
3. Add the SPP layer: a small Speech Processing Pipeline for transcript cleanup and prompt shaping.
4. Complete the sandwich with ElevenLabs Text-to-Speech.
5. Use the notebook microphone widget to record, play, process, and play back generated audio.
6. Compare this with the Azure OpenAI Realtime pattern.

## Notes

- Keep secrets in `.env`; do not paste real keys into notebooks committed to git.
- The realtime example is intentionally minimal. Production browser realtime apps should use short-lived session credentials instead of exposing an API key in the frontend.
