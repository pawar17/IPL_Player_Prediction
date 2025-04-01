import pytest
import sys
from pathlib import Path

def run_weather_tests():
    """Run weather data collection tests"""
    # Get the tests directory path
    tests_dir = Path(__file__).parent
    
    # Run pytest with specific test file
    test_file = tests_dir / 'test_weather_collector.py'
    
    # Run tests with verbosity
    pytest.main([
        str(test_file),
        '-v',
        '--tb=short'
    ])

if __name__ == '__main__':
    run_weather_tests() 