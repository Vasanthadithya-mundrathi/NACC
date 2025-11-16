"""
NACC Enterprise UI - Professional AI Agent Interface
Enterprise-grade conversational interface with modern design, accessibility, and advanced features.
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

# Orchestrator URL
ORCHESTRATOR_URL = os.getenv("NACC_ORCHESTRATOR_URL", "http://127.0.0.1:8888")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnterpriseTheme:
    """Enterprise design system with consistent styling tokens"""
    
    # Color Palette - Professional Enterprise Theme
    COLORS = {
        # Primary Brand Colors
        'primary': '#2563eb',      # Professional Blue
        'primary_light': '#3b82f6', # Light Blue
        'primary_dark': '#1d4ed8',  # Dark Blue
        
        # Secondary Colors
        'secondary': '#64748b',     # Slate Gray
        'accent': '#0ea5e9',        # Sky Blue
        
        # Semantic Colors
        'success': '#059669',       # Emerald Green
        'warning': '#d97706',       # Amber
        'error': '#dc2626',         # Red
        'info': '#0284c7',          # Cyan
        
        # Neutral Colors
        'gray_50': '#f8fafc',
        'gray_100': '#f1f5f9',
        'gray_200': '#e2e8f0',
        'gray_300': '#cbd5e1',
        'gray_400': '#94a3b8',
        'gray_500': '#64748b',
        'gray_600': '#475569',
        'gray_700': '#334155',
        'gray_800': '#1e293b',
        'gray_900': '#0f172a',
        
        # Background Colors
        'bg_primary': '#ffffff',
        'bg_secondary': '#f8fafc',
        'bg_tertiary': '#f1f5f9',
        
        # Text Colors
        'text_primary': '#0f172a',
        'text_secondary': '#475569',
        'text_muted': '#64748b',
        
        # Border Colors
        'border_light': '#e2e8f0',
        'border_medium': '#cbd5e1',
        'border_dark': '#94a3b8',
    }
    
    # Typography Scale
    TYPOGRAPHY = {
        'font_family': "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif",
        'font_mono': "'JetBrains Mono', 'Fira Code', 'Monaco', 'Consolas', monospace",
        
        # Font Sizes
        'xs': '0.75rem',    # 12px
        'sm': '0.875rem',   # 14px
        'base': '1rem',     # 16px
        'lg': '1.125rem',   # 18px
        'xl': '1.25rem',    # 20px
        '2xl': '1.5rem',    # 24px
        '3xl': '1.875rem',  # 30px
        '4xl': '2.25rem',   # 36px
        
        # Font Weights
        'normal': '400',
        'medium': '500',
        'semibold': '600',
        'bold': '700',
    }
    
    # Spacing Scale
    SPACING = {
        'xs': '0.25rem',    # 4px
        'sm': '0.5rem',     # 8px
        'md': '1rem',       # 16px
        'lg': '1.5rem',     # 24px
        'xl': '2rem',       # 32px
        '2xl': '3rem',      # 48px
        '3xl': '4rem',      # 64px
    }
    
    # Border Radius
    RADIUS = {
        'sm': '0.375rem',   # 6px
        'md': '0.5rem',     # 8px
        'lg': '0.75rem',    # 12px
        'xl': '1rem',       # 16px
        '2xl': '1.5rem',    # 24px
        'full': '9999px',
    }
    
    # Shadows
    SHADOWS = {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    }
    
    # Transitions
    TRANSITIONS = {
        'fast': '150ms cubic-bezier(0.4, 0, 0.2, 1)',
        'normal': '300ms cubic-bezier(0.4, 0, 0.2, 1)',
        'slow': '500ms cubic-bezier(0.4, 0, 0.2, 1)',
    }


class EnterpriseNACCUI(NACCConversationUI):
    """Enhanced NACC UI with enterprise-grade features"""
    
    def __init__(self):
        super().__init__()
        self.theme = EnterpriseTheme()
        self.accessibility_mode = False
        
    def get_enterprise_css(self) -> str:
        """Generate comprehensive enterprise CSS with design system"""
        return f"""
        /* Import Inter font for professional typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');
        
        :root {{
            /* CSS Custom Properties for Dynamic Theming */
            --primary: {self.theme.COLORS['primary']};
            --primary-light: {self.theme.COLORS['primary_light']};
            --primary-dark: {self.theme.COLORS['primary_dark']};
            --success: {self.theme.COLORS['success']};
            --warning: {self.theme.COLORS['warning']};
            --error: {self.theme.COLORS['error']};
            --info: {self.theme.COLORS['info']};
            
            --bg-primary: {self.theme.COLORS['bg_primary']};
            --bg-secondary: {self.theme.COLORS['bg_secondary']};
            --bg-tertiary: {self.theme.COLORS['bg_tertiary']};
            
            --text-primary: {self.theme.COLORS['text_primary']};
            --text-secondary: {self.theme.COLORS['text_secondary']};
            --text-muted: {self.theme.COLORS['text_muted']};
            
            --border-light: {self.theme.COLORS['border_light']};
            --border-medium: {self.theme.COLORS['border_medium']};
            --border-dark: {self.theme.COLORS['border_dark']};
            
            --shadow-sm: {self.theme.SHADOWS['sm']};
            --shadow-md: {self.theme.SHADOWS['md']};
            --shadow-lg: {self.theme.SHADOWS['lg']};
            --shadow-xl: {self.theme.SHADOWS['xl']};
            
            --radius-sm: {self.theme.RADIUS['sm']};
            --radius-md: {self.theme.RADIUS['md']};
            --radius-lg: {self.theme.RADIUS['lg']};
            --radius-xl: {self.theme.RADIUS['xl']};
            
            --transition-fast: {self.theme.TRANSITIONS['fast']};
            --transition-normal: {self.theme.TRANSITIONS['normal']};
            --transition-slow: {self.theme.TRANSITIONS['slow']};
        }}
        
        /* Global Styles */
        .gradio-container {{
            font-family: {self.theme.TYPOGRAPHY['font_family']} !important;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
            min-height: 100vh !important;
        }}
        
        /* Header Styling */
        .enterprise-header {{
            background: var(--bg-primary) !important;
            border-bottom: 1px solid var(--border-light) !important;
            box-shadow: var(--shadow-sm) !important;
            padding: 1rem 2rem !important;
            margin-bottom: 2rem !important;
        }}
        
        .enterprise-logo {{
            display: flex !important;
            align-items: center !important;
            gap: 1rem !important;
        }}
        
        .enterprise-title {{
            font-size: {self.theme.TYPOGRAPHY['2xl']} !important;
            font-weight: {self.theme.TYPOGRAPHY['bold']} !important;
            color: var(--text-primary) !important;
            margin: 0 !important;
        }}
        
        .enterprise-subtitle {{
            font-size: {self.theme.TYPOGRAPHY['sm']} !important;
            color: var(--text-muted) !important;
            margin: 0 !important;
            font-weight: {self.theme.TYPOGRAPHY['medium']} !important;
        }}
        
        /* Main Layout */
        .enterprise-main {{
            display: grid !important;
            grid-template-columns: 1fr 400px !important;
            gap: 2rem !important;
            padding: 0 2rem !important;
            max-width: 1600px !important;
            margin: 0 auto !important;
        }}
        
        @media (max-width: 1200px) {{
            .enterprise-main {{
                grid-template-columns: 1fr !important;
                gap: 1.5rem !important;
            }}
        }}
        
        /* Chat Interface Styling */
        .chat-container {{
            background: var(--bg-primary) !important;
            border-radius: var(--radius-xl) !important;
            box-shadow: var(--shadow-lg) !important;
            border: 1px solid var(--border-light) !important;
            overflow: hidden !important;
            height: calc(100vh - 200px) !important;
            min-height: 600px !important;
            display: flex !important;
            flex-direction: column !important;
        }}
        
        .chat-header {{
            background: var(--bg-secondary) !important;
            border-bottom: 1px solid var(--border-light) !important;
            padding: 1.5rem 2rem !important;
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
        }}
        
        .chat-title {{
            font-size: {self.theme.TYPOGRAPHY['xl']} !important;
            font-weight: {self.theme.TYPOGRAPHY['semibold']} !important;
            color: var(--text-primary) !important;
            margin: 0 !important;
        }}
        
        .session-info {{
            font-size: {self.theme.TYPOGRAPHY['sm']} !important;
            color: var(--text-muted) !important;
        }}
        
        .chat-messages {{
            flex: 1 !important;
            overflow-y: auto !important;
            padding: 2rem !important;
            scroll-behavior: smooth !important;
        }}
        
        /* Message Styling */
        .message {{
            margin-bottom: 1.5rem !important;
            animation: slideIn 0.3s ease-out !important;
        }}
        
        @keyframes slideIn {{
            from {{
                opacity: 0 !important;
                transform: translateY(10px) !important;
            }}
            to {{
                opacity: 1 !important;
                transform: translateY(0) !important;
            }}
        }}
        
        .user-message {{
            display: flex !important;
            justify-content: flex-end !important;
        }}
        
        .user-bubble {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%) !important;
            color: white !important;
            padding: 1rem 1.5rem !important;
            border-radius: var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg) !important;
            max-width: 70% !important;
            word-wrap: break-word !important;
            box-shadow: var(--shadow-md) !important;
        }}
        
        .bot-message {{
            display: flex !important;
            justify-content: flex-start !important;
        }}
        
        .bot-bubble {{
            background: var(--bg-primary) !important;
            color: var(--text-primary) !important;
            padding: 1.5rem 2rem !important;
            border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) var(--radius-sm) !important;
            border: 1px solid var(--border-light) !important;
            max-width: 70% !important;
            box-shadow: var(--shadow-sm) !important;
        }}
        
        .bot-bubble:hover {{
            box-shadow: var(--shadow-md) !important;
            transition: box-shadow var(--transition-fast) !important;
        }}
        
        /* Chat Input Area - ENHANCED VISIBILITY */
        .chat-input-area {{
            background: var(--bg-primary) !important;
            border-top: 2px solid var(--border-medium) !important;
            padding: 1.5rem 2rem !important;
        }}
        
        .input-container {{
            display: flex !important;
            gap: 1rem !important;
            align-items: flex-end !important;
        }}
        
        /* Enhanced Input Field with Maximum Contrast */
        .message-input {{
            flex: 1 !important;
            border: 2px solid var(--border-dark) !important;
            border-radius: var(--radius-lg) !important;
            padding: 1rem 1.5rem !important;
            font-size: 1rem !important;
            font-family: {self.theme.TYPOGRAPHY['font_family']} !important;
            background: #ffffff !important;
            color: #000000 !important;
            font-weight: 500 !important;
            outline: none !important;
            transition: all var(--transition-fast) !important;
            resize: none !important;
            min-height: 3rem !important;
            max-height: 8rem !important;
            line-height: 1.5 !important;
        }}
        
        /* Strong placeholder visibility */
        .message-input::placeholder {{
            color: #64748b !important;
            font-weight: 400 !important;
            opacity: 1 !important;
        }}
        
        .message-input:focus {{
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.15) !important;
            background: #ffffff !important;
        }}
        
        .send-button {{
            background: var(--primary) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: var(--radius-lg) !important;
            padding: 1rem 1.5rem !important;
            font-weight: {self.theme.TYPOGRAPHY['semibold']} !important;
            font-size: 0.95rem !important;
            cursor: pointer !important;
            transition: all var(--transition-fast) !important;
            min-width: 80px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        
        .send-button:hover {{
            background: var(--primary-dark) !important;
            transform: translateY(-2px) !important;
            box-shadow: var(--shadow-lg) !important;
        }}
        
        .send-button:active {{
            transform: translateY(0) !important;
        }}
        
        /* Right Panel Styling */
        .right-panel {{
            background: var(--bg-primary) !important;
            border-radius: var(--radius-xl) !important;
            box-shadow: var(--shadow-lg) !important;
            border: 1px solid var(--border-light) !important;
            overflow: hidden !important;
            height: calc(100vh - 200px) !important;
            min-height: 600px !important;
            display: flex !important;
            flex-direction: column !important;
        }}
        
        .panel-header {{
            background: var(--bg-secondary) !important;
            border-bottom: 1px solid var(--border-light) !important;
            padding: 1.5rem 2rem !important;
        }}
        
        .panel-title {{
            font-size: {self.theme.TYPOGRAPHY['lg']} !important;
            font-weight: {self.theme.TYPOGRAPHY['semibold']} !important;
            color: var(--text-primary) !important;
            margin: 0 !important;
        }}
        
        .panel-content {{
            flex: 1 !important;
            overflow-y: auto !important;
            padding: 2rem !important;
        }}
        
        /* Status Cards */
        .status-card {{
            background: var(--bg-primary) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-lg) !important;
            padding: 1.5rem !important;
            margin-bottom: 1rem !important;
            transition: all var(--transition-fast) !important;
        }}
        
        .status-card:hover {{
            box-shadow: var(--shadow-md) !important;
            transform: translateY(-1px) !important;
        }}
        
        .status-indicator {{
            display: inline-flex !important;
            align-items: center !important;
            gap: 0.5rem !important;
            font-weight: {self.theme.TYPOGRAPHY['medium']} !important;
        }}
        
        .status-online {{
            color: var(--success) !important;
        }}
        
        .status-offline {{
            color: var(--error) !important;
        }}
        
        .status-warning {{
            color: var(--warning) !important;
        }}
        
        /* Tool Execution Log */
        .tool-log {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
            border: 1px solid #fbbf24 !important;
            border-left: 4px solid var(--warning) !important;
            border-radius: var(--radius-md) !important;
            padding: 1rem 1.5rem !important;
            font-family: {self.theme.TYPOGRAPHY['font_mono']} !important;
            font-size: {self.theme.TYPOGRAPHY['sm']} !important;
            margin: 1rem 0 !important;
            box-shadow: var(--shadow-sm) !important;
        }}
        
        /* Context Bar */
        .context-bar {{
            background: linear-gradient(135deg, #e0e7ff 0%, #ddd6fe 100%) !important;
            border: 1px solid #a5b4fc !important;
            border-left: 4px solid var(--primary) !important;
            border-radius: var(--radius-md) !important;
            padding: 0.75rem 1rem !important;
            font-size: {self.theme.TYPOGRAPHY['sm']} !important;
            margin: 1rem 0 !important;
            color: var(--text-secondary) !important;
        }}
        
        /* Loading States */
        .loading {{
            display: flex !important;
            align-items: center !important;
            gap: 0.5rem !important;
            color: var(--text-muted) !important;
        }}
        
        .loading-spinner {{
            width: 1rem !important;
            height: 1rem !important;
            border: 2px solid var(--border-light) !important;
            border-top: 2px solid var(--primary) !important;
            border-radius: 50% !important;
            animation: spin 1s linear infinite !important;
        }}
        
        @keyframes spin {{
            to {{
                transform: rotate(360deg) !important;
            }}
        }}
        
        /* Example Queries */
        .examples-container {{
            background: var(--bg-primary) !important;
            border-radius: var(--radius-xl) !important;
            box-shadow: var(--shadow-lg) !important;
            border: 1px solid var(--border-light) !important;
            padding: 2rem !important;
            margin-top: 2rem !important;
        }}
        
        .examples-title {{
            font-size: {self.theme.TYPOGRAPHY['lg']} !important;
            font-weight: {self.theme.TYPOGRAPHY['semibold']} !important;
            color: var(--text-primary) !important;
            margin-bottom: 1rem !important;
        }}
        
        .example-button {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-md) !important;
            padding: 0.75rem 1rem !important;
            font-size: {self.theme.TYPOGRAPHY['sm']} !important;
            color: var(--text-secondary) !important;
            cursor: pointer !important;
            transition: all var(--transition-fast) !important;
            margin: 0.5rem !important;
        }}
        
        .example-button:hover {{
            background: var(--primary) !important;
            color: white !important;
            transform: translateY(-1px) !important;
            box-shadow: var(--shadow-md) !important;
        }}
        
        /* Accessibility Improvements */
        @media (prefers-reduced-motion: reduce) {{
            * {{
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }}
        }}
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {{
            .user-bubble {{
                border: 2px solid currentColor !important;
            }}
            
            .bot-bubble {{
                border: 2px solid var(--border-dark) !important;
            }}
        }}
        
        /* Focus management for accessibility */
        .focus-visible {{
            outline: 2px solid var(--primary) !important;
            outline-offset: 2px !important;
        }}
        
        /* Mobile Responsive */
        @media (max-width: 768px) {{
            .enterprise-main {{
                padding: 0 1rem !important;
            }}
            
            .chat-container,
            .right-panel {{
                height: calc(100vh - 150px) !important;
                min-height: 500px !important;
            }}
            
            .chat-messages {{
                padding: 1rem !important;
            }}
            
            .user-bubble,
            .bot-bubble {{
                max-width: 85% !important;
            }}
        }}
        
        /* Print styles */
        @media print {{
            .send-button,
            .example-button {{
                display: none !important;
            }}
            
            .chat-container,
            .right-panel {{
                box-shadow: none !important;
                border: 1px solid #ccc !important;
            }}
        }}
        """

    def create_enterprise_header(self) -> str:
        """Create clean enterprise header HTML"""
        return f"""
        <div class="enterprise-header" role="banner">
            <div class="enterprise-logo">
                <div style="
                    width: 2.5rem; 
                    height: 2.5rem; 
                    background: linear-gradient(135deg, {self.theme.COLORS['primary']} 0%, {self.theme.COLORS['accent']} 100%);
                    border-radius: {self.theme.RADIUS['lg']};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 1.125rem;
                ">
                    AI
                </div>
                <div>
                    <h1 class="enterprise-title">Enterprise AI Agent</h1>
                </div>
            </div>
        </div>
        """

    def create_welcome_panel(self) -> str:
        """Create clean welcome panel for right sidebar"""
        return f"""
        <div style="padding: 3rem 2rem; text-align: center; font-family: {self.theme.TYPOGRAPHY['font_family']};">
            <div style="
                width: 4rem; 
                height: 4rem; 
                background: linear-gradient(135deg, {self.theme.COLORS['primary']} 0%, {self.theme.COLORS['accent']} 100%);
                border-radius: {self.theme.RADIUS['2xl']};
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 2rem;
                color: white;
                font-size: 2rem;
                box-shadow: {self.theme.SHADOWS['lg']};
            ">
                🤖
            </div>
            
            <h2 style="
                color: {self.theme.COLORS['text_primary']}; 
                font-size: {self.theme.TYPOGRAPHY['xl']}; 
                font-weight: {self.theme.TYPOGRAPHY['semibold']}; 
                margin-bottom: 1rem;
            ">
                AI Agent Ready
            </h2>
            
            <p style="
                color: {self.theme.COLORS['text_secondary']}; 
                font-size: {self.theme.TYPOGRAPHY['base']}; 
                line-height: 1.6; 
                max-width: 350px; 
                margin: 0 auto 2rem;
            ">
                Start a conversation to orchestrate network operations
            </p>
            
            <div style="display: grid; gap: 0.75rem; max-width: 300px; margin: 0 auto;">
                <div style="
                    background: var(--bg-secondary);
                    border: 1px solid var(--border-light);
                    border-radius: var(--radius-md);
                    padding: 0.75rem 1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                ">
                    <span style="color: var(--success); font-size: 1.25rem;">✓</span>
                    <span style="color: var(--text-secondary); font-size: 0.9rem;">File Operations</span>
                </div>
                <div style="
                    background: var(--bg-secondary);
                    border: 1px solid var(--border-light);
                    border-radius: var(--radius-md);
                    padding: 0.75rem 1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                ">
                    <span style="color: var(--success); font-size: 1.25rem;">✓</span>
                    <span style="color: var(--text-secondary); font-size: 0.9rem;">Command Execution</span>
                </div>
                <div style="
                    background: var(--bg-secondary);
                    border: 1px solid var(--border-light);
                    border-radius: var(--radius-md);
                    padding: 0.75rem 1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                ">
                    <span style="color: var(--success); font-size: 1.25rem;">✓</span>
                    <span style="color: var(--text-secondary); font-size: 0.9rem;">Network Management</span>
                    </div>
                </div>
            </div>
        </div>
        """

    def create_enhanced_file_browser(self, files: List[str], current_path: str) -> str:
        """Create enhanced file browser with modern design"""
        html = f"""
        <div style="padding: 2rem; font-family: {self.theme.TYPOGRAPHY['font_family']};">
            <div style="margin-bottom: 1.5rem;">
                <h3 style="color: {self.theme.COLORS['text_primary']}; font-size: {self.theme.TYPOGRAPHY['xl']}; font-weight: {self.theme.TYPOGRAPHY['semibold']}; margin-bottom: 0.5rem;">
                    📂 {current_path}
                </h3>
                <div style="color: {self.theme.COLORS['text_muted']}; font-size: {self.theme.TYPOGRAPHY['sm']};">
                    {len(files)} items
                </div>
            </div>
            
            <div style="
                background: {self.theme.COLORS['bg_secondary']}; 
                border-radius: {self.theme.RADIUS['lg']}; 
                padding: 1rem; 
                border: 1px solid {self.theme.COLORS['border_light']};
                max-height: 400px;
                overflow-y: auto;
            ">
        """
        
        for file in files:
            # Use proper SVG icons instead of emoji
            is_folder = "/" in file or not "." in file
            icon_svg = f"""
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style="color: {self.theme.COLORS['primary']};">
                    <path d="M10 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2h-8l-2-2z"/>
                </svg>
            """ if is_folder else f"""
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style="color: {self.theme.COLORS['text_secondary']};">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                </svg>
            """
            
            file_style = f"""
                <div style="
                    padding: 0.75rem 1rem;
                    margin: 0.5rem 0;
                    background: {self.theme.COLORS['bg_primary']};
                    border-radius: {self.theme.RADIUS['md']};
                    border: 1px solid {self.theme.COLORS['border_light']};
                    cursor: pointer;
                    transition: all {self.theme.TRANSITIONS['fast']};
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                "
                onmouseover="this.style.background='{self.theme.COLORS['bg_tertiary']}'; this.style.transform='translateX(4px)'"
                onmouseout="this.style.background='{self.theme.COLORS['bg_primary']}'; this.style.transform='translateX(0)'">
                    {icon_svg}
                    <span style="
                        font-family: {self.theme.TYPOGRAPHY['font_mono']};
                        color: {self.theme.COLORS['text_primary']};
                        font-size: {self.theme.TYPOGRAPHY['sm']};
                    ">
                        {file}
                    </span>
                </div>
            """
            html += file_style
        
        html += "</div></div>"
        return html

    def create_status_dashboard(self, nodes: List[Dict]) -> str:
        """Create enterprise status dashboard"""
        html = f"""
        <div style="padding: 2rem; font-family: {self.theme.TYPOGRAPHY['font_family']};">
            <h3 style="color: {self.theme.COLORS['text_primary']}; font-size: {self.theme.TYPOGRAPHY['xl']}; font-weight: {self.theme.TYPOGRAPHY['semibold']}; margin-bottom: 1.5rem;">
                🌐 Network Status Dashboard
            </h3>
        """
        
        # System overview
        online_nodes = len([n for n in nodes if n.get('healthy', False)])
        total_nodes = len(nodes)
        
        html += f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
            <div class="status-card">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold; color: {self.theme.COLORS['success']};">{online_nodes}</div>
                    <div style="color: {self.theme.COLORS['text_muted']}; font-size: {self.theme.TYPOGRAPHY['sm']};">Online Nodes</div>
                </div>
            </div>
            <div class="status-card">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold; color: {self.theme.COLORS['primary']};">{total_nodes}</div>
                    <div style="color: {self.theme.COLORS['text_muted']}; font-size: {self.theme.TYPOGRAPHY['sm']};">Total Nodes</div>
                </div>
            </div>
            <div class="status-card">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: bold; color: {self.theme.COLORS['warning']};">{total_nodes - online_nodes}</div>
                    <div style="color: {self.theme.COLORS['text_muted']}; font-size: {self.theme.TYPOGRAPHY['sm']};">Offline Nodes</div>
                </div>
            </div>
        </div>
        """
        
        # Individual node status
        for node in nodes:
            node_id = node.get('node_id') or node.get('id', 'Unknown')
            is_healthy = node.get('healthy', False)
            status_color = self.theme.COLORS['success'] if is_healthy else self.theme.COLORS['error']
            status_text = "ONLINE" if is_healthy else "OFFLINE"
            metrics = node.get('metrics', {})
            
            html += f"""
            <div style="
                background: {self.theme.COLORS['bg_primary']}; 
                border-radius: {self.theme.RADIUS['lg']}; 
                padding: 1.5rem; 
                margin-bottom: 1rem; 
                border-left: 4px solid {status_color}; 
                box-shadow: {self.theme.SHADOWS['sm']};
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: {self.theme.COLORS['text_primary']}; font-size: {self.theme.TYPOGRAPHY['lg']}; font-weight: {self.theme.TYPOGRAPHY['semibold']};">
                        🖥️ {node_id}
                    </h4>
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
                <div style="color: {self.theme.COLORS['text_secondary']}; font-size: {self.theme.TYPOGRAPHY['sm']}; line-height: 1.6;">
                    <div>🏷️ <strong>Tags:</strong> {', '.join(node.get('tags', []))}</div>
            """
            
            if metrics:
                html += f"""
                    <div style="margin-top: 0.5rem;">
                        <div>💻 <strong>CPU:</strong> {metrics.get('cpu_percent', 0):.1f}%</div>
                        <div>💾 <strong>Memory:</strong> {metrics.get('memory_percent', 0):.1f}%</div>
                        <div>💽 <strong>Disk:</strong> {metrics.get('disk_percent', 0):.1f}%</div>
                    </div>
                """
            
            html += """
                </div>
            </div>
            """
        
        html += "</div>"
        return html

    def create_error_message(self, error: str, context: str = "") -> str:
        """Create professional error message"""
        return f"""
        <div style="
            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
            border: 1px solid #f87171; 
            border-left: 4px solid {self.theme.COLORS['error']}; 
            border-radius: {self.theme.RADIUS['lg']}; 
            padding: 1.5rem; 
            margin: 1rem 0;
            font-family: {self.theme.TYPOGRAPHY['font_family']};
        ">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem;">❌</span>
                <strong style="color: {self.theme.COLORS['error']};">Error</strong>
            </div>
            <div style="color: {self.theme.COLORS['text_secondary']}; font-size: {self.theme.TYPOGRAPHY['sm']};">
                {error}
                {f'<br><br><strong>Context:</strong> {context}' if context else ''}
            </div>
        </div>
        """

    def create_loading_state(self, message: str = "Processing...") -> str:
        """Create professional loading state"""
        return f"""
        <div style="
            display: flex; 
            align-items: center; 
            justify-content: center; 
            gap: 1rem; 
            padding: 2rem;
            color: {self.theme.COLORS['text_muted']};
            font-family: {self.theme.TYPOGRAPHY['font_family']};
        ">
            <div class="loading-spinner"></div>
            <span>{message}</span>
        </div>
        """

    def process_message_with_enhanced_ui(self, user_message: str, chat_history: List, session_id: str) -> Tuple[List, str, str, str]:
        """Enhanced message processing with enterprise UI"""
        if not user_message.strip():
            return chat_history, self.create_welcome_panel(), "", "", session_id
        
        # Process with existing logic
        updated_history, right_content, tool_log = self.process_message(user_message, chat_history or [], session_id)
        
        # Update session info
        session = self.get_or_create_session(session_id)
        session_info = f"""
        Session: {session.session_id[:8]}... | 
        Node: {session.current_node} | 
        Path: {session.current_path} | 
        Tools: {len(session.tool_execution_log)} | 
        Messages: {len(session.conversation_history)}
        """
        
        return updated_history, right_content, tool_log, session_info, session_id


