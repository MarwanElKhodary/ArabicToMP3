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
import time


class EpubToMp3Converter:
    def __init__(
        self,
        epub_path,
        output_dir="output",
        voice_name="ar-EG-SalmaNeural",
        chunk_size=4000,
    ):
        self.epub_path = Path(epub_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.voice_name = voice_name
        self.chunk_size = chunk_size
        self.book_name = self._get_book_name()
        self.setup_azure_speech()

    def _get_book_name(self):
        """Extract book name from EPUB file for use in filenames"""
        try:
            book = epub.read_epub(self.epub_path)
            title = book.get_metadata("DC", "title")
            if title:
                book_name = title[0][0]  # Get the first title
                # Clean the title for use in filenames
                safe_name = re.sub(r"[^\w\s-]", "", book_name).strip()
                safe_name = re.sub(r"[-\s]+", "_", safe_name)
                return safe_name
        except Exception:
            pass

        # Fallback to filename without extension
        return self.epub_path.stem

    def setup_azure_speech(self):
        """Configure Azure Speech SDK for Arabic text"""
        self.speech_config = speechsdk.SpeechConfig(
            subscription=os.environ.get("SPEECH_KEY"),
            endpoint=os.environ.get("ENDPOINT"),
        )

        self.speech_config.speech_synthesis_voice_name = self.voice_name

        # Set speech rate and other properties
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
        )

    def split_text_into_chunks(self, text, max_chunk_size=None):
        """
        Split text into chunks of approximately max_chunk_size characters
        without breaking words or sentences when possible
        """
        if max_chunk_size is None:
            max_chunk_size = self.chunk_size

        if len(text) <= max_chunk_size:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by sentences first (Arabic sentences often end with . or ؟ or !)
        sentences = re.split(r"[.؟!]\s+", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Add back the punctuation (except for the last sentence)
            if not sentence.endswith((".", "؟", "!")):
                sentence += "."

            # If adding this sentence would exceed the chunk size
            if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
                # If current chunk is not empty, save it
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # If this single sentence is longer than max_chunk_size, split it by words
                if len(sentence) > max_chunk_size:
                    word_chunks = self._split_by_words(sentence, max_chunk_size)
                    chunks.extend(word_chunks[:-1])  # Add all but the last chunk
                    current_chunk = word_chunks[-1] if word_chunks else ""
                else:
                    current_chunk = sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # Add the last chunk if it's not empty
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_words(self, text, max_chunk_size):
        """Split text by words when sentence splitting isn't enough"""
        words = text.split()
        chunks = []
        current_chunk = ""

        for word in words:
            if len(current_chunk) + len(word) + 1 > max_chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = word
            else:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

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

    def text_to_speech(self, text, output_path, retry_count=3):
        """Convert text to speech using Azure AI Speech and save as MP3 file"""
        for attempt in range(retry_count):
            try:
                synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=self.speech_config,
                    audio_config=None,  # We'll handle the output manually
                )

                print(f"Converting text chunk ({len(text)} characters)...")
                result = synthesizer.speak_text_async(text).get()

                if result is None:
                    return False

                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    with open(output_path, "wb") as audio_file:
                        audio_file.write(result.audio_data)

                    final_size = os.path.getsize(output_path)
                    final_size_mb = final_size / (1024 * 1024)
                    print(
                        f"Successfully created: {output_path.name} ({final_size_mb:.2f} MB)"
                    )
                    return True

                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = speechsdk.CancellationDetails(result)
                    print(f"Speech synthesis canceled: {cancellation_details.reason}")
                    if cancellation_details.error_details:
                        print(f"Error details: {cancellation_details.error_details}")

                    # If it's a quota/rate limit error, wait before retrying
                    if (
                        "quota" in str(cancellation_details.error_details).lower()
                        or "rate" in str(cancellation_details.error_details).lower()
                    ):
                        wait_time = (attempt + 1) * 5  # Exponential backoff
                        print(
                            f"Rate limit detected, waiting {wait_time} seconds before retry..."
                        )
                        time.sleep(wait_time)
                        continue

                    raise Exception(
                        f"Speech synthesis canceled: {cancellation_details.error_details}"
                    )
                else:
                    raise Exception(
                        f"Speech synthesis failed with reason: {result.reason}"
                    )

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(
                        f"Error during Azure Speech conversion after {retry_count} attempts: {e}"
                    )
                    raise

        return False

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

    def convert_chapter_chunked(self, chapter_index=0):
        """Convert a specific chapter to multiple MP3 files (chunked)"""
        chapters = self.get_chapters()

        if not chapters:
            print("No chapters found in the EPUB file")
            return []

        if chapter_index >= len(chapters):
            print(
                f"Chapter index {chapter_index} not found. Available chapters: 0-{len(chapters)-1}"
            )
            return []

        chapter = chapters[chapter_index]
        print(f"\nProcessing Chapter {chapter_index + 1}: {chapter['title']}")
        print(f"Total text length: {len(chapter['text'])} characters")

        # Split chapter text into chunks
        text_chunks = self.split_text_into_chunks(chapter["text"])
        print(f"Split into {len(text_chunks)} chunks")

        output_files = []

        for chunk_index, chunk_text in enumerate(text_chunks):
            output_filename = f"{self.book_name}_Ch{chapter_index + 1:02d}_Part{chunk_index + 1:02d}.mp3"
            output_path = self.output_dir / output_filename

            print(f"\nProcessing chunk {chunk_index + 1}/{len(text_chunks)}")

            try:
                success = self.text_to_speech(chunk_text, output_path)
                if success:
                    output_files.append(output_path)
                else:
                    print(f"Failed to convert chunk {chunk_index + 1}")

                # Small delay between API calls to avoid rate limiting
                time.sleep(1)

            except Exception as e:
                print(f"Failed to convert chunk {chunk_index + 1}: {e}")
                continue

        return output_files

    def convert_all_chapters_chunked(self):
        """Convert all chapters to chunked MP3 files"""
        chapters = self.get_chapters()

        if not chapters:
            print("No chapters found in the EPUB file")
            return []

        all_output_files = []

        for i, chapter in enumerate(chapters):
            print(f"\n{'='*60}")
            print(f"Processing Chapter {i+1}/{len(chapters)}: {chapter['title']}")
            print(f"{'='*60}")

            chapter_files = self.convert_chapter_chunked(i)
            all_output_files.extend(chapter_files)

            # Longer delay between chapters to be safe
            if i < len(chapters) - 1:  # Don't sleep after the last chapter
                print("Waiting before next chapter...")
                time.sleep(3)

        print(f"\n{'='*60}")
        print(f"Conversion complete! Created {len(all_output_files)} audio files.")
        print(f"{'='*60}")

        return all_output_files

    def convert_entire_book_chunked(self):
        """Convert entire book as one continuous text, chunked into parts"""
        chapters = self.get_chapters()

        if not chapters:
            print("No chapters found in the EPUB file")
            return []

        # Combine all chapter texts
        full_text = ""
        for chapter in chapters:
            full_text += chapter["text"] + "\n\n"

        print(f"Total book length: {len(full_text)} characters")

        # Split into chunks
        text_chunks = self.split_text_into_chunks(full_text)
        print(f"Split entire book into {len(text_chunks)} parts")

        output_files = []

        for chunk_index, chunk_text in enumerate(text_chunks):
            output_filename = f"{self.book_name}_Part{chunk_index + 1:03d}.mp3"
            output_path = self.output_dir / output_filename

            print(f"\nProcessing part {chunk_index + 1}/{len(text_chunks)}")

            try:
                success = self.text_to_speech(chunk_text, output_path)
                if success:
                    output_files.append(output_path)
                else:
                    print(f"Failed to convert part {chunk_index + 1}")

                # Small delay between API calls
                time.sleep(1)

            except Exception as e:
                print(f"Failed to convert part {chunk_index + 1}: {e}")
                continue

        print(f"\nBook conversion complete! Created {len(output_files)} audio files.")
        return output_files

    def list_chapters(self):
        """List all chapters in the EPUB file with chunk information"""
        chapters = self.get_chapters()

        print(f"\nFound {len(chapters)} chapters in '{self.epub_path.name}':")
        print("-" * 70)

        total_chunks = 0
        for i, chapter in enumerate(chapters):
            chunks = self.split_text_into_chunks(chapter["text"])
            chunk_count = len(chunks)
            total_chunks += chunk_count

            print(f"{i}: {chapter['title']}")
            print(f"   Length: {len(chapter['text'])} characters")
            print(f"   Will be split into: {chunk_count} audio files")
            print()

        print(f"Total audio files that will be created: {total_chunks}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Arabic EPUB to MP3 using Azure Speech (with chunking)"
    )
    parser.add_argument("epub_file", help="Path to the EPUB file")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument(
        "-c", "--chapter", type=int, help="Convert specific chapter (0-based index)"
    )
    parser.add_argument("-l", "--list", action="store_true", help="List all chapters")
    parser.add_argument(
        "-a", "--all", action="store_true", help="Convert all chapters (chunked)"
    )
    parser.add_argument(
        "-b",
        "--book",
        action="store_true",
        help="Convert entire book as continuous chunks",
    )
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
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4000,
        help="Maximum characters per chunk (default: 4000)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.epub_file):
        print(f"Error: EPUB file '{args.epub_file}' not found")
        return

    try:
        converter = EpubToMp3Converter(
            args.epub_file, args.output, args.voice, args.chunk_size
        )
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
        converter.convert_chapter_chunked(args.chapter)
    elif args.all:
        converter.convert_all_chapters_chunked()
    elif args.book:
        converter.convert_entire_book_chunked()
    else:
        print("Converting first chapter in chunks (use --help for more options)")
        converter.convert_chapter_chunked(0)


if __name__ == "__main__":
    main()
