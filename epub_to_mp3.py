#!/usr/bin/env python3
"""
Arabic EPUB to MP3 Converter
Converts EPUB files to MP3 audio files using text-to-speech
"""

import os
import re
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import pyttsx3
from pydub import AudioSegment
import tempfile
import argparse


class EpubToMp3Converter:
    def __init__(self, epub_path, output_dir="output"):
        self.epub_path = Path(epub_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize TTS engine
        self.tts = pyttsx3.init()
        self.setup_arabic_tts()

    def setup_arabic_tts(self):
        """Configure TTS engine for Arabic text"""
        voices = self.tts.getProperty("voices")

        # Try to find an Arabic voice
        arabic_voice = None
        for voice in voices:
            if "arabic" in voice.name.lower() or "ar" in voice.id.lower():
                arabic_voice = voice
                break

        if arabic_voice:
            self.tts.setProperty("voice", arabic_voice.id)
            print(f"Using Arabic voice: {arabic_voice.name}")
        else:
            print("No Arabic voice found, using default voice")

        # Set speech rate and volume
        self.tts.setProperty("rate", 150)  # Adjust speed as needed
        self.tts.setProperty("volume", 0.9)

    def extract_text_from_html(self, html_content):
        """Extract clean text from HTML content"""
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text and clean it up
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        return text

    def get_chapters(self):
        """Extract chapters from EPUB file"""
        book = epub.read_epub(self.epub_path)
        chapters = []

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Extract text content
                html_content = item.get_content().decode("utf-8")
                text = self.extract_text_from_html(html_content)

                if text.strip():  # Only add non-empty chapters
                    chapter_title = item.get_name() or f"Chapter {len(chapters) + 1}"
                    chapters.append(
                        {"title": chapter_title, "text": text, "id": item.get_id()}
                    )

        return chapters

    def text_to_speech(self, text, output_path):
        """Convert text to speech and save as audio file"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Generate speech
            self.tts.save_to_file(text, temp_path)
            self.tts.runAndWait()

            # Convert to MP3 using pydub
            audio = AudioSegment.from_wav(temp_path)
            audio.export(output_path, format="mp3", bitrate="128k")

            print(f"Audio saved to: {output_path}")

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def convert_chapter(self, chapter_index=0):
        """Convert a specific chapter to MP3"""
        chapters = self.get_chapters()

        if not chapters:
            print("No chapters found in the EPUB file")
            return None

        if chapter_index >= len(chapters):
            print(
                f"Chapter index {chapter_index} not found. Available chapters: 0-{len(chapters)-1}"
            )
            return None

        chapter = chapters[chapter_index]

        # Create safe filename
        safe_title = re.sub(r"[^\w\s-]", "", chapter["title"]).strip()
        safe_title = re.sub(r"[-\s]+", "_", safe_title)

        output_filename = f"chapter_{chapter_index:02d}_{safe_title}.mp3"
        output_path = self.output_dir / output_filename

        print(f"Converting chapter {chapter_index}: {chapter['title']}")
        print(f"Text length: {len(chapter['text'])} characters")

        # Convert to MP3
        self.text_to_speech(chapter["text"], output_path)

        return output_path

    def convert_all_chapters(self):
        """Convert all chapters to separate MP3 files"""
        chapters = self.get_chapters()

        if not chapters:
            print("No chapters found in the EPUB file")
            return []

        output_files = []

        for i, chapter in enumerate(chapters):
            print(f"\nProcessing chapter {i+1}/{len(chapters)}: {chapter['title']}")
            output_path = self.convert_chapter(i)
            if output_path:
                output_files.append(output_path)

        return output_files

    def list_chapters(self):
        """List all chapters in the EPUB file"""
        chapters = self.get_chapters()

        print(f"\nFound {len(chapters)} chapters in '{self.epub_path.name}':")
        print("-" * 50)

        for i, chapter in enumerate(chapters):
            text_preview = (
                chapter["text"][:100] + "..."
                if len(chapter["text"]) > 100
                else chapter["text"]
            )
            print(f"{i}: {chapter['title']}")
            print(f"   Text preview: {text_preview}")
            print(f"   Length: {len(chapter['text'])} characters\n")


def main():
    parser = argparse.ArgumentParser(description="Convert Arabic EPUB to MP3")
    parser.add_argument("epub_file", help="Path to the EPUB file")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument(
        "-c", "--chapter", type=int, help="Convert specific chapter (0-based index)"
    )
    parser.add_argument("-l", "--list", action="store_true", help="List all chapters")
    parser.add_argument("-a", "--all", action="store_true", help="Convert all chapters")

    args = parser.parse_args()

    if not os.path.exists(args.epub_file):
        print(f"Error: EPUB file '{args.epub_file}' not found")
        return

    converter = EpubToMp3Converter(args.epub_file, args.output)

    if args.list:
        converter.list_chapters()
    elif args.chapter is not None:
        converter.convert_chapter(args.chapter)
    elif args.all:
        converter.convert_all_chapters()
    else:
        # Default: convert first chapter
        print("Converting first chapter (use --help for more options)")
        converter.convert_chapter(0)


if __name__ == "__main__":
    main()
