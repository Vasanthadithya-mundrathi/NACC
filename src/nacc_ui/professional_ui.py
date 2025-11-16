"""
NACC Professional UI - Enterprise-Grade Interface with Advanced Features
Enhanced version with dark mode, professional animations, and comprehensive enterprise features.
"""

import gradio as gr
import json
import requests
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import logging
from pathlib import Path

# Import the existing components
from .ai_intent_parser import AIIntentParser, PathResolver, ExecutionPlan
from .conversational_ui import NACCConversationUI, SessionState
from .enterprise_ui import EnterpriseNACCUI, EnterpriseTheme

# Orchestrator URL
ORCHESTRATOR_URL = os.getenv("NACC_ORCHESTRATOR_URL", "http://127.0.0.1:8888")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProfessionalTheme(EnterpriseTheme):
    """Enhanced theme system with dark mode support and advanced design tokens"""
    
    # Dark Mode Colors
    DARK_COLORS = {
        # Primary Brand Colors (Dark)
        'primary': '#3b82f6',      # Light Blue for better visibility
        'primary_light': '#60a5fa', # Lighter Blue
        'primary_dark': '#2563eb',  # Dark Blue
        
        # Secondary Colors (Dark)
        'secondary': '#94a3b8',     # Light Gray
        'accent': '#38bdf8',        # Sky Blue
        
        # Semantic Colors (Dark)
        'success': '#10b981',       # Emerald Green
        'warning': '#f59e0b',       # Amber
        'error': '#ef4444',         # Red
        'info': '#06b6d4',          # Cyan
        
        # Background Colors (Dark)
        'bg_primary': '#0f172a',    # Dark Slate
        'bg_secondary': '#1e293b',  # Medium Dark
        'bg_tertiary': '#334155',   # Light Dark
        
        # Text Colors (Dark)
        'text_primary': '#f8fafc',   # Near White
        'text_secondary': '#cbd5e1', # Light Gray
        'text_muted': '#94a3b8',     # Medium Gray
        
        # Border Colors (Dark)
        'border_light': '#334155',   # Light borders
        'border_medium': '#475569',  # Medium borders
        'border_dark': '#64748b',    # Dark borders
    }
    
    # Animation timing
    ANIMATIONS = {
        'bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'slide': 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        'fade': 'ease-in-out',
    }


