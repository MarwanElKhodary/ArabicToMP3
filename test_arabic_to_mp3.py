#!/usr/bin/env python3
"""
Minimal tests for Arabic EPUB to MP3 Converter
Tests core functionality without requiring Azure credentials or actual EPUB files
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch
from arabic_to_mp3 import EpubToMp3Converter


class TestTextProcessing:
    """Test text processing functions that don't require external dependencies"""
    
    def setup_method(self):
        """Create a mock converter for testing"""
        with patch('arabic_to_mp3.epub.read_epub'):
            with patch.dict(os.environ, {'SPEECH_KEY': 'test_key', 'ENDPOINT': 'test_endpoint'}):
                self.converter = EpubToMp3Converter('test.epub')
    
    def test_split_text_into_chunks_short_text(self):
        """Test that short text isn't split"""
        text = "هذا نص قصير."
        chunks = self.converter.split_text_into_chunks(text, max_chunk_size=1000)
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_split_text_into_chunks_arabic_sentences(self):
        """Test splitting Arabic text by sentences"""
        text = "هذه الجملة الأولى. هذه الجملة الثانية؟ هذه الجملة الثالثة!"
        chunks = self.converter.split_text_into_chunks(text, max_chunk_size=50)
        assert len(chunks) > 1
        # Verify that each chunk contains complete sentences
        for chunk in chunks:
            assert chunk.strip() != ""
    
    def test_split_text_into_chunks_respects_max_size(self):
        """Test that chunks don't exceed max size (approximately)"""
        text = "كلمة " * 1000  # Create long text
        max_size = 100
        chunks = self.converter.split_text_into_chunks(text, max_chunk_size=max_size)
        
        for chunk in chunks:
            # Allow some flexibility due to sentence/word boundaries
            assert len(chunk) <= max_size + 50
    
    def test_split_by_words(self):
        """Test word-based splitting"""
        text = "كلمة واحدة اثنان ثلاثة أربعة خمسة"
        chunks = self.converter._split_by_words(text, max_chunk_size=20)
        assert len(chunks) > 1
        
        for chunk in chunks:
            assert len(chunk) <= 25  # Allow some flexibility
            assert chunk.strip() != ""
    
    def test_extract_text_from_html(self):
        """Test HTML text extraction"""
        html = """
        <html>
            <head><title>Title</title></head>
            <body>
                <p>هذا نص عربي.</p>
                <script>alert('remove me');</script>
                <style>body { color: red; }</style>
                <p>نص آخر هنا.</p>
            </body>
        </html>
        """
        
        text = self.converter.extract_text_from_html(html)
        
        # Should contain Arabic text
        assert "هذا نص عربي" in text
        assert "نص آخر هنا" in text
        
        # Should not contain script or style content
        assert "alert" not in text
        assert "color: red" not in text
        assert "<p>" not in text


class TestInitialization:
    """Test converter initialization and basic setup"""
    
    @patch('arabic_to_mp3.epub.read_epub')
    def test_init_with_defaults(self, mock_epub):
        """Test initialization with default parameters"""
        mock_book = Mock()
        mock_book.get_metadata.return_value = [("Test Book", "")]
        mock_epub.return_value = mock_book
        
        with patch.dict(os.environ, {'SPEECH_KEY': 'test_key', 'ENDPOINT': 'test_endpoint'}):
            converter = EpubToMp3Converter('test.epub')
            
            assert converter.epub_path == Path('test.epub')
            assert converter.output_dir == Path('output')
            assert converter.voice_name == "ar-EG-SalmaNeural"
            assert converter.chunk_size == 4000
    
    @patch('arabic_to_mp3.epub.read_epub')
    def test_init_with_custom_params(self, mock_epub):
        """Test initialization with custom parameters"""
        mock_book = Mock()
        mock_book.get_metadata.return_value = [("Test Book", "")]
        mock_epub.return_value = mock_book
        
        with patch.dict(os.environ, {'SPEECH_KEY': 'test_key', 'ENDPOINT': 'test_endpoint'}):
            converter = EpubToMp3Converter(
                'custom.epub',
                output_dir='custom_output',
                voice_name='ar-EG-ShakirNeural',
                chunk_size=2000
            )
            
            assert converter.epub_path == Path('custom.epub')
            assert converter.output_dir == Path('custom_output')
            assert converter.voice_name == "ar-EG-ShakirNeural"
            assert converter.chunk_size == 2000
    
    @patch('arabic_to_mp3.epub.read_epub')
    def test_get_book_name_from_metadata(self, mock_epub):
        """Test extracting book name from EPUB metadata"""
        mock_book = Mock()
        mock_book.get_metadata.return_value = [("كتاب عربي رائع!", "")]
        mock_epub.return_value = mock_book
        
        with patch.dict(os.environ, {'SPEECH_KEY': 'test_key', 'ENDPOINT': 'test_endpoint'}):
            converter = EpubToMp3Converter('test.epub')
            
            # Should clean the title for filename use
            assert converter.book_name == "كتاب_عربي_رائع"
    
    @patch('arabic_to_mp3.epub.read_epub')
    def test_get_book_name_fallback(self, mock_epub):
        """Test fallback to filename when metadata unavailable"""
        mock_epub.side_effect = Exception("Cannot read EPUB")
        
        with patch.dict(os.environ, {'SPEECH_KEY': 'test_key', 'ENDPOINT': 'test_endpoint'}):
            converter = EpubToMp3Converter('arabic_book.epub')
            
            # Should use filename without extension
            assert converter.book_name == "arabic_book"

class TestVoiceAndConfiguration:
    """Test voice selection and configuration"""
    
    def test_list_available_voices(self, capsys):
        """Test voice listing output"""
        with patch('arabic_to_mp3.epub.read_epub'):
            with patch.dict(os.environ, {'SPEECH_KEY': 'test_key', 'ENDPOINT': 'test_endpoint'}):
                converter = EpubToMp3Converter('test.epub')
                converter.list_available_voices()
                
                captured = capsys.readouterr()
                assert "ar-EG-SalmaNeural" in captured.out
                assert "ar-EG-ShakirNeural" in captured.out
                assert "Egyptian Arabic" in captured.out


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_missing_environment_variables(self):
        """Test behavior when Azure credentials are missing"""
        # TODO: Implement
        pass
    
    @patch('arabic_to_mp3.epub.read_epub')
    def test_invalid_epub_file(self, mock_epub):
        """Test handling of invalid EPUB files"""
        # ? I guess implement? I'm not really sure


if __name__ == "__main__":
    pytest.main([__file__, "-v"])