"""
FT-Echo CLI Client
Interactive command-line interface for testing FT-Echo protocol.
"""
import sys
from pathlib import Path
from tcp_client_lib import FTEchoClient


def print_help():
    """Print help message"""
    print("""
FT-Echo CLI Client Commands:
  connect <host> <port>  - Connect to server
  list                   - List files on server
  get <filename>         - Download a file
  put <filepath>         - Upload a file
  resume <file> <offset> <direction> - Resume transfer (direction: get|put)
  quit                   - Disconnect and exit
  help                   - Show this help
""")


def main():
    """Main CLI loop"""
    client = None
    print("FT-Echo CLI Client")
    print("Type 'help' for commands")
    
    while True:
        try:
            line = input("ft-echo> ").strip()
            if not line:
                continue
            
            parts = line.split()
            cmd = parts[0].lower()
            
            if cmd == 'help':
                print_help()
            
            elif cmd == 'connect':
                if len(parts) < 3:
                    print("Usage: connect <host> <port>")
                    continue
                host = parts[1]
                port = int(parts[2])
                client = FTEchoClient(host, port)
                client.connect()
                print(f"Connected to {host}:{port}")
            
            elif cmd == 'list':
                if not client:
                    print("Not connected. Use 'connect <host> <port>' first")
                    continue
                try:
                    files = client.list_files()
                    if files:
                        print(f"\nFound {len(files)} files:")
                        print(f"{'Filename':<40} {'Size':>15}")
                        print("-" * 60)
                        for f in files:
                            print(f"{f['name']:<40} {f['size']:>15} bytes")
                    else:
                        print("No files found on server")
                except Exception as e:
                    print(f"Error: {e}")
            
            elif cmd == 'get':
                if not client:
                    print("Not connected. Use 'connect <host> <port>' first")
                    continue
                if len(parts) < 2:
                    print("Usage: get <filename> [dest_path]")
                    continue
                filename = parts[1]
                dest_path = parts[2] if len(parts) > 2 else filename
                try:
                    print(f"Downloading {filename} to {dest_path}...")
                    result = client.get_file(filename, dest_path)
                    print(f"✓ Download complete!")
                    print(f"  SHA256: {result['sha']}")
                    print(f"  Size: {result['size']} bytes")
                except Exception as e:
                    print(f"Error: {e}")
            
            elif cmd == 'put':
                if not client:
                    print("Not connected. Use 'connect <host> <port>' first")
                    continue
                if len(parts) < 2:
                    print("Usage: put <filepath>")
                    continue
                filepath = parts[1]
                try:
                    src_path = Path(filepath)
                    if not src_path.exists():
                        print(f"Error: File not found: {filepath}")
                        continue
                    print(f"Uploading {filepath}...")
                    result = client.put_file(str(src_path))
                    print(f"✓ Upload complete!")
                    print(f"  SHA256: {result['sha']}")
                    print(f"  Size: {result['size']} bytes")
                except Exception as e:
                    print(f"Error: {e}")
            
            elif cmd == 'resume':
                if not client:
                    print("Not connected. Use 'connect <host> <port>' first")
                    continue
                if len(parts) < 4:
                    print("Usage: resume <file> <offset> <direction>")
                    print("  direction: 'get' or 'put'")
                    continue
                filename = parts[1]
                offset = int(parts[2])
                direction = parts[3].lower()
                try:
                    if direction == 'get':
                        print(f"Resuming GET {filename} from offset {offset}...")
                        result = client.get_file(filename, filename, resume=True, offset=offset)
                        print(f"✓ Resume complete!")
                        print(f"  SHA256: {result['sha']}")
                    elif direction == 'put':
                        print(f"Resuming PUT {filename} from offset {offset}...")
                        result = client.put_file(filename, resume=True, offset=offset)
                        print(f"✓ Resume complete!")
                        print(f"  SHA256: {result['sha']}")
                    else:
                        print(f"Invalid direction: {direction}. Use 'get' or 'put'")
                except Exception as e:
                    print(f"Error: {e}")
            
            elif cmd == 'quit' or cmd == 'exit':
                if client:
                    try:
                        client.quit()
                    except:
                        pass
                print("Goodbye!")
                break
            
            else:
                print(f"Unknown command: {cmd}. Type 'help' for commands")
        
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'quit' to exit.")
        except EOFError:
            print("\nGoodbye!")
            if client:
                try:
                    client.quit()
                except:
                    pass
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    main()

