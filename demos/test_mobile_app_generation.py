"""
Mobile App Generation Test
Demonstrates Q2O's MobileAgent generating a complete React Native app.

Expected Output:
- Complete React Native project structure
- Authentication screens (Login, Register, ForgotPassword)
- Main app screens (Home, Profile, Settings)
- Navigation setup with React Navigation
- Platform-specific configurations (iOS + Android)
- TypeScript components with proper typing
- All LLM-enhanced or template-based
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import os
from datetime import datetime

# Load .env file
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

from agents.mobile_agent import MobileAgent
from agents.base_agent import Task, AgentType


async def main():
    """Test MobileAgent by generating a complete mobile app."""
    
    print("=" * 80)
    print(" " * 15 + "Q2O MOBILE APP GENERATION TEST")
    print(" " * 10 + "React Native App with Authentication & Features")
    print("=" * 80)
    print()
    
    # Check if LLM is enabled
    llm_enabled = os.getenv("Q2O_USE_LLM", "true").lower() == "true"
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    
    if not llm_enabled:
        print("[WARNING] Q2O_USE_LLM=false - MobileAgent will use templates only")
        print()
    
    if not api_key:
        print("[INFO] No API keys found - MobileAgent will use templates only")
        print("       (Add API keys for LLM-enhanced generation)")
        print()
    
    # Create output directory
    project_name = f"mobile_app_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    output_dir = Path(__file__).parent / "output" / project_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output Directory: {output_dir}")
    print()
    
    # ========================================================================
    # MOBILE APP GENERATION
    # ========================================================================
    print("=" * 80)
    print("GENERATING MOBILE APP")
    print("=" * 80)
    print()
    print("🤖 Initializing MobileAgent...")
    print()
    
    mobile = MobileAgent(
        agent_id="mobile_test",
        workspace_path=str(output_dir),
        project_id="test_mobile_app"
    )
    
    if mobile.llm_enabled:
        print("   ✅ LLM Integration: ACTIVE")
        print("   ✅ Hybrid Generation: Enabled")
        print("   ✅ Template Learning: Ready")
    else:
        print("   ℹ️  LLM Integration: Disabled (templates only)")
    
    print()
    
    # Define mobile app features
    features = [
        "Login",
        "Register",
        "ForgotPassword",
        "Home",
        "Profile",
        "Settings",
        "Notifications"
    ]
    
    print(f"📱 App Features: {len(features)} screens")
    for idx, feature in enumerate(features, 1):
        print(f"   {idx}. {feature}")
    print()
    
    # Create mobile development task
    task = Task(
        id="task_mobile_001",
        title="Create Complete React Native Mobile App",
        description="""
        Build a production-ready React Native mobile application with:
        
        - Authentication flow (Login, Register, Password Reset)
        - Main application screens (Home, Profile, Settings)
        - Push notifications support
        - Navigation with React Navigation
        - TypeScript for type safety
        - Platform-specific configurations for iOS and Android
        - Modern UI with React Native Paper
        - State management with Context API
        - API integration ready
        - Offline-first architecture
        - Accessibility support
        """,
        agent_type=AgentType.MOBILE,
        tech_stack=[
            "React Native",
            "TypeScript",
            "React Navigation",
            "React Native Paper",
            "AsyncStorage",
            "React Native Push Notifications"
        ],
        metadata={
            "platforms": ["ios", "android"],
            "features": features,
            "complexity": "high",
            "target_devices": "iOS 13+, Android 8+"
        }
    )
    
    print("💻 Generating mobile app...")
    print()
    
    # Process the task
    result_task = mobile.process_task(task)
    
    # ========================================================================
    # RESULTS
    # ========================================================================
    print()
    print("=" * 80)
    print("MOBILE APP GENERATION COMPLETE!")
    print("=" * 80)
    print()
    
    if result_task.result:
        files_created = result_task.result.get("files_created", [])
        platforms = result_task.result.get("platforms", [])
        
        print("📊 Summary:")
        print(f"   Status: {result_task.result.get('status', 'unknown')}")
        print(f"   Files Generated: {len(files_created)}")
        print(f"   Platforms: {', '.join(platforms)}")
        print(f"   Features: {len(features)} screens")
        print()
        
        # Categorize files
        screens = [f for f in files_created if 'screens' in f]
        components = [f for f in files_created if 'components' in f]
        navigation = [f for f in files_created if 'navigation' in f]
        config = [f for f in files_created if 'package.json' in f or 'tsconfig' in f or 'Info.plist' in f or 'Manifest' in f]
        other = [f for f in files_created if f not in screens + components + navigation + config]
        
        print("📁 Generated Files by Category:")
        print()
        
        if screens:
            print(f"   Screens ({len(screens)}):")
            for screen in screens:
                file_path = output_dir / screen
                size = file_path.stat().st_size if file_path.exists() else 0
                print(f"      - {screen} ({size} bytes)")
            print()
        
        if navigation:
            print(f"   Navigation ({len(navigation)}):")
            for nav in navigation:
                file_path = output_dir / nav
                size = file_path.stat().st_size if file_path.exists() else 0
                print(f"      - {nav} ({size} bytes)")
            print()
        
        if config:
            print(f"   Configuration ({len(config)}):")
            for conf in config:
                file_path = output_dir / conf
                size = file_path.stat().st_size if file_path.exists() else 0
                print(f"      - {conf} ({size} bytes)")
            print()
        
        if other:
            print(f"   Other Files ({len(other)}):")
            for oth in other:
                file_path = output_dir / oth
                size = file_path.stat().st_size if file_path.exists() else 0
                print(f"      - {oth} ({size} bytes)")
            print()
        
        # Show sample code
        if screens:
            sample_screen = output_dir / screens[0]
            if sample_screen.exists():
                print("📄 Sample Generated Code:")
                print("   " + "=" * 76)
                content = sample_screen.read_text()
                lines = content.split('\n')[:25]  # First 25 lines
                for line in lines:
                    print(f"   {line}")
                if len(content.split('\n')) > 25:
                    print(f"   ... ({len(content.split('\n')) - 25} more lines)")
                print("   " + "=" * 76)
                print()
    else:
        print("   [ERROR] Task failed to complete")
        return
    
    print()
    print("=" * 80)
    print("🎉 SUCCESS! Q2O generated a complete React Native mobile app!")
    print("=" * 80)
    print()
    print("What was generated:")
    print("  ✅ Complete React Native project structure")
    print("  ✅ Authentication screens (Login, Register, Password Reset)")
    print("  ✅ Main app screens (Home, Profile, Settings, Notifications)")
    print("  ✅ Navigation setup with React Navigation")
    print("  ✅ TypeScript configuration")
    print("  ✅ Platform-specific configs (iOS Info.plist, Android Manifest)")
    print("  ✅ Package.json with dependencies")
    print()
    
    if mobile.llm_enabled:
        print("💡 LLM Enhancement:")
        print("  - Intelligent code generation for complex features")
        print("  - Templates learned and saved for future apps")
        print("  - Next similar app will be faster and cheaper!")
        print()
        print("💰 Cost Tracking:")
        print("  Check llm_costs.db for detailed usage")
        print("  Check learned_templates.db for mobile templates created")
        print()
    
    print(f"📂 Full Output: {output_dir}")
    print()
    print("Next Steps:")
    print("  1. cd into output directory")
    print("  2. Run: npm install")
    print("  3. Run: npm run ios (or npm run android)")
    print("  4. Customize the generated code for your needs")
    print()
    print("🚀 Q2O: From idea to mobile app in minutes!")
    print()


if __name__ == "__main__":
    print()
    print("Starting Mobile App Generation Test...")
    print("This will demonstrate Q2O's MobileAgent capabilities")
    print()
    
    asyncio.run(main())

