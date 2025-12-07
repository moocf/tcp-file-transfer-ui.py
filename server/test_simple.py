"""
Simple test script for FT-Echo protocol
Run this after starting the TCP server to verify basic functionality
"""
import sys
from pathlib import Path
from tcp_client_lib import list_files, get_file, put_file

def main():
    host = "localhost"
    port = 9000
    
    print("FT-Echo Simple Test")
    print("=" * 50)
    
    # Create a test file
    test_file = Path("../demo_data/test_simple.txt")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("Hello, FT-Echo!\nThis is a test file.\n")
    
    print(f"\n1. Testing PUT: {test_file}")
    try:
        result = put_file(host, port, str(test_file))
        print(f"   ✓ PUT successful")
        print(f"   SHA256: {result['sha']}")
        print(f"   Size: {result['size']} bytes")
    except Exception as e:
        print(f"   ✗ PUT failed: {e}")
        return 1
    
    print(f"\n2. Testing LIST")
    try:
        files = list_files(host, port)
        print(f"   ✓ LIST successful: {len(files)} files")
        for f in files:
            print(f"   - {f['name']}: {f['size']} bytes")
    except Exception as e:
        print(f"   ✗ LIST failed: {e}")
        return 1
    
    print(f"\n3. Testing GET: test_simple.txt")
    dest_file = Path("../storage/downloaded_test.txt")
    dest_file.parent.mkdir(exist_ok=True)
    try:
        result = get_file(host, port, "test_simple.txt", str(dest_file))
        print(f"   ✓ GET successful")
        print(f"   SHA256: {result['sha']}")
        print(f"   Size: {result['size']} bytes")
        
        # Verify contents
        if test_file.read_bytes() == dest_file.read_bytes():
            print(f"   ✓ File contents match!")
        else:
            print(f"   ✗ File contents do not match!")
            return 1
    except Exception as e:
        print(f"   ✗ GET failed: {e}")
        return 1
    
    print("\n" + "=" * 50)
    print("All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())

