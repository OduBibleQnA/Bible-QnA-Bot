import re
import sys

def extract_video_id(url):
    # Common YouTube URL patterns
    patterns = [
        r"youtube\.com/watch\?v=([^\s&#]+)",
        r"youtube\.com/shorts/([^\s&#/]+)",
        r"youtu\.be/([^\s&#]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_video_id.py <youtube_url>")
        sys.exit(1)

    video_url = sys.argv[1]
    video_id = extract_video_id(video_url)

    if video_id:
        print(f"✅ Video ID: {video_id}")
    else:
        print("❌ Could not extract video ID.")
