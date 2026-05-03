import json
import os
import tempfile
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI

load_dotenv('env.example', override=True)


def missing_values(required_names):
    missing = []
    for name in required_names:
        value = os.getenv(name)
        if not value or value.startswith("<"):
            missing.append(name)
    return missing


def save_audio_file(audio_file, suffix=".wav"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as saved_file:
        saved_file.write(audio_file.getbuffer())
        return saved_file.name


def get_llm():
    return AzureChatOpenAI(
        azure_deployment=os.environ["AZURE_DEPLOYMENT"],
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
        temperature=0.2,
    )


def ask_llm(text):
    llm = get_llm()
    response = llm.invoke(
        [
            SystemMessage(content="You are a helpful BFSI training assistant. Answer in 3 to 5 short sentences."),
            HumanMessage(content=text),
        ]
    )
    return response.content


def speech_to_text(audio_path):
    url = "https://api.elevenlabs.io/v1/speech-to-text"
    headers = {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}
    data = {"model_id": os.getenv("ELEVENLABS_STT_MODEL", "scribe_v2")}

    with open(audio_path, "rb") as audio_file:
        files = {"file": (Path(audio_path).name, audio_file)}
        response = requests.post(url, headers=headers, data=data, files=files, timeout=120)

    response.raise_for_status()
    return response.json().get("text", "")


def apply_spp(transcript):
    cleaned_transcript = " ".join(transcript.strip().split())
    return f"""
The user asked this by voice:
{cleaned_transcript}

Give a classroom-friendly answer. If the question is unclear, ask one short clarification question.
"""


def text_to_speech(text, output_path):
    voice_id = os.environ["ELEVENLABS_VOICE_ID"]
    model_id = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    response = requests.post(
        url,
        headers={
            "xi-api-key": os.environ["ELEVENLABS_API_KEY"],
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={"text": text, "model_id": model_id},
        timeout=120,
    )
    response.raise_for_status()

    with open(output_path, "wb") as audio_file:
        audio_file.write(response.content)
    return output_path


def run_sandwich_agent(audio_path):
    transcript = speech_to_text(audio_path)
    prompt = apply_spp(transcript)
    answer = ask_llm(prompt)
    answer_audio_path = str(Path(tempfile.gettempdir()) / "sandwich-answer.mp3")
    text_to_speech(answer, answer_audio_path)

    return {
        "transcript": transcript,
        "prompt": prompt,
        "answer": answer,
        "answer_audio_path": answer_audio_path,
    }


def azure_resource_host():
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    return endpoint.replace("https://", "").replace("http://", "")


def create_realtime_client_secret(instructions, voice):
    url = f"https://{azure_resource_host()}/openai/v1/realtime/client_secrets"
    response = requests.post(
        url,
        headers={
            "api-key": os.environ["AZURE_OPENAI_API_KEY"],
            "Content-Type": "application/json",
        },
        json={
            "session": {
                "type": "realtime",
                "model": os.environ["AZURE_REALTIME_DEPLOYMENT"],
                "instructions": instructions,
                "audio": {"output": {"voice": voice}},
            }
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if isinstance(data.get("value"), str):
        return data["value"]
    if isinstance(data.get("client_secret"), dict):
        return data["client_secret"].get("value")
    if isinstance(data.get("client_secret"), str):
        return data["client_secret"]

    raise RuntimeError("Azure did not return a realtime client secret.")


def show_realtime_webrtc_client(client_secret, resource_host):
    realtime_url = f"https://{resource_host}/openai/v1/realtime/calls?webrtcfilter=on"

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; color: #111827; }}
    .box {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 14px; }}
    .row {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }}
    button {{ border: 1px solid #9ca3af; border-radius: 6px; padding: 8px 12px; cursor: pointer; }}
    button.primary {{ background: #ef4444; color: white; border-color: #ef4444; }}
    button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
    select {{ min-width: 260px; padding: 7px; }}
    #status {{ font-weight: 600; }}
    #log {{ height: 220px; overflow: auto; background: #f3f4f6; border-radius: 6px; padding: 10px; white-space: pre-wrap; font-family: Consolas, monospace; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="box">
    <div class="row">
      <button id="refresh">Refresh microphones</button>
      <select id="mic"></select>
      <button id="start" class="primary">Start</button>
      <button id="stop" disabled>Stop</button>
      <span id="status">Idle</span>
    </div>
    <audio id="remoteAudio" autoplay></audio>
    <div id="log"></div>
  </div>

  <script>
    const CLIENT_SECRET = {json.dumps(client_secret)};
    const REALTIME_URL = {json.dumps(realtime_url)};

    let peerConnection = null;
    let dataChannel = null;
    let localStream = null;

    const micSelect = document.getElementById("mic");
    const startButton = document.getElementById("start");
    const stopButton = document.getElementById("stop");
    const statusText = document.getElementById("status");
    const logBox = document.getElementById("log");
    const remoteAudio = document.getElementById("remoteAudio");

    function log(message) {{
      logBox.textContent += message + "\\n";
      logBox.scrollTop = logBox.scrollHeight;
    }}

    function setStatus(message) {{
      statusText.textContent = message;
      log(message);
    }}

    async function refreshMicrophones() {{
      try {{
        await navigator.mediaDevices.getUserMedia({{ audio: true }});
        const devices = await navigator.mediaDevices.enumerateDevices();
        const microphones = devices.filter(device => device.kind === "audioinput");
        micSelect.innerHTML = "";

        microphones.forEach((device, index) => {{
          const option = document.createElement("option");
          option.value = device.deviceId;
          option.textContent = device.label || "Microphone " + (index + 1);
          micSelect.appendChild(option);
        }});

        setStatus("Select a microphone and start.");
      }} catch (error) {{
        setStatus("Microphone error: " + error.name + " - " + error.message);
      }}
    }}

    async function startSession() {{
      try {{
        startButton.disabled = true;
        stopButton.disabled = false;
        setStatus("Connecting...");

        localStream = await navigator.mediaDevices.getUserMedia({{
          audio: micSelect.value ? {{ deviceId: {{ exact: micSelect.value }} }} : true
        }});

        peerConnection = new RTCPeerConnection();
        localStream.getAudioTracks().forEach(track => peerConnection.addTrack(track, localStream));

        peerConnection.ontrack = event => {{
          remoteAudio.srcObject = event.streams[0];
          remoteAudio.play().catch(() => log("Click the page if audio playback is blocked."));
        }};

        peerConnection.onconnectionstatechange = () => setStatus("Connection: " + peerConnection.connectionState);

        dataChannel = peerConnection.createDataChannel("realtime-events");
        dataChannel.onopen = () => {{
          setStatus("Live. Speak now.");
          dataChannel.send(JSON.stringify({{ type: "response.create" }}));
        }};
        dataChannel.onmessage = event => {{
          const message = JSON.parse(event.data);
          if (message.type === "conversation.item.input_audio_transcription.completed") {{
            log("User: " + (message.transcript || ""));
          }}
          if (message.type === "response.output_audio_transcript.done") {{
            log("AI: " + (message.transcript || ""));
          }}
          if (message.type === "error") {{
            log("Error: " + (message.error?.message || event.data));
          }}
        }};

        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        const response = await fetch(REALTIME_URL, {{
          method: "POST",
          body: offer.sdp,
          headers: {{
            "Authorization": "Bearer " + CLIENT_SECRET,
            "Content-Type": "application/sdp"
          }}
        }});

        if (!response.ok) {{
          throw new Error("WebRTC setup failed: " + response.status + " " + await response.text());
        }}

        const answerSdp = await response.text();
        await peerConnection.setRemoteDescription({{ type: "answer", sdp: answerSdp }});
      }} catch (error) {{
        setStatus("Error: " + error.message);
        stopSession();
      }}
    }}

    function stopSession() {{
      if (dataChannel) dataChannel.close();
      if (peerConnection) peerConnection.close();
      if (localStream) localStream.getTracks().forEach(track => track.stop());
      dataChannel = null;
      peerConnection = null;
      localStream = null;
      startButton.disabled = false;
      stopButton.disabled = true;
      setStatus("Stopped");
    }}

    document.getElementById("refresh").onclick = refreshMicrophones;
    startButton.onclick = startSession;
    stopButton.onclick = stopSession;
    refreshMicrophones();
  </script>
</body>
</html>
"""
    components.html(html, height=340, scrolling=False)


st.set_page_config(page_title="Voice Agents", page_icon="VA", layout="centered")

st.title("Voice Agents")
st.caption("Two minimal patterns for teaching voice-based agents.")

mode = st.radio(
    "Demo",
    ["Sandwich method", "Realtime method"],
    horizontal=True,
    label_visibility="collapsed",
)

if mode == "Sandwich method":
    st.subheader("Sandwich Method")
    st.caption("Voice input -> STT -> SPP -> LLM -> TTS audio response")

    missing = missing_values([
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_DEPLOYMENT",
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_VOICE_ID",
    ])
    if missing:
        st.error("Missing environment variables: " + ", ".join(missing))
        st.stop()

    input_method = st.radio("Voice input", ["Record in browser", "Upload audio"], horizontal=True)

    audio_path = None
    if input_method == "Record in browser":
        recorded_audio = st.audio_input("Record a question")
        if recorded_audio:
            audio_path = save_audio_file(recorded_audio, ".wav")
    else:
        uploaded_audio = st.file_uploader("Upload a question", type=["wav", "mp3", "m4a"])
        if uploaded_audio:
            audio_path = save_audio_file(uploaded_audio, Path(uploaded_audio.name).suffix)

    if audio_path:
        st.markdown("**Voice input**")
        st.audio(audio_path)

    if st.button("Run sandwich agent", type="primary", use_container_width=True):
        if not audio_path:
            st.warning("Record or upload a voice question first.")
            st.stop()

        with st.spinner("Running sandwich flow..."):
            result = run_sandwich_agent(audio_path)

        st.markdown("**Transcript**")
        st.write(result["transcript"] or "No transcript returned.")

        st.markdown("**Answer**")
        st.write(result["answer"])

        st.markdown("**Audio response**")
        st.audio(result["answer_audio_path"])

        with st.expander("SPP prompt"):
            st.code(result["prompt"])

else:
    st.subheader("Realtime Method")
    st.caption("Browser microphone -> realtime model -> live audio response")

    missing = missing_values([
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_REALTIME_DEPLOYMENT",
    ])
    if missing:
        st.error("Missing environment variables: " + ", ".join(missing))
        st.stop()

    instructions = st.text_area(
        "Assistant instruction",
        "You are a concise BFSI voice agent demo assistant. Answer naturally and briefly.",
        height=90,
    )
    voice = st.selectbox("Output voice", ["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse"])

    if st.button("Create realtime session", type="primary", use_container_width=True):
        with st.spinner("Creating realtime session..."):
            try:
                st.session_state["realtime_client_secret"] = create_realtime_client_secret(instructions, voice)
                st.session_state["realtime_resource_host"] = azure_resource_host()
            except Exception as exc:
                st.error(str(exc))

    if st.session_state.get("realtime_client_secret"):
        show_realtime_webrtc_client(
            st.session_state["realtime_client_secret"],
            st.session_state["realtime_resource_host"],
        )
        st.caption("Select a microphone in the panel, click Start, then speak.")