def create_enterprise_ui():
    """Create the enterprise-grade UI interface"""
    nacc = EnterpriseNACCUI()
    
    # Create the interface with enterprise styling
    with gr.Blocks(
        css=nacc.get_enterprise_css(), 
        title="Enterprise AI Agent",
        theme=gr.themes.Soft(
            primary_hue="blue", 
            neutral_hue="slate",
            text_size="lg",
            font=["Inter", "system-ui", "sans-serif"]
        ),
        head="""
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        """
    ) as interface:
        
        # Enterprise Header
        header_html = gr.HTML(nacc.create_enterprise_header())
        
        # Main Layout
        with gr.Row():
            with gr.Column(scale=2):
                # Chat Container
                chat_container = gr.HTML('<div class="chat-container">')
                
                # Chat Header - Simplified
                gr.HTML('<div class="chat-header"><h2 class="chat-title">AI Assistant</h2></div>')
                
                # Chat Messages
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=500,
                    show_label=False,
                    type="messages",
                    elem_classes=["chat-messages"]
                )
                
                # Chat Input - Enhanced for Maximum Visibility
                with gr.Row():
                    msg = gr.Textbox(
                        label="",
                        placeholder="Type your message here...",
                        show_label=False,
                        container=False,
                        elem_classes=["message-input"],
                        scale=9,
                        lines=1,
                        max_lines=4
                    )
                    submit = gr.Button(
                        "Send", 
                        variant="primary", 
                        scale=1, 
                        min_width=80,
                        elem_classes=["send-button"]
                    )
                
                chat_container_end = gr.HTML('</div>')
            
            with gr.Column(scale=1):
                # Right Panel
                right_panel = gr.HTML(nacc.create_welcome_panel(), label="📊 Status & Output")
        
        # Status Display (Simplified)
        tool_log = gr.HTML(
            nacc.create_loading_state("Ready"),
            elem_classes=["tool-log"]
        )
        
        # Quick Actions
        gr.Markdown("### 💡 Quick Actions")
        
        examples = [
            "Show network topology",
            "List files",
            "Health check"
        ]
        
        with gr.Row():
            for example in examples:
                gr.Button(
                    example, 
                    variant="secondary", 
                    size="sm",
                    elem_classes=["example-button"]
                ).click(fn=lambda x=example: x, outputs=msg)
        
        # Session State
        session_id_state = gr.State()
        
        # Response handler
        def respond(message, chat_history, session_id):
            """Handle user message with enhanced UI"""
            if not message.strip():
                return chat_history, nacc.create_welcome_panel(), nacc.create_loading_state("Ready"), session_id
            
            updated_history, right_content, tool_log_content, session_info, session_id = nacc.process_message_with_enhanced_ui(
                message, chat_history or [], session_id
            )
            
            return updated_history, right_content, tool_log_content, session_id
        
        def new_chat(session_id):
            """Start a new enterprise chat session"""
            import hashlib
            from datetime import datetime
            new_session_id = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
            
            return [], nacc.create_welcome_panel(), nacc.create_loading_state("New session started"), new_session_id
        
        # Event Handlers
        submit.click(
            respond, 
            [msg, chatbot, session_id_state], 
            [chatbot, right_panel, tool_log, session_id_state]
        )
        msg.submit(
            respond, 
            [msg, chatbot, session_id_state], 
            [chatbot, right_panel, tool_log, session_id_state]
        )
    
    return interface


def main():
    """Main entry point for the enterprise UI"""
    ui = create_enterprise_ui()
    ui.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        favicon_path=None
    )

if __name__ == "__main__":
    main()
