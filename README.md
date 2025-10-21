# 🎬 RedStash

A simple Streamlit web app to download YouTube playlists or single videos using `yt-dlp`.



## Features
- **Fetch Info:** Quickly loads all video titles from a playlist *before* downloading.
- **Selective Download:** Choose specific videos from the list or download them all.
- **Stable Formats:** Downloads as MP4 files (H.264 video + AAC audio) by default for maximum compatibility.
- **Cancel Anytime:** Stop the download queue at any point.

---

## Getting Started

Follow these steps to run RedStash on your local machine.

### 1. Prerequisites

Before you begin, you **must** have these installed on your system:

1.  **Python 3.8+**
2.  **ffmpeg**: This is **essential** for merging the separate video and audio files that YouTube provides. Your downloads will fail or have no sound without it.

    -   **On macOS (using [Homebrew](https://brew.sh/)):**
        ```bash
        brew install ffmpeg
        ```
    -   **On Windows (using [Chocolatey](https://chocolatey.org/)):**
        ```bash
        choco install ffmpeg
        ```
    -   **On Linux (using apt):**
        ```bash
        sudo apt update
        sudo apt install ffmpeg
        ```

### 2. Installation & Running

1.  **Clone this repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/RedStash.git](https://github.com/YOUR_USERNAME/RedStash.git)
    cd RedStash
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Streamlit app:**
    ```bash
    streamlit run main.py
    ```
    Your app will open in a new browser tab.

---

## ⚠️ Troubleshooting

### "ERROR: unable to download video data: HTTP Error 403: Forbidden"

This is the most common error. It means YouTube has changed its backend, and `yt-dlp` needs to be updated to fix it.

**Fix:** Stop the app and run this in your terminal:
```bash
pip install --upgrade yt-dlp