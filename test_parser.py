"""Enhanced unit and integration tests with better OOP practices."""

# Standard library imports
import tempfile
from pathlib import Path
from unittest.mock import patch

# Third-party imports
import pytest

# Local imports
from helpers import JSONLHandler
from metadata_parser import MetadataParser
from validation_report import Validator


class TestJSONLHandler:
    """Test class for JSONLHandler with better encapsulation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.handler = JSONLHandler()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_write_and_read_jsonl(self):
        """Test writing and reading JSONL files."""
        test_data = [
            {"id": 1, "title": "Test Entry 1"},
            {"id": 2, "title": "Test Entry 2"}
        ]
        
        test_file = Path(self.temp_dir) / "test.jsonl"
        
        # Test writing
        written_count = self.handler.write_jsonl(str(test_file), test_data)
        assert written_count == 2
        assert self.handler.files_written_count == 1
        
        # Test reading
        read_data = list(self.handler.read_jsonl(str(test_file)))
        assert len(read_data) == 2
        assert read_data[0]["title"] == "Test Entry 1"
        assert self.handler.files_read_count == 1


class TestMetadataParser:
    """Test class for MetadataParser with mocked dependencies."""
    
    @patch('extractor.PDFExtractor.is_valid_pdf', new_callable=lambda: True)
    @patch('extractor.PDFExtractor.extract_text')
    def test_metadata_parsing(self, mock_extract, mock_is_valid):
        """Test metadata parsing with mocked PDF extraction."""
        # Setup mocks
        mock_extract.return_value = [{
            "page": 1,
            "text": ("Universal Serial Bus Power Delivery Specification\n"
                   "Revision: 3.2\nVersion: 1.1\nRelease Date: 2024-10")
        }]
        
        # Create parser with temporary output
        with tempfile.NamedTemporaryFile(suffix='.jsonl', 
                                       delete=False) as temp_file:
            parser = MetadataParser("dummy.pdf", temp_file.name)
            
            # Test parsing
            metadata = parser.parse_metadata()
            
            # Verify results
            assert metadata["revision"] == "3.2"
            assert metadata["version"] == "1.1"
            assert "Universal Serial Bus" in metadata["doc_title"]
            assert parser.processed_count == 1
            assert parser.status == "completed"


class TestValidator:
    """Test class for Validator with comprehensive coverage."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = Validator(
            out_path=str(Path(self.temp_dir) / "report.xlsx")
        )
    
    def test_metadata_validation(self):
        """Test metadata validation functionality."""
        # Valid metadata
        valid_metadata = {
            "doc_title": "Test Document",
            "revision": "1.0",
            "version": "1.0",
            "release_date": "2024-01"
        }
        
        result = Validator.validate_metadata(valid_metadata)
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        
        # Invalid metadata
        invalid_metadata = {"doc_title": "Test Document"}
        
        result = Validator.validate_metadata(invalid_metadata)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0


class TestBackwardsCompatibility:
    """Test backwards compatibility with original interface."""
    
    def test_helper_class_compatibility(self):
        """Test that Helper class still works as before."""
        from helpers import Helper
        
        # Test static methods exist
        assert hasattr(Helper, 'write_jsonl')
        assert hasattr(Helper, 'read_jsonl')


if __name__ == "__main__":
    pytest.main([__file__])
