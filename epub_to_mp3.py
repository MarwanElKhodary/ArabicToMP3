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
import time


class EpubToMp3Converter:
    def __init__(self, epub_path, output_dir="output"):
        self.epub_path = Path(epub_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)  # ? Is it ok that this is exist_ok
        self.tts_engine = pyttsx3.init()
        self.setup_arabic_tts()

    def list_available_voices(self):
        """List all available voices for debugging"""
        voices = self.tts_engine.getProperty("voices")
        print("\nAvailable voices:")
        print("-" * 50)
        for i, voice in enumerate(voices):
            print(f"{i}: {voice.name}")
            print(f"   ID: {voice.id}")
            print()

    def setup_arabic_tts(self):
        """Configure TTS engine for Arabic text"""
        voices = self.tts_engine.getProperty("voices")

        arabic_voice = None
        arabic_keywords = ["arabic"]

        for voice in voices:
            voice_info = f"{voice.name.lower()} {voice.id.lower()}"
            if any(keyword in voice_info for keyword in arabic_keywords):
                arabic_voice = voice
                break

        if arabic_voice:
            self.tts_engine.setProperty("voice", arabic_voice.id)
            print(f"Using Arabic voice: {arabic_voice.name}")
        else:
            print("WARNING: No Arabic voice found!")

        self.tts_engine.setProperty(
            "rate", 120
        )  # Slower for better Arabic pronunciation
        self.tts_engine.setProperty("volume", 1.0)

    def extract_text_from_html(self, html_content):
        """Extract clean text from HTML content"""
        soup = BeautifulSoup(html_content, "html.parser")

        for script in soup(["script", "style"]):
            script.decompose()

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

        # TODO: Refactor into test cases
        try:
            print(f"Generating speech for text: {text[:50]}...")

            # Generate speech
            self.tts_engine.save_to_file(text, temp_path)
            self.tts_engine.runAndWait()

            # Wait a bit to ensure file is written
            time.sleep(1)

            if not os.path.exists(temp_path):
                raise Exception("TTS failed to create audio file")

            wav_size = os.path.getsize(temp_path)
            print(f"Generated WAV file size: {wav_size} bytes")

            if wav_size < 1000:  # WAV files should be much larger than this
                raise Exception(
                    f"Generated audio file is too small ({wav_size} bytes) - TTS likely failed"
                )

            print("Converting WAV to MP3...")
            audio = AudioSegment.from_wav(temp_path)

            audio.export(
                output_path,
                format="mp3",
                bitrate="192k",
                parameters=["-q:a", "2"],  # ? What does this do?
            )

            final_size = os.path.getsize(output_path)
            print(f"Final MP3 file size: {final_size} bytes")
            print(f"Audio saved to: {output_path}")

        except Exception as e:
            print(f"Error during TTS conversion: {e}")
            raise

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_tts(self):
        """Test TTS with a simple Arabic phrase"""
        test_text = "مرحبا بكم في اختبار التحويل من النص إلى الكلام"
        test_output = self.output_dir / "test_arabic_tts.mp3"

        try:
            self.text_to_speech(test_text, test_output)
            print("TTS test successful!")
            return True
        except Exception as e:
            print(f"TTS test failed: {e}")
            return False

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

        # Show a preview of the text
        preview_text = (
            chapter["text"][:200] + "..."
            if len(chapter["text"]) > 200
            else chapter["text"]
        )
        print(f"Text preview: {preview_text}")

        # Convert to MP3
        try:
            self.text_to_speech(chapter["text"], output_path)
            return output_path
        except Exception as e:
            print(f"Failed to convert chapter {chapter_index}: {e}")
            return None

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
    parser.add_argument(
        "-t", "--test", action="store_true", help="Test TTS with Arabic text"
    )
    parser.add_argument(
        "-v", "--voices", action="store_true", help="List available voices"
    )

    args = parser.parse_args()

    if not os.path.exists(args.epub_file):
        print(f"Error: EPUB file '{args.epub_file}' not found")
        return

    converter = EpubToMp3Converter(args.epub_file, args.output)

    if args.voices:
        converter.list_available_voices()
    elif args.test:
        converter.test_tts()
    elif args.list:
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
