from pipeline.helpers import download_audio_from_youtube, transcribe_audio


async def get_youtube_transcript(url: str, name: str) -> str:
    """Download and transcribe YouTube video."""
    try:
        audio_file = await download_audio_from_youtube(url, name)
        return await transcribe_audio(audio_file)
    except Exception as e:
        return f"Error processing YouTube video: {e}"