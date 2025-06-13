#!/usr/bin/env python3
"""
Arabic EPUB to MP3 Converter
Converts EPUB files to MP3 audio files using Azure AI Speech text-to-speech
"""

import os
import re
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import azure.cognitiveservices.speech as speechsdk
import argparse


class EpubToMp3Converter:
    def __init__(self, epub_path, output_dir="output", voice_name="ar-EG-SalmaNeural"):
        self.epub_path = Path(epub_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.voice_name = voice_name
        self.setup_azure_speech()

    def setup_azure_speech(self):
        """Configure Azure Speech SDK for Arabic text"""

        self.speech_config = speechsdk.SpeechConfig(
            subscription=os.environ.get("SPEECH_KEY"),
            endpoint=os.environ.get("ENDPOINT"),
        )

        self.speech_config.speech_synthesis_voice_name = self.voice_name

        # TODO: Make voice a little slower
        # Optional: Set speech rate and other properties
        # You can adjust these values as needed
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
        )

    def list_available_voices(self):
        """List available voices (Note: This requires a different API call in Azure)"""
        print("Available Arabic voices for Azure Speech:")
        print("-" * 50)
        print("ar-EG-SalmaNeural - Egyptian Arabic (Female)")
        print("ar-EG-ShakirNeural - Egyptian Arabic (Male)")

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
        """Convert text to speech using Azure AI Speech and save as MP3 file"""
        try:
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None,  # We'll handle the output manually
            )

            result = synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print("Speech synthesis completed successfully")

                with open(output_path, "wb") as audio_file:
                    # ? How does this dictate the filename?
                    audio_file.write(result.audio_data)

                final_size = os.path.getsize(output_path)
                # TODO: Convert this to MB
                print(f"Final MP3 file size: {final_size} bytes")
                print(f"Audio saved to: {output_path}")
            else:
                raise Exception(f"Speech synthesis failed with reason: {result.reason}")

        except Exception as e:
            print(f"Error during Azure Speech conversion: {e}")
            raise

    def test_tts(self):
        """Test Azure Speech with a simple Arabic phrase"""
        test_text = "مرحبا بكم في اختبار التحويل من النص إلى الكلام باستخدام خدمة الكلام من مايكروسوفت"
        test_output = self.output_dir / "test_azure_arabic_tts.mp3"

        try:
            self.text_to_speech(test_text, test_output)
            print("Azure Speech TTS test successful!")
            return True
        except Exception as e:
            print(f"Azure Speech TTS test failed: {e}")
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

        # TODO: Change filename format to be "<book_name>_Chapter <chapter_index>"
        # ? Should also check if filename is enough to be displayed in Spotify as a local file or would it need editing the file properties
        # ? What does the safe_title do?
        # Create safe filename
        safe_title = re.sub(r"[^\w\s-]", "", chapter["title"]).strip()
        safe_title = re.sub(r"[-\s]+", "_", safe_title)

        output_filename = f"chapter_{chapter_index:02d}_{safe_title}.mp3"
        output_path = self.output_dir / output_filename

        print(f"Converting chapter {chapter_index}: {chapter['title']}")
        print(f"Text length: {len(chapter['text'])} characters")

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
            print(f"{i}: {chapter['title']}")
            print(f"   Length: {len(chapter['text'])} characters\n")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Arabic EPUB to MP3 using Azure Speech"
    )
    parser.add_argument("epub_file", help="Path to the EPUB file")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument(
        "-c", "--chapter", type=int, help="Convert specific chapter (0-based index)"
    )
    parser.add_argument("-l", "--list", action="store_true", help="List all chapters")
    parser.add_argument("-a", "--all", action="store_true", help="Convert all chapters")
    parser.add_argument(
        "-t", "--test", action="store_true", help="Test Azure Speech with Arabic text"
    )
    parser.add_argument(
        "-v", "--voices", action="store_true", help="List available Arabic voices"
    )
    parser.add_argument(
        "--voice",
        default="ar-EG-SalmaNeural",
        choices=["ar-EG-SalmaNeural", "ar-EG-ShakirNeural"],
        help="Choose Arabic voice (default: ar-EG-SalmaNeural)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.epub_file):
        print(f"Error: EPUB file '{args.epub_file}' not found")
        return

    try:
        converter = EpubToMp3Converter(args.epub_file, args.output, args.voice)
    except ValueError as e:
        print(f"Error: {e}")
        return

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
        print("Converting first chapter (use --help for more options)")
        converter.convert_chapter(0)


if __name__ == "__main__":
    main()
