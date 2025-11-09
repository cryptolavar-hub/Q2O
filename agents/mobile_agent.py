"""
Mobile Agent - Generates complete React Native mobile applications.

Enhanced with LLM integration for adaptive mobile development:
- Generates React Native code for iOS and Android
- Integrates native modules (camera, GPS, notifications, biometrics)
- Handles platform-specific code and configurations
- Creates navigation, state management, and API integrations
- Self-improving with template learning
"""

from typing import Dict, Any, List, Optional
import os
import logging
import asyncio
from pathlib import Path

from agents.base_agent import BaseAgent, AgentType, Task, TaskStatus
from agents.research_aware_mixin import ResearchAwareMixin
from utils.project_layout import ProjectLayout, get_default_layout
from utils.name_sanitizer import sanitize_objective, sanitize_for_filename

# LLM Integration (with graceful fallback)
try:
    from utils.llm_service import get_llm_service, LLMService
    from utils.template_learning_engine import get_template_learning_engine, TemplateLearningEngine
    from utils.configuration_manager import get_configuration_manager, ConfigurationManager
    LLM_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"LLM integration not available for MobileAgent: {e}")
    LLM_INTEGRATION_AVAILABLE = False


class MobileAgent(BaseAgent, ResearchAwareMixin):
    """
    Agent responsible for generating React Native mobile applications.
    
    Enhanced with hybrid generation strategy:
    1. Check learned templates (free, instant)
    2. Use traditional templates (fast, reliable)
    3. Generate with LLM if needed (adaptive, handles ANY mobile feature)
    4. Learn from successful LLM generations (self-improving)
    """

    def __init__(self, agent_id: str = "mobile_main", workspace_path: str = ".",
                 project_layout: Optional[ProjectLayout] = None,
                 project_id: Optional[str] = None):
        super().__init__(agent_id, AgentType.MOBILE, project_layout)
        self.workspace_path = workspace_path
        self.project_id = project_id
        self.generated_files: List[str] = []
        
        # LLM Integration
        self.use_llm = os.getenv("Q2O_USE_LLM", "true").lower() == "true"
        
        if LLM_INTEGRATION_AVAILABLE and self.use_llm:
            self.llm_service = get_llm_service()
            self.template_learning = get_template_learning_engine()
            self.config_manager = get_configuration_manager()
            self.llm_enabled = True
            logging.info("✅ MobileAgent: LLM integration enabled (hybrid mode)")
        else:
            self.llm_service = None
            self.template_learning = None
            self.config_manager = None
            self.llm_enabled = False
            if self.use_llm:
                logging.warning("⚠️  MobileAgent: LLM requested but not available, template-only mode")
            else:
                logging.info("ℹ️  MobileAgent: LLM disabled, template-only mode")
    
    def process_task(self, task: Task) -> Task:
        """
        Process a mobile development task.
        
        Enhanced with LLM integration for hybrid generation.
        
        Args:
            task: The mobile task to process
            
        Returns:
            The updated task with generated files
        """
        try:
            self.logger.info(f"Processing mobile task: {task.title}")
            
            # Load research results from dependencies
            research_results = self.get_research_results(task)
            
            # Extract useful information from research
            if research_results:
                api_info = self.extract_api_info_from_research(research_results)
                task.metadata['research_context'] = api_info
                self.logger.info(f"Enriched task with research: {len(api_info.get('key_findings', []))} findings")
            
            # Extract task information
            description = task.description
            metadata = task.metadata
            platforms = metadata.get("platforms", ["ios", "android"])
            features = metadata.get("features", [])
            tech_stack = task.tech_stack or ["React Native", "TypeScript"]
            
            # Setup project structure
            self._setup_project_structure()
            
            # Generate mobile app components (handles async if LLM enabled)
            if self.llm_enabled:
                loop = asyncio.get_event_loop()
                generated_files = loop.run_until_complete(
                    self._generate_mobile_app_async(description, platforms, features, tech_stack, task)
                )
            else:
                generated_files = self._generate_mobile_app(description, platforms, features, tech_stack, task)
            
            # Update task metadata
            task.metadata["generated_files"] = generated_files
            task.metadata["platforms"] = platforms
            task.result = {
                "files_created": generated_files,
                "platforms": platforms,
                "features": features,
                "status": "completed"
            }

            self.complete_task(task.id, task.result)
            self.logger.info(f"Completed mobile task {task.id}")
            
        except Exception as e:
            error_msg = f"Error processing mobile task: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.fail_task(task.id, error_msg)
            
        return task
    
    async def _generate_mobile_app_async(
        self,
        description: str,
        platforms: List[str],
        features: List[str],
        tech_stack: List[str],
        task: Task
    ) -> List[str]:
        """
        Generate mobile app using HYBRID approach with LLM integration.
        
        Strategy:
        1. Check learned templates (FREE!)
        2. Use traditional templates (fast, reliable)
        3. Generate with LLM (adaptive, handles ANY feature)
        4. Learn from successful LLM generations
        
        Args:
            description: What to build
            platforms: Target platforms (ios, android, or both)
            features: List of features to implement
            tech_stack: Technologies being used
            task: The task
            
        Returns:
            List of file paths created
        """
        generated_files = []
        
        # Core app structure
        generated_files.extend(await self._generate_app_structure())
        
        # Generate screens/components for each feature
        for feature in features:
            feature_files = await self._generate_feature_hybrid(
                feature, description, platforms, tech_stack, task
            )
            generated_files.extend(feature_files)
        
        # Generate navigation
        nav_files = await self._generate_navigation(features, tech_stack)
        generated_files.extend(nav_files)
        
        # Platform-specific configuration
        for platform in platforms:
            config_files = self._generate_platform_config(platform)
            generated_files.extend(config_files)
        
        return generated_files
    
    async def _generate_feature_hybrid(
        self,
        feature: str,
        description: str,
        platforms: List[str],
        tech_stack: List[str],
        task: Task
    ) -> List[str]:
        """
        Generate a mobile feature using hybrid approach.
        
        1. Check learned templates
        2. Try traditional template
        3. Generate with LLM
        4. Learn from success
        """
        task_desc = f"React Native {feature}: {description}"
        
        # STEP 1: Check learned templates (FREE!)
        if self.template_learning:
            learned_template = self.template_learning.find_similar_template(
                task_desc, tech_stack
            )
            if learned_template:
                self.logger.info(f"📚 Using learned template for {feature}")
                self.template_learning.increment_usage(learned_template.template_id)
                # BUG FIX: Use sanitize_for_filename instead of raw feature name
                sanitized_name = sanitize_for_filename(feature)
                return [self._write_file(f"src/screens/{sanitized_name}Screen.tsx", learned_template.template_content)]
        
        # STEP 2: Try traditional template
        try:
            content = self._generate_screen_template(feature, platforms)
            if content:
                self.logger.info(f"📄 Used traditional template for {feature}")
                # BUG FIX: Use sanitize_for_filename instead of raw feature name
                sanitized_name = sanitize_for_filename(feature)
                return [self._write_file(f"src/screens/{sanitized_name}Screen.tsx", content)]
        except Exception as e:
            self.logger.debug(f"Traditional template not available for {feature}: {e}")
        
        # STEP 3: Generate with LLM (ADAPTIVE)
        if not self.llm_service:
            raise ValueError(f"No template for {feature} and LLM not available")
        
        self.logger.info(f"🤖 Generating {feature} with LLM (no template available)")
        
        # Get research context
        research_context = task.metadata.get('research_context')
        
        # Build prompt
        system_prompt = """You are a senior React Native mobile developer.

Generate production-ready React Native code for iOS and Android.

Requirements:
- Use TypeScript for type safety
- Follow React Native best practices
- Optimize for performance (FlatList for lists, memoization)
- Handle platform differences (Platform.select, Platform.OS)
- Implement proper navigation (React Navigation)
- Add error handling and loading states
- Support both light and dark themes
- Ensure accessibility (screen readers)
- Handle safe areas (notches, home indicators)

Platform Considerations:
iOS: Follow Human Interface Guidelines
Android: Follow Material Design

Return clean, well-structured, production-ready TypeScript code with all necessary imports."""

        user_prompt = f"""Create a React Native screen for: {feature}

Description: {description}
Platforms: {', '.join(platforms)}
Tech Stack: {', '.join(tech_stack)}

Generate a complete, working screen component with:
- TypeScript types
- Proper imports
- Navigation integration
- Loading and error states
- Platform-specific styling if needed
- Accessibility support"""

        # Generate with LLM
        response = await self.llm_service.complete(
            system_prompt,
            user_prompt,
            temperature=0.4,  # Moderate for mobile code
            max_tokens=2048
        )
        
        if not response.success:
            raise ValueError(f"LLM generation failed: {response.error}")
        
        code_content = response.content
        
        # Log usage
        if response.usage:
            self.logger.info(
                f"💰 LLM cost: ${response.usage.total_cost:.4f} "
                f"({response.usage.input_tokens}+{response.usage.output_tokens} tokens)"
            )
        
        # STEP 4: Learn from successful generation
        if self.template_learning and response.success:
            quality_score = 95  # Placeholder
            
            template_id = await self.template_learning.learn_from_generation(
                task_description=task_desc,
                tech_stack=tech_stack,
                generated_code=code_content,
                source_llm=response.provider,
                quality_score=quality_score,
                metadata={
                    "feature": feature,
                    "platforms": platforms,
                    "task_id": task.id
                }
            )
            
            if template_id:
                self.logger.info(f"✨ Learned new mobile template: {template_id}")
        
        # Write file (BUG FIX: Use sanitize_for_filename)
        sanitized_name = sanitize_for_filename(feature)
        file_path = f"src/screens/{sanitized_name}Screen.tsx"
        return [self._write_file(file_path, code_content)]
    
    def _generate_mobile_app(
        self,
        description: str,
        platforms: List[str],
        features: List[str],
        tech_stack: List[str],
        task: Task
    ) -> List[str]:
        """
        Traditional synchronous generation (fallback when LLM unavailable).
        
        Uses built-in templates only.
        """
        generated_files = []
        
        # App structure
        generated_files.extend(self._generate_app_structure_sync())
        
        # Screens
        for feature in features:
            try:
                content = self._generate_screen_template(feature, platforms)
                # Use sanitize_for_filename for consistency
                sanitized_name = sanitize_for_filename(feature)
                file_path = f"src/screens/{sanitized_name}Screen.tsx"
                generated_files.append(self._write_file(file_path, content))
            except Exception as e:
                self.logger.warning(f"Could not generate {feature}: {e}")
        
        # Navigation
        generated_files.append(self._write_file(
            "src/navigation/RootNavigator.tsx",
            self._generate_navigation_template(features)
        ))
        
        # Platform configs
        for platform in platforms:
            generated_files.extend(self._generate_platform_config(platform))
        
        return generated_files
    
    def _setup_project_structure(self):
        """Create React Native project directory structure."""
        dirs = [
            "src/screens",
            "src/components",
            "src/navigation",
            "src/services",
            "src/store",
            "src/hooks",
            "src/utils",
            "src/types",
            "src/theme",
            "assets/images",
            "assets/fonts",
            "ios",
            "android"
        ]
        
        for dir_path in dirs:
            full_path = os.path.join(self.workspace_path, dir_path)
            os.makedirs(full_path, exist_ok=True)
    
    async def _generate_app_structure(self) -> List[str]:
        """Generate base app structure files."""
        files = []
        
        # App.tsx
        app_content = '''import React from 'react';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import {NavigationContainer} from '@react-navigation/native';
import RootNavigator from './src/navigation/RootNavigator';

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <RootNavigator />
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
'''
        files.append(self._write_file("App.tsx", app_content))
        
        # package.json
        package_json = '''{
  "name": "mobile-app",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web"
  },
  "dependencies": {
    "react": "18.2.0",
    "react-native": "0.72.0",
    "@react-navigation/native": "^6.1.0",
    "@react-navigation/stack": "^6.3.0",
    "react-native-safe-area-context": "4.6.0"
  },
  "devDependencies": {
    "@types/react": "~18.2.0",
    "typescript": "^5.0.0"
  }
}
'''
        files.append(self._write_file("package.json", package_json))
        
        # tsconfig.json
        tsconfig = '''{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true
  }
}
'''
        files.append(self._write_file("tsconfig.json", tsconfig))
        
        return files
    
    def _generate_app_structure_sync(self) -> List[str]:
        """Sync version of app structure generation."""
        try:
            # Check if already in async context
            loop = asyncio.get_running_loop()
            # Already async - just generate directly without async features
            return self._generate_app_structure_basic()
        except RuntimeError:
            # No running loop - safe to use async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._generate_app_structure())
            finally:
                loop.close()
    
    def _generate_app_structure_basic(self) -> List[str]:
        """Generate app structure synchronously (no async)."""
        files = []
        
        # App.tsx
        app_content = '''import React from 'react';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import {NavigationContainer} from '@react-navigation/native';
import RootNavigator from './src/navigation/RootNavigator';

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <RootNavigator />
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
'''
        files.append(self._write_file("App.tsx", app_content))
        
        # package.json
        package_json = '''{
  "name": "mobile-app",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web"
  },
  "dependencies": {
    "react": "18.2.0",
    "react-native": "0.72.0",
    "@react-navigation/native": "^6.1.0",
    "@react-navigation/stack": "^6.3.0",
    "react-native-safe-area-context": "4.6.0"
  },
  "devDependencies": {
    "@types/react": "~18.2.0",
    "typescript": "^5.0.0"
  }
}
'''
        files.append(self._write_file("package.json", package_json))
        
        # tsconfig.json
        tsconfig = '''{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true
  }
}
'''
        files.append(self._write_file("tsconfig.json", tsconfig))
        
        return files
    
    async def _generate_navigation(self, features: List[str], tech_stack: List[str]) -> List[str]:
        """Generate navigation setup."""
        content = self._generate_navigation_template(features)
        return [self._write_file("src/navigation/RootNavigator.tsx", content)]
    
    def _generate_navigation_template(self, features: List[str]) -> str:
        """Generate basic navigation template."""
        # Use sanitize_for_filename for consistency with actual file names
        screens_import = "\n".join([
            f"import {sanitize_objective(f)}Screen from '../screens/{sanitize_for_filename(f)}Screen';"
            for f in features
        ])
        
        screens_nav = "\n      ".join([
            f'<Stack.Screen name="{sanitize_objective(f)}" component={{{sanitize_objective(f)}Screen}} />'
            for f in features
        ])
        
        return f'''import React from 'react';
import {{createStackNavigator}} from '@react-navigation/stack';
{screens_import}

const Stack = createStackNavigator();

export default function RootNavigator() {{
  return (
    <Stack.Navigator>
      {screens_nav}
    </Stack.Navigator>
  );
}}
'''
    
    def _generate_screen_template(self, feature: str, platforms: List[str]) -> str:
        """Generate basic screen template."""
        screen_name = sanitize_objective(feature)
        
        return f'''import React from 'react';
import {{View, Text, StyleSheet}} from 'react-native';

export default function {screen_name}Screen() {{
  return (
    <View style={{styles.container}}>
      <Text style={{styles.title}}>{feature}</Text>
      <Text style={{styles.subtitle}}>Screen implementation goes here</Text>
    </View>
  );
}}

const styles = StyleSheet.create({{
  container: {{
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  }},
  title: {{
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  }},
  subtitle: {{
    fontSize: 16,
    color: '#666',
  }},
}});
'''
    
    def _generate_platform_config(self, platform: str) -> List[str]:
        """Generate platform-specific configuration files."""
        files = []
        
        if platform == "ios":
            # iOS Info.plist placeholder
            info_plist = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>MobileApp</string>
</dict>
</plist>
'''
            files.append(self._write_file("ios/Info.plist", info_plist))
        
        elif platform == "android":
            # Android manifest placeholder
            manifest = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:name=".MainApplication"
        android:label="@string/app_name">
    </application>
</manifest>
'''
            files.append(self._write_file("android/AndroidManifest.xml", manifest))
        
        return files
    
    def _write_file(self, relative_path: str, content: str) -> str:
        """Write a file and return its path."""
        full_path = os.path.join(self.workspace_path, relative_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"Created file: {relative_path}")
        self.generated_files.append(relative_path)
        
        return relative_path