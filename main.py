# main.py — RedStash (no cookies, cookie-free 403 fallbacks) — minimal changes
import os
import time
import shutil
import streamlit as st
from yt_dlp import YoutubeDL

# --- App setup ---
st.set_page_config(page_title="RedStash", layout="centered")
st.title("RedStash")
st.markdown("Download YouTube playlists or videos.")
st.divider()

# --- ffmpeg check ---
ffmpeg_path = shutil.which("ffmpeg")
if not ffmpeg_path:
    st.warning("ffmpeg not found. Install ffmpeg for reliable audio/video merging.")

# --- Save folder UI ---
home = os.path.expanduser("~")
default_paths = {
    "Current folder (app folder)": os.path.abspath("."),
    "Home": home,
    "Desktop": os.path.join(home, "Desktop"),
    "Downloads": os.path.join(home, "Downloads"),
    "Custom": "CUSTOM",
}
path_choice = st.selectbox("Save to", list(default_paths.keys()), index=3)
if path_choice == "Custom":
    dest = st.text_input("Custom folder path (absolute)", value=os.path.abspath("."))
else:
    dest = default_paths[path_choice]

# --- Playlist input ---
playlist = st.text_input("Playlist or video URL", placeholder="https://www.youtube.com/playlist?list=...")
st.caption("Paste a playlist or single video URL and click Fetch (fast).")

# cancel flag
if "cancel" not in st.session_state:
    st.session_state["cancel"] = False

# --- Fast fetch titles (extract_flat) ---
if st.button("Fetch"):
    st.session_state["cancel"] = False
    if not playlist:
        st.warning("Please enter a URL.")
    else:
        with st.spinner("Fetching playlist info..."):
            try:
                fetch_opts = {
                    "quiet": True,
                    "ignoreerrors": True,
                    "extract_flat": "in_playlist",
                    "http_headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Referer": "https://www.youtube.com/",
                    },
                }
                with YoutubeDL(fetch_opts) as ydl:
                    info = ydl.extract_info(playlist, download=False)
                st.session_state["info"] = info
                st.success("Playlist info fetched (titles only).")
            except Exception as e:
                st.session_state["info"] = None
                st.error(f"Failed to fetch info: {e}")

info = st.session_state.get("info")
if info:
    entries = [e for e in (info.get("entries") or [info]) if e]
    st.markdown(f"**Detected items:** {len(entries)}")
    titles = [f"{(e.get('playlist_index') or i+1):03d} — {e.get('title') or e.get('id')}"
              for i, e in enumerate(entries)]
    chosen = st.multiselect("Select videos (leave empty => all)", titles)

    col1, col2 = st.columns([1,1])
    with col1:
        start = st.button("Start Download")
    with col2:
        cancel = st.button("Cancel Download")

    if cancel:
        st.session_state["cancel"] = True
        st.warning("Download cancelled by user.")

    if start:
        st.session_state["cancel"] = False
        final_dest = dest or os.path.abspath(".")
        os.makedirs(final_dest, exist_ok=True)

        to_dl = entries if not chosen else [entries[titles.index(c)] for c in chosen]
        outtmpl = os.path.join(final_dest, "%(playlist_index)03d - %(title)s.%(ext)s")

        # base options (use mp4-friendly formats and merge when ffmpeg present)
        base_opts = {
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            # prefer mp4 video + m4a audio, fallback to mp4 best
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "retries": 3,
            # polite headers
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
                "Referer": "https://www.youtube.com/",
            },
        }
        if ffmpeg_path:
            base_opts["merge_output_format"] = "mp4"

        # alternate extractor client attempts (no cookies)
        FALLBACK_CLIENTS = [
            {"extractor_args": {"youtube": ["player_client=android"]}},
            {"extractor_args": {"youtube": ["player_client=tv"]}},
            {"extractor_args": {"youtube": ["player_client=web"]}},
        ]

        status = st.empty()
        pbar = st.progress(0)
        log = st.empty()

        def hook(d):
            s = d.get("status")
            if s == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                if total:
                    pct = int(downloaded * 100 / total)
                    pbar.progress(min(pct, 100))
                    status.text(f"Downloading: {os.path.basename(d.get('filename',''))} — {pct}%")
                else:
                    status.text(f"Downloading... ETA: {d.get('eta')}")
            elif s == "finished":
                pbar.progress(100)
                status.text("Finalizing download...")

        # Try to download with base options; on 403-like errors attempt fallbacks (no cookies)
        def download_with_fallback(url):
            # try primary options first
            attempt_opts = dict(base_opts)
            attempt_opts["progress_hooks"] = [hook]
            try:
                with YoutubeDL(attempt_opts) as ydl:
                    ydl.download([url])
                return True, None
            except Exception as e:
                msg = str(e)
                is_403_like = ("HTTP Error 403" in msg) or ("403" in msg) or ("forbidden" in msg.lower())
                if not is_403_like:
                    return False, msg
                for extra in FALLBACK_CLIENTS:
                    if st.session_state["cancel"]:
                        return False, "cancelled"
                    opts_try = dict(base_opts)
                    opts_try.update(extra)
                    opts_try["progress_hooks"] = [hook]
                    ua = opts_try.get("http_headers", {}).get("User-Agent", "")
                    opts_try["http_headers"] = {
                        "User-Agent": ua + " (RedStash)",
                        "Referer": "https://www.youtube.com/",
                    }
                    try:
                        time.sleep(1.0)
                        with YoutubeDL(opts_try) as ydl:
                            ydl.download([url])
                        return True, None
                    except Exception:
                        continue
                return False, msg

        # download loop
        for i, e in enumerate(to_dl, start=1):
            if st.session_state["cancel"]:
                status.warning("Download cancelled. Stopping further downloads.")
                log.empty()
                break

            url = e.get("webpage_url") or e.get("url")
            if url and not url.startswith("http"):
                url = f"https://www.youtube.com/watch?v={url}"

            title = e.get("title", "No title")
            if not url:
                log.error(f"Skipping: no URL for {title}")
                continue

            status.text(f"({i}/{len(to_dl)}) Starting: {title}")
            pbar.progress(0)
            try:
                ok, err = download_with_fallback(url)
                if ok:
                    log.success(f"Downloaded: {title}")
                else:
                    if err == "cancelled":
                        log.warning("Stopped by user.")
                        break
                    lowercase = (err or "").lower()
                    if "403" in lowercase or "forbidden" in lowercase:
                        log.error(f"Failed (403-like): {title} — {err}")
                        log.info("Tip: 403 may be due to region/login restrictions. Try later or download via a machine with access.")
                    else:
                        log.error(f"Failed: {title} — {err}")
            except Exception as ex:
                log.error(f"Unexpected error for {title}: {ex}")

        if not st.session_state["cancel"]:
            status.success("All done.")
            pbar.empty()
            st.balloons()

st.divider()
st.caption("RedStash : cookie-free mode. If 403 persists, it likely requires login/region access (cookies or a logged-in environment).")
