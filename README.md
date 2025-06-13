
# Arabic EPUB to MP3 Converter

A Python tool that converts Arabic EPUB files to MP3 audio files using Microsoft Azure AI Speech Services.

## Features

- Convert entire EPUB books or individual chapters to MP3 format
- Chapter listing and preview

## Prerequisites

- Python 3.7 or higher
- Azure Cognitive Services Speech subscription
- Required Python packages (see Installation)

## Installation

Clone this repository or download the script:

```bash
git clone <your-repository-url>
cd arabic-epub-to-mp3
```

Install required packages:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install azure-cognitiveservices-speech ebooklib beautifulsoup4 lxml
```

Set up Azure Cognitive Services:

- Create an Azure Cognitive Services Speech resource
  - Get your subscription key and endpoint
  - Set environment variables:

```bash
# On Linux/Mac:
export SPEECH_KEY="your_speech_key_here"
export ENDPOINT="your_endpoint_here"

# On Windows:
set SPEECH_KEY=your_speech_key_here
set ENDPOINT=your_endpoint_here
```

## Available Arabic Voices

The tool assumes the use of two Egyptian Arabic voices:

- **ar-EG-SalmaNeural** (Female) - Default voice
- **ar-EG-ShakirNeural** (Male)

## Usage Examples

### Basic Usage

Convert the first chapter of an EPUB file:

```bash
python arabic_to_mp3.py "كتاب_عربي.epub"
```

### List All Voices

```bash
python arabic_to_mp3.py "كتاب_عربي.epub" --voices
```

### Test Azure Speech Service

Test if your Azure credentials are working:

```bash
python arabic_to_mp3.py "كتاب_عربي.epub" --test
```

### List All Chapters

Preview all chapters in the EPUB file:

```bash
python arabic_to_mp3.py "كتاب_عربي.epub" --list
```

### Convert Specific Chapter

Convert chapter 3 (0-based indexing, so chapter 3 is index 2):

```bash
python arabic_to_mp3.py "كتاب_عربي.epub" --chapter 2
```

### Convert All Chapters

Convert the entire book to separate MP3 files:

```bash
python arabic_to_mp3.py "كتاب_عربي.epub" --all
```

### Use Different Voice

Convert using the male voice:

```bash
python arabic_to_mp3.py "كتاب_عربي.epub" --voice ar-EG-ShakirNeural --all
```

### Specify Output Directory

Save MP3 files to a specific directory:

```bash
python arabic_to_mp3.py "كتاب_عربي.epub" --output "/path/to/audiobooks" --all
```

### Complete Example

Convert entire book with male voice to custom directory:

```bash
python arabic_to_mp3.py "الأسود_يليق_بك.epub" \
    --all \
    --voice ar-EG-ShakirNeural \
    --output "~/AudioBooks/الأسود_يليق_بك"
```

## Command Line Arguments

| Argument    | Short | Description                              | Example                      |
| ----------- | ----- | ---------------------------------------- | ---------------------------- |
| `epub_file` | -     | Path to the EPUB file (required)         | `"book.epub"`                |
| `--output`  | `-o`  | Output directory for MP3 files           | `--output "audiobooks"`      |
| `--chapter` | `-c`  | Convert specific chapter (0-based index) | `--chapter 5`                |
| `--list`    | `-l`  | List all chapters in the EPUB            | `--list`                     |
| `--all`     | `-a`  | Convert all chapters                     | `--all`                      |
| `--test`    | `-t`  | Test Azure Speech with Arabic text       | `--test`                     |
| `--voices`  | `-v`  | List available Arabic voices             | `--voices`                   |
| `--voice`   | -     | Choose Arabic voice                      | `--voice ar-EG-ShakirNeural` |

## Development

### Running Tests

The project includes comprehensive unit tests:

```bash
# Run all tests
python -m pytest test_arabic_to_mp3.py -v

# Run specific test class
python -m pytest test_arabic_to_mp3.py::TestEpubToMp3Converter -v

# Run with coverage
python -m pytest test_arabic_to_mp3.py --cov=arabic_to_mp3 --cov-report=html
```