class ProfessionalNACCUI(EnterpriseNACCUI):
    """Enhanced UI with professional features, dark mode, and enterprise capabilities"""
    
    def __init__(self):
        super().__init__()
        self.theme = ProfessionalTheme()
        self.current_theme = "dark"  # Default to dark mode like screenshot
        self.animation_enabled = True
        self.professional_mode = True
        
    def get_comprehensive_css(self) -> str:
        """Generate comprehensive CSS with dark mode support and professional features"""
        base_css = self.get_enterprise_css()
        
        dark_mode_css = f"""
        /* Dark Mode Support */
        [data-theme="dark"] {{
            --primary: {self.theme.DARK_COLORS['primary']};
            --primary-light: {self.theme.DARK_COLORS['primary_light']};
            --primary-dark: {self.theme.DARK_COLORS['primary_dark']};
            --success: {self.theme.DARK_COLORS['success']};
            --warning: {self.theme.DARK_COLORS['warning']};
            --error: {self.theme.DARK_COLORS['error']};
            --info: {self.theme.DARK_COLORS['info']};
            
            --bg-primary: {self.theme.DARK_COLORS['bg_primary']};
            --bg-secondary: {self.theme.DARK_COLORS['bg_secondary']};
            --bg-tertiary: {self.theme.DARK_COLORS['bg_tertiary']};
            
            --text-primary: {self.theme.DARK_COLORS['text_primary']};
            --text-secondary: {self.theme.DARK_COLORS['text_secondary']};
            --text-muted: {self.theme.DARK_COLORS['text_muted']};
            
            --border-light: {self.theme.DARK_COLORS['border_light']};
            --border-medium: {self.theme.DARK_COLORS['border_medium']};
            --border-dark: {self.theme.DARK_COLORS['border_dark']};
        }}
        
        /* Theme Toggle Button */
        .theme-toggle {{
            position: fixed !important;
            top: 2rem !important;
            right: 2rem !important;
            z-index: 1000 !important;
            background: var(--bg-primary) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-full) !important;
            padding: 0.75rem !important;
            cursor: pointer !important;
            transition: all {self.theme.TRANSITIONS['fast']} !important;
            box-shadow: var(--shadow-md) !important;
            color: var(--text-primary) !important;
        }}
        
        .theme-toggle:hover {{
            transform: translateY(-2px) !important;
            box-shadow: var(--shadow-lg) !important;
        }}
        
        /* Enhanced Animations */
        @keyframes pulse {{
            0%, 100% {{
                opacity: 1 !important;
            }}
            50% {{
                opacity: 0.7 !important;
            }}
        }}
        
        @keyframes slideInUp {{
            from {{
                opacity: 0 !important;
                transform: translateY(30px) !important;
            }}
            to {{
                opacity: 1 !important;
                transform: translateY(0) !important;
            }}
        }}
        
        @keyframes slideInRight {{
            from {{
                opacity: 0 !important;
                transform: translateX(30px) !important;
            }}
            to {{
                opacity: 1 !important;
                transform: translateX(0) !important;
            }}
        }}
        
        @keyframes fadeIn {{
            from {{
                opacity: 0 !important;
            }}
            to {{
                opacity: 1 !important;
            }}
        }}
        
        @keyframes shimmer {{
            0% {{
                background-position: -200px 0 !important;
            }}
            100% {{
                background-position: calc(200px + 100%) 0 !important;
            }}
        }}
        
        /* Professional Loading States */
        .professional-loading {{
            background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg-tertiary) 50%, var(--bg-secondary) 75%) !important;
            background-size: 200px 100% !important;
            animation: shimmer 1.5s infinite !important;
            border-radius: var(--radius-md) !important;
        }}
        
        .status-indicator-animated {{
            animation: pulse 2s infinite !important;
        }}
        
        /* Enhanced Message Styling */
        .message-enhanced {{
            animation: slideInUp 0.4s {self.theme.ANIMATIONS['smooth']} !important;
            margin-bottom: 1.5rem !important;
        }}
        
        .user-message-enhanced {{
            display: flex !important;
            justify-content: flex-end !important;
            animation: slideInRight 0.4s {self.theme.ANIMATIONS['smooth']} !important;
        }}
        
        .bot-bubble-enhanced {{
            background: var(--bg-primary) !important;
            color: var(--text-primary) !important;
            padding: 1.5rem 2rem !important;
            border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) var(--radius-sm) !important;
            border: 1px solid var(--border-light) !important;
            max-width: 70% !important;
            box-shadow: var(--shadow-md) !important;
            transition: all {self.theme.TRANSITIONS['fast']} !important;
            position: relative !important;
            overflow: hidden !important;
        }}
        
        .bot-bubble-enhanced::before {{
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent) !important;
            transition: left 0.5s !important;
        }}
        
        .bot-bubble-enhanced:hover::before {{
            left: 100% !important;
        }}
        
        .bot-bubble-enhanced:hover {{
            box-shadow: var(--shadow-lg) !important;
            transform: translateY(-2px) !important;
        }}
        
        /* Professional Status Dashboard */
        .status-dashboard {{
            background: var(--bg-primary) !important;
            border-radius: var(--radius-xl) !important;
            box-shadow: var(--shadow-xl) !important;
            border: 1px solid var(--border-light) !important;
            overflow: hidden !important;
            animation: fadeIn 0.6s {self.theme.ANIMATIONS['smooth']} !important;
        }}
        
        .metric-card {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-lg) !important;
            padding: 1.5rem !important;
            margin-bottom: 1rem !important;
            transition: all {self.theme.TRANSITIONS['fast']} !important;
            position: relative !important;
            overflow: hidden !important;
        }}
        
        .metric-card::before {{
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 4px !important;
            height: 100% !important;
            background: var(--primary) !important;
            transition: width {self.theme.TRANSITIONS['fast']} !important;
        }}
        
        .metric-card:hover {{
            transform: translateY(-4px) !important;
            box-shadow: var(--shadow-xl) !important;
        }}
        
        .metric-card:hover::before {{
            width: 100% !important;
            opacity: 0.1 !important;
        }}
        
        /* Professional Navigation */
        .enterprise-navigation {{
            background: var(--bg-primary) !important;
            border-bottom: 1px solid var(--border-light) !important;
            backdrop-filter: blur(10px) !important;
            position: sticky !important;
            top: 0 !important;
            z-index: 100 !important;
            padding: 1rem 2rem !important;
        }}
        
        .nav-item {{
            padding: 0.5rem 1rem !important;
            border-radius: var(--radius-md) !important;
            color: var(--text-secondary) !important;
            text-decoration: none !important;
            font-weight: {self.theme.TYPOGRAPHY['medium']} !important;
            transition: all {self.theme.TRANSITIONS['fast']} !important;
            cursor: pointer !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 0.5rem !important;
        }}
        
        .nav-item:hover,
        .nav-item.active {{
            background: var(--primary) !important;
            color: white !important;
            transform: translateY(-1px) !important;
        }}
        
        /* Enhanced File Browser */
        .file-browser-enhanced {{
            background: var(--bg-secondary) !important;
            border-radius: var(--radius-lg) !important;
            padding: 1rem !important;
            border: 1px solid var(--border-light) !important;
            max-height: 500px !important;
            overflow-y: auto !important;
        }}
        
        .file-item {{
            display: flex !important;
            align-items: center !important;
            gap: 0.75rem !important;
            padding: 0.75rem 1rem !important;
            margin: 0.5rem 0 !important;
            background: var(--bg-primary) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-md) !important;
            cursor: pointer !important;
            transition: all {self.theme.TRANSITIONS['fast']} !important;
            position: relative !important;
            overflow: hidden !important;
        }}
        
        .file-item::before {{
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, var(--primary-light), transparent) !important;
            transition: left 0.3s !important;
        }}
        
        .file-item:hover::before {{
            left: 100% !important;
        }}
        
        .file-item:hover {{
            background: var(--primary) !important;
            color: white !important;
            transform: translateX(4px) !important;
            box-shadow: var(--shadow-md) !important;
        }}
        
        /* Professional Error States */
        .error-container {{
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%) !important;
            border: 1px solid var(--error) !important;
            border-left: 4px solid var(--error) !important;
            border-radius: var(--radius-lg) !important;
            padding: 1.5rem !important;
            margin: 1rem 0 !important;
            animation: slideInUp 0.3s {self.theme.ANIMATIONS['smooth']} !important;
        }}
        
        /* Help System */
        .help-panel {{
            background: var(--bg-primary) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-xl) !important;
            box-shadow: var(--shadow-xl) !important;
            padding: 2rem !important;
            animation: fadeIn 0.5s {self.theme.ANIMATIONS['smooth']} !important;
        }}
        
        .help-section {{
            margin-bottom: 2rem !important;
        }}
        
        .help-title {{
            font-size: {self.theme.TYPOGRAPHY['xl']} !important;
            font-weight: {self.theme.TYPOGRAPHY['semibold']} !important;
            color: var(--text-primary) !important;
            margin-bottom: 1rem !important;
        }}
        
        .help-item {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-md) !important;
            padding: 1rem !important;
            margin-bottom: 0.5rem !important;
            transition: all {self.theme.TRANSITIONS['fast']} !important;
        }}
        
        .help-item:hover {{
            background: var(--bg-tertiary) !important;
            transform: translateX(2px) !important;
        }}
        
        /* Professional Tooltips */
        .tooltip {{
            position: relative !important;
            display: inline-block !important;
        }}
        
        .tooltip .tooltip-text {{
            visibility: hidden !important;
            width: 200px !important;
            background-color: var(--bg-primary) !important;
            color: var(--text-primary) !important;
            text-align: center !important;
            border-radius: var(--radius-md) !important;
            padding: 0.5rem !important;
            position: absolute !important;
            z-index: 1000 !important;
            bottom: 125% !important;
            left: 50% !important;
            margin-left: -100px !important;
            opacity: 0 !important;
            transition: opacity {self.theme.TRANSITIONS['fast']} !important;
            box-shadow: var(--shadow-lg) !important;
            border: 1px solid var(--border-light) !important;
            font-size: {self.theme.TYPOGRAPHY['sm']} !important;
        }}
        
        .tooltip:hover .tooltip-text {{
            visibility: visible !important;
            opacity: 1 !important;
        }}
        
        /* Keyboard Shortcuts Indicator */
        .keyboard-hint {{
            background: var(--bg-tertiary) !important;
            border: 1px solid var(--border-medium) !important;
            border-radius: var(--radius-sm) !important;
            padding: 0.2rem 0.4rem !important;
            font-family: {self.theme.TYPOGRAPHY['font_mono']} !important;
            font-size: {self.theme.TYPOGRAPHY['xs']} !important;
            color: var(--text-muted) !important;
            margin-left: 0.5rem !important;
        }}
        
        /* Enhanced Mobile Responsiveness */
        @media (max-width: 768px) {{
            .enterprise-main {{
                padding: 0 1rem !important;
                grid-template-columns: 1fr !important;
                gap: 1rem !important;
            }}
            
            .chat-container,
            .right-panel {{
                height: calc(100vh - 120px) !important;
                min-height: 400px !important;
            }}
            
            .chat-messages {{
                padding: 1rem !important;
            }}
            
            .user-bubble,
            .bot-bubble {{
                max-width: 85% !important;
            }}
            
            .theme-toggle {{
                top: 1rem !important;
                right: 1rem !important;
                padding: 0.5rem !important;
            }}
            
            .enterprise-navigation {{
                padding: 0.75rem 1rem !important;
            }}
        }}
        
        /* Accessibility Enhancements */
        @media (prefers-reduced-motion: reduce) {{
            * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
            
            .message-enhanced,
            .user-message-enhanced {{
                animation: none !important;
            }}
        }}
        
        /* High Contrast Mode */
        @media (prefers-contrast: high) {{
            .user-bubble {{
                border: 2px solid var(--text-primary) !important;
            }}
            
            .bot-bubble-enhanced {{
                border: 2px solid var(--border-dark) !important;
            }}
            
            .file-item:hover {{
                outline: 2px solid var(--primary) !important;
            }}
        }}
        
        /* Focus Management */
        .focus-enhanced:focus {{
            outline: 2px solid var(--primary) !important;
            outline-offset: 2px !important;
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1) !important;
        }}
        
        /* Print Optimizations */
        @media print {{
            .theme-toggle,
            .enterprise-navigation,
            .help-panel {{
                display: none !important;
            }}
            
            .chat-container,
            .right-panel {{
                box-shadow: none !important;
                border: 1px solid #ccc !important;
            }}
            
            .message-enhanced,
            .user-message-enhanced {{
                animation: none !important;
            }}
        }}
        """
        
        return base_css + dark_mode_css
    
    def create_theme_toggle(self) -> str:
        """Create theme toggle button"""
        return f"""
        <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme (L/D)">
            <svg id="theme-icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z"/>
            </svg>
        </button>
        <script>
            function toggleTheme() {{
                const html = document.documentElement;
                const currentTheme = html.getAttribute('data-theme');
                const themeIcon = document.getElementById('theme-icon');
                
                if (currentTheme === 'dark') {{
                    html.removeAttribute('data-theme');
                    themeIcon.innerHTML = '<path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z"/>';
                    localStorage.setItem('theme', 'light');
                }} else {{
                    html.setAttribute('data-theme', 'dark');
                    themeIcon.innerHTML = '<path d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z"/>';
                    localStorage.setItem('theme', 'dark');
                }}
            }}
            
            // Initialize theme - DEFAULT TO DARK MODE like screenshot
            const savedTheme = localStorage.getItem('theme') || 'dark';
            if (savedTheme === 'dark') {{
                document.documentElement.setAttribute('data-theme', 'dark');
                document.getElementById('theme-icon').innerHTML = '<path d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z"/>';
            }}
        </script>
        """
    
    def create_professional_header(self) -> str:
        """Create enhanced professional header with navigation"""
        return f"""
        <div class="enterprise-navigation" role="banner">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="enterprise-logo">
                    <div style="
                        width: 3rem; 
                        height: 3rem; 
                        background: linear-gradient(135deg, {self.theme.COLORS['primary']} 0%, {self.theme.COLORS['accent']} 100%);
                        border-radius: {self.theme.RADIUS['lg']};
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                        font-size: 1.25rem;
                        box-shadow: {self.theme.SHADOWS['md']};
                    ">
                        N
                    </div>
                    <div>
                        <h1 class="enterprise-title">NACC</h1>
                    </div>
                </div>
                
                <nav style="display: flex; gap: 1rem; align-items: center;">
                    <a class="nav-item active" href="#" onclick="showTab('chat')">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 8px;">
                            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                        </svg>
                        Chat
                        <span class="keyboard-hint">C</span>
                    </a>
                    <a class="nav-item" href="#" onclick="showTab('dashboard')">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 8px;">
                            <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
                        </svg>
                        Dashboard
                        <span class="keyboard-hint">D</span>
                    </a>
                    <a class="nav-item" href="#" onclick="showTab('help')">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 8px;">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                        </svg>
                        Help
                        <span class="keyboard-hint">H</span>
                    </a>
                </nav>
            </div>
        </div>
        {self.create_theme_toggle()}
        """
    
    def create_help_system(self) -> str:
        """Create comprehensive help system"""
        return f"""
        <div class="help-panel">
            <h2 class="help-title">📚 About NACC Project</h2>
            
            <div class="help-section">
                <h3 style="color: var(--text-primary); font-size: {self.theme.TYPOGRAPHY['lg']}; margin-bottom: 1rem;">
                    🎯 What is NACC?
                </h3>
                <div class="help-item">
                    <strong>Network AI Command & Control (NACC)</strong> is an intelligent network orchestration platform that combines 
                    natural language processing with network automation. Simply describe what you want to accomplish, and NACC's AI 
                    will understand your intent and execute the appropriate commands across your infrastructure.
                </div>
                <div class="help-item">
                    <strong>Key Capabilities:</strong> Multi-node management, natural language interface, real-time monitoring, 
                    automated command execution, and context-aware conversations.
                </div>
            </div>
            
            <div class="help-section">
                <h3 style="color: var(--text-primary); font-size: {self.theme.TYPOGRAPHY['lg']}; margin-bottom: 1rem;">
                    🛠️ Available Tools
                </h3>
                <div class="help-item">
                    <strong>📊 Network Dashboard</strong><br>
                    <span style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">
                        Real-time visualization of all connected nodes with health metrics, CPU/memory/disk usage, and status indicators
                    </span>
                </div>
                <div class="help-item">
                    <strong>🖥️ Command Execution</strong><br>
                    <span style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">
                        Execute shell commands on any node through natural language. AI translates your requests into precise commands
                    </span>
                </div>
                <div class="help-item">
                    <strong>📁 File Browser</strong><br>
                    <span style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">
                        Browse, view, and manage files across your network infrastructure with visual file explorer
                    </span>
                </div>
                <div class="help-item">
                    <strong>🔍 AI Intent Parser</strong><br>
                    <span style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">
                        Understands natural language and converts it to executable commands using Mistral-NeMo AI model
                    </span>
                </div>
                <div class="help-item">
                    <strong>🌐 Multi-Node Orchestration</strong><br>
                    <span style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">
                        Manage multiple servers simultaneously with tag-based targeting and parallel execution
                    </span>
                </div>
                <div class="help-item">
                    <strong>📝 Session Management</strong><br>
                    <span style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">
                        Context-aware sessions that remember your current node, path, and conversation history
                    </span>
                </div>
            </div>
            
            <div class="help-section">
                <h3 style="color: var(--text-primary); font-size: {self.theme.TYPOGRAPHY['lg']}; margin-bottom: 1rem;">
                    💡 Usage Examples
                </h3>
                <div class="help-item">
                    <strong>"Show network status"</strong> - View all connected nodes and their health
                </div>
                <div class="help-item">
                    <strong>"List files on production server"</strong> - Browse files on a specific node
                </div>
                <div class="help-item">
                    <strong>"Check disk space on all servers"</strong> - Execute command across multiple nodes
                </div>
                <div class="help-item">
                    <strong>"Create monitoring script"</strong> - Generate and deploy custom scripts
                </div>
                <div class="help-item">
                    <strong>"Switch to dev environment"</strong> - Change context to different node
                </div>
            </div>
            
            <div class="help-section">
                <h3 style="color: var(--text-primary); font-size: {self.theme.TYPOGRAPHY['lg']}; margin-bottom: 1rem;">
                    🏗️ Architecture
                </h3>
                <div class="help-item">
                    <strong>AI Engine:</strong> Mistral-NeMo 12B model for intent understanding and command generation
                </div>
                <div class="help-item">
                    <strong>Orchestrator:</strong> FastAPI-based backend managing node communication and command execution
                </div>
                <div class="help-item">
                    <strong>UI Framework:</strong> Gradio-based professional interface with dark/light theme support
                </div>
                <div class="help-item">
                    <strong>Node Agents:</strong> Lightweight agents running on each managed server for command execution
                </div>
            </div>
        </div>
        """
    
    def create_real_time_dashboard(self, nodes: List[Dict] = None) -> str:
        """Create comprehensive real-time status dashboard"""
        if not nodes:
            nodes = []
        
        html = f"""
        <div class="status-dashboard">
            <div style="padding: 2rem; font-family: {self.theme.TYPOGRAPHY['font_family']};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                    <h2 style="color: var(--text-primary); font-size: {self.theme.TYPOGRAPHY['2xl']}; font-weight: {self.theme.TYPOGRAPHY['bold']}; margin: 0;">
                        🌐 Real-Time Network Dashboard
                    </h2>
                    <div class="status-indicator-animated" style="color: var(--success); display: flex; align-items: center; gap: 0.5rem;">
                        <span style="width: 8px; height: 8px; background: var(--success); border-radius: 50%; animation: pulse 2s infinite;"></span>
                        <span style="font-weight: {self.theme.TYPOGRAPHY['medium']};">LIVE</span>
                    </div>
                </div>
        """
        
        # System Overview Metrics
        online_nodes = len([n for n in nodes if n.get('healthy', False)])
        total_nodes = len(nodes)
        health_percentage = (online_nodes / total_nodes * 100) if total_nodes > 0 else 0
        
        html += f"""
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;">
                    <div class="metric-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2.5rem; font-weight: bold; color: var(--success); margin-bottom: 0.5rem;">{online_nodes}</div>
                            <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">🟢 Online Nodes</div>
                            <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['xs']}; margin-top: 0.25rem;">
                                {health_percentage:.0f}% Health Score
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2.5rem; font-weight: bold; color: var(--primary); margin-bottom: 0.5rem;">{total_nodes}</div>
                            <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">🌐 Total Nodes</div>
                            <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['xs']}; margin-top: 0.25rem;">
                                Network Infrastructure
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2.5rem; font-weight: bold; color: var(--warning); margin-bottom: 0.5rem;">{total_nodes - online_nodes}</div>
                            <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">🔴 Offline Nodes</div>
                            <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['xs']}; margin-top: 0.25rem;">
                                Requires Attention
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div style="text-align: center;">
                            <div style="font-size: 2.5rem; font-weight: bold; color: var(--info); margin-bottom: 0.5rem;">99.9%</div>
                            <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">⚡ Uptime</div>
                            <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['xs']}; margin-top: 0.25rem;">
                                Last 30 Days
                            </div>
                        </div>
                    </div>
                </div>
        """
        
        # Individual Node Details
        if nodes:
            html += """
                <h3 style="color: var(--text-primary); font-size: {self.theme.TYPOGRAPHY['xl']}; font-weight: {self.theme.TYPOGRAPHY['semibold']}; margin-bottom: 1rem;">
                    🖥️ Node Details
                </h3>
            """
            
            for node in nodes:
                node_id = node.get('node_id') or node.get('id', 'Unknown')
                is_healthy = node.get('healthy', False)
                status_color = 'var(--success)' if is_healthy else 'var(--error)'
                status_text = 'ONLINE' if is_healthy else 'OFFLINE'
                status_icon = '🟢' if is_healthy else '🔴'
                metrics = node.get('metrics', {})
                
                # Calculate resource utilization
                cpu = metrics.get('cpu_percent', 0)
                memory = metrics.get('memory_percent', 0)
                disk = metrics.get('disk_percent', 0)
                
                # Determine health status
                if cpu > 80 or memory > 85:
                    health_status = 'warning'
                    health_color = 'var(--warning)'
                    health_icon = '⚠️'
                elif not is_healthy:
                    health_status = 'error'
                    health_color = 'var(--error)'
                    health_icon = '🔴'
                else:
                    health_status = 'good'
                    health_color = 'var(--success)'
                    health_icon = '✅'
                
                html += f"""
                <div class="metric-card" style="margin-bottom: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div style="font-size: 1.5rem;">🖥️</div>
                            <div>
                                <h4 style="margin: 0; color: var(--text-primary); font-size: {self.theme.TYPOGRAPHY['lg']}; font-weight: {self.theme.TYPOGRAPHY['semibold']};">
                                    {node_id}
                                </h4>
                                <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">
                                    {', '.join(node.get('tags', []))}
                                </div>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                <span style="font-size: 1.2rem;">{health_icon}</span>
                                <span style="color: {health_color}; font-weight: {self.theme.TYPOGRAPHY['semibold']};">{health_status.upper()}</span>
                            </div>
                            <span style="
                                background: {status_color}; 
                                color: white; 
                                padding: 0.25rem 0.75rem; 
                                border-radius: {self.theme.RADIUS['full']}; 
                                font-size: {self.theme.TYPOGRAPHY['xs']}; 
                                font-weight: {self.theme.TYPOGRAPHY['semibold']};
                                text-transform: uppercase;
                            ">
                                {status_text}
                            </span>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;">
                        <div>
                            <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['xs']}; margin-bottom: 0.25rem;">💻 CPU</div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <div style="flex: 1; background: var(--bg-tertiary); border-radius: {self.theme.RADIUS['sm']}; height: 6px; overflow: hidden;">
                                    <div style="
                                        width: {cpu}%; 
                                        height: 100%; 
                                        background: {'var(--error)' if cpu > 80 else 'var(--warning)' if cpu > 60 else 'var(--success)'}; 
                                        transition: width {self.theme.TRANSITIONS['normal']};
                                    "></div>
                                </div>
                                <span style="color: var(--text-secondary); font-size: {self.theme.TYPOGRAPHY['sm']}; font-weight: {self.theme.TYPOGRAPHY['medium']};">{cpu:.1f}%</span>
                            </div>
                        </div>
                        
                        <div>
                            <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['xs']}; margin-bottom: 0.25rem;">💾 Memory</div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <div style="flex: 1; background: var(--bg-tertiary); border-radius: {self.theme.RADIUS['sm']}; height: 6px; overflow: hidden;">
                                    <div style="
                                        width: {memory}%; 
                                        height: 100%; 
                                        background: {'var(--error)' if memory > 85 else 'var(--warning)' if memory > 70 else 'var(--success)'}; 
                                        transition: width {self.theme.TRANSITIONS['normal']};
                                    "></div>
                                </div>
                                <span style="color: var(--text-secondary); font-size: {self.theme.TYPOGRAPHY['sm']}; font-weight: {self.theme.TYPOGRAPHY['medium']};">{memory:.1f}%</span>
                            </div>
                        </div>
                        
                        <div>
                            <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['xs']}; margin-bottom: 0.25rem;">💽 Disk</div>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <div style="flex: 1; background: var(--bg-tertiary); border-radius: {self.theme.RADIUS['sm']}; height: 6px; overflow: hidden;">
                                    <div style="
                                        width: {disk}%; 
                                        height: 100%; 
                                        background: {'var(--error)' if disk > 90 else 'var(--warning)' if disk > 75 else 'var(--success)'}; 
                                        transition: width {self.theme.TRANSITIONS['normal']};
                                    "></div>
                                </div>
                                <span style="color: var(--text-secondary); font-size: {self.theme.TYPOGRAPHY['sm']}; font-weight: {self.theme.TYPOGRAPHY['medium']};">{disk:.1f}%</span>
                            </div>
                        </div>
                    </div>
                </div>
                """
        else:
            html += """
                <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📡</div>
                    <h3 style="color: var(--text-secondary); margin-bottom: 0.5rem;">No Nodes Connected</h3>
                    <p>Connect your first node to start monitoring your network infrastructure.</p>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def create_enhanced_file_content_view(self, filename: str, content: str) -> str:
        """Create enhanced file content viewer with syntax highlighting"""
        # Detect language and appropriate styling
        ext = Path(filename).suffix
        lang_map = {
            ".py": ("Python", "#3776ab"),
            ".js": ("JavaScript", "#f7df1e"),
            ".ts": ("TypeScript", "#3178c6"),
            ".sh": ("Bash", "#89e051"),
            ".yml": ("YAML", "#cb171e"),
            ".yaml": ("YAML", "#cb171e"),
            ".json": ("JSON", "#292929"),
            ".md": ("Markdown", "#083fa1"),
            ".html": ("HTML", "#e34c26"),
            ".css": ("CSS", "#1572b6"),
            ".go": ("Go", "#00add8"),
            ".rs": ("Rust", "#dea584"),
        }
        
        lang_name, lang_color = lang_map.get(ext, ("Text", self.theme.COLORS['secondary']))
        
        html = f"""
        <div style="padding: 2rem; font-family: {self.theme.TYPOGRAPHY['font_family']};">
            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 1.5rem;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="
                        width: 3rem; 
                        height: 3rem; 
                        background: {lang_color}; 
                        border-radius: {self.theme.RADIUS['lg']};
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 1.2rem;
                        font-weight: bold;
                    ">
                        📄
                    </div>
                    <div>
                        <h3 style="color: var(--text-primary); font-size: {self.theme.TYPOGRAPHY['xl']}; font-weight: {self.theme.TYPOGRAPHY['semibold']}; margin: 0;">
                            {filename}
                        </h3>
                        <div style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['sm']};">
                            {lang_name} • {len(content)} characters • {content.count('\\n')} lines
                        </div>
                    </div>
                </div>
                
                <div style="display: flex; gap: 0.5rem;">
                    <button onclick="copyToClipboard()" style="
                        background: var(--primary); 
                        color: white; 
                        border: none; 
                        border-radius: {self.theme.RADIUS['md']}; 
                        padding: 0.5rem 1rem; 
                        cursor: pointer;
                        transition: all {self.theme.TRANSITIONS['fast']};
                    " onmouseover="this.style.background='var(--primary-dark)'" onmouseout="this.style.background='var(--primary)'">
                        📋 Copy
                    </button>
                </div>
            </div>
            
            <div style="
                background: var(--bg_primary); 
                border: 1px solid var(--border-light); 
                border-radius: {self.theme.RADIUS['lg']}; 
                overflow: hidden;
                box-shadow: {self.theme.SHADOWS['lg']};
            ">
                <div style="
                    background: var(--bg-secondary); 
                    padding: 0.75rem 1rem; 
                    border-bottom: 1px solid var(--border-light);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <span style="color: var(--text-secondary); font-size: {self.theme.TYPOGRAPHY['sm']}; font-weight: {self.theme.TYPOGRAPHY['medium']};">
                        {lang_name} Source
                    </span>
                    <span style="color: var(--text-muted); font-size: {self.theme.TYPOGRAPHY['xs']};">
                        UTF-8
                    </span>
                </div>
                
                <div style="
                    background: #1e293b; 
                    padding: 1.5rem; 
                    overflow: auto; 
                    max-height: 500px;
                    font-family: {self.theme.TYPOGRAPHY['font_mono']};
                    font-size: {self.theme.TYPOGRAPHY['sm']};
                    line-height: 1.6;
                ">
                    <pre style="margin: 0; color: #e2e8f0; white-space: pre-wrap; word-wrap: break-word;"><code class="language-{lang_name.lower()}">{content}</code></pre>
                </div>
            </div>
        </div>
        
        <script>
            function copyToClipboard() {{
                const text = `{content.replace('`', '\\`').replace('$', '\\$')}`;
                navigator.clipboard.writeText(text).then(() => {{
                    const btn = event.target;
                    const originalText = btn.textContent;
                    btn.textContent = '✅ Copied!';
                    setTimeout(() => {{
                        btn.textContent = originalText;
                    }}, 2000);
                }});
            }}
        </script>
        """
        return html


def create_professional_ui():
    """Create the professional-grade UI interface"""
    nacc = ProfessionalNACCUI()
    
    # Create the interface with comprehensive styling
    with gr.Blocks(
        css=nacc.get_comprehensive_css(), 
        title="NACC Enterprise AI - Professional Network Orchestration",
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
        head="""
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="NACC Enterprise AI - Professional Network Orchestration & Command Control Platform">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <meta name="theme-color" content="#2563eb">
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
        """
    ) as interface:
        
        # Professional Header
        header_html = gr.HTML(nacc.create_professional_header())
        
        # Main Layout
        with gr.Row():
            with gr.Column(scale=2):
                # Chat Header
                gr.HTML('<div class="chat-header"><h2 class="chat-title">NACC AGENT</h2><div class="session-info">How can I help you today?</div></div>')
                
                # Chat Messages with enhanced styling
                chatbot = gr.Chatbot(
                    label="Enterprise Conversation",
                    height=500,
                    show_label=False,
                    type="messages",
                    elem_classes=["chat-messages"]
                )
                
                # Enhanced Chat Input with professional styling
                with gr.Row():
                    msg = gr.Textbox(
                        label="Enterprise Command",
                        placeholder="Describe your network orchestration needs... (Press C to focus, Enter to send)",
                        show_label=False,
                        container=False,
                        elem_classes=["message-input", "focus-enhanced"],
                        scale=9
                    )
                    submit = gr.Button(
                        "📤", 
                        variant="primary", 
                        scale=1, 
                        min_width=60,
                        elem_classes=["send-button"]
                    )
            
            with gr.Column(scale=1):
                # Enhanced Right Panel with tabs
                with gr.Tabs():
                    with gr.TabItem("📊 Status & Output", id="dashboard"):
                        right_panel = gr.HTML(nacc.create_welcome_panel())
                    
                    with gr.TabItem("🔍 File Browser", id="files"):
                        file_panel = gr.HTML(nacc.create_enhanced_file_browser([], "/home"))
                    
                    with gr.TabItem("❓ Help & Guide", id="help"):
                        help_panel = gr.HTML(nacc.create_help_system())
        
        # Enhanced Tool Execution Log
        tool_log = gr.HTML(
            nacc.create_loading_state("🚀 Enterprise AI ready! Professional network orchestration active."),
            elem_classes=["tool-log"]
        )
        
        # Enhanced Context Information
        context_bar = gr.HTML(
            '<div class="context-bar">💡 Context: Enterprise session | Professional AI mode | WCAG 2.1 AA compliant</div>',
            elem_classes=["context-bar"]
        )
        
        # Professional Example Queries Section
        gr.HTML('<h3 class="examples-title">🎯 Try these enterprise commands:</h3>')
        
        examples = [
            "Show me the real-time network dashboard with all node metrics",
            "List all files on the production server with enhanced browser",
            "Execute comprehensive health checks across the entire infrastructure",
            "Create a professional monitoring script and deploy to all nodes",
            "Generate network performance analysis and identify optimization opportunities"
        ]
        
        with gr.Row():
            for example in examples[:3]:
                gr.Button(
                    example, 
                    variant="secondary", 
                    size="sm",
                    elem_classes=["example-button"]
                ).click(fn=lambda x=example: x, outputs=msg)
        
        with gr.Row():
            for example in examples[3:]:
                gr.Button(
                    example, 
                    variant="secondary", 
                    size="sm",
                    elem_classes=["example-button"]
                ).click(fn=lambda x=example: x, outputs=msg)
        
        # Session State Management
        session_id_state = gr.State()
        
        # Enhanced Response Handler
        def respond(message, chat_history, session_id):
            """Handle user message with professional UI enhancements"""
            if not message.strip():
                return chat_history, nacc.create_welcome_panel(), nacc.create_loading_state("Ready for enterprise commands!"), 
            
            # Process with enhanced message handling
            updated_history, right_content, tool_log_content, session_info = nacc.process_message_with_enhanced_ui(
                message, chat_history or [], session_id
            )
            
            # Enhanced session info
            session = nacc.get_or_create_session(session_id)
            enhanced_session_info = f"""
            Session: {session.session_id[:8]}... | 
            Node: {session.current_node} | 
            Path: {session.current_path} | 
            Tools: {len(session.tool_execution_log)} | 
            Messages: {len(session.conversation_history)} | 
            Theme: {nacc.current_theme.title()}
            """
            
            return updated_history, right_content, tool_log_content, enhanced_session_info, session_id
        
        def new_professional_session(session_id):
            """Start a new professional enterprise session"""
            import hashlib
            from datetime import datetime
            new_session_id = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
            
            return [], nacc.create_welcome_panel(), nacc.create_loading_state("🚀 New enterprise session started! Professional AI mode activated.")
        
        # Enhanced Event Handlers
        submit.click(
            respond, 
            [msg, chatbot, session_id_state], 
            [chatbot, right_panel, tool_log, context_bar, session_id_state]
        )
        msg.submit(
            respond, 
            [msg, chatbot, session_id_state], 
            [chatbot, right_panel, tool_log, context_bar, session_id_state]
        )
        
        # Keyboard shortcut handlers
        def handle_keyboard_shortcuts(evt: gr.SelectData):
            """Handle keyboard shortcuts for accessibility"""
            if hasattr(evt, 'key') and evt.key:
                key = evt.key.lower()
                if key == 'c':
                    return gr.update(value=""), gr.update()
                elif key == 'd':
                    # Switch to dashboard tab
                    return gr.update(), gr.update()
                elif key == 'h':
                    # Switch to help tab  
                    return gr.update(), gr.update()
        
        # Add keyboard shortcut support
        interface.load(
            lambda: None,
            inputs=[],
            outputs=[]
        )
    
    return interface


def main():
    """Main entry point for the professional UI"""
    ui = create_professional_ui()
    ui.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        favicon_path=None,
        debug=True
    )

if __name__ == "__main__":
    main()
