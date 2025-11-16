#!/usr/bin/env python3
"""
NACC UI Launcher - Select and launch different UI variants
Allows easy comparison between conversational, enterprise, and professional UIs
"""

import sys
import argparse
from pathlib import Path

def launch_ui(share: bool = False, port: int = 7860):
    """Launch the NACC UI"""
    
    print(f"\n{'='*80}")
    print(f"🚀 NACC UI LAUNCHER")
    print(f"{'='*80}")
    print(f"Port: {port}")
    print(f"Share: {share}")
    print(f"{'='*80}\n")
    
    print("💼 Launching NACC Professional UI")
    print("   Features: Dark theme, dashboard, file browser, help system\n")
    from src.nacc_ui.professional_ui_v2 import create_professional_ui_v2
    demo = create_professional_ui_v2()
    demo.launch(server_name="0.0.0.0", server_port=port, share=share)


def main():
    parser = argparse.ArgumentParser(
        description="NACC UI Launcher - Network AI Command & Control Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch NACC UI (default port 7860)
  python -m src.nacc_ui.launch_ui
  
  # Launch with sharing enabled
  python -m src.nacc_ui.launch_ui --share
  
  # Launch on custom port
  python -m src.nacc_ui.launch_ui --port 8080

About NACC:
  Network AI Command & Control is an intelligent network orchestration
  platform that combines natural language processing with automation.
  
  Features:
  - Natural language command interface
  - Real-time network dashboard
  - Multi-node orchestration
  - File browser and management
  - Context-aware AI conversations
        """
    )
    
    parser.add_argument(
        '--share', '-s',
        action='store_true',
        help='Create public sharing link'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=7860,
        help='Port to run on (default: 7860)'
    )
    
    args = parser.parse_args()
    
    try:
        launch_ui(args.share, args.port)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down NACC UI...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error launching UI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
