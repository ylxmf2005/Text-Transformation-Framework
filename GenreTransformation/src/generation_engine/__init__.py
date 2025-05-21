"""
Generation Engine Module

This module produces high-quality final text based on the selected and potentially
human-adjusted semantic core, final target attributes, and final high-level instructions.
"""

from .generation_processor import GenerationEngine

__all__ = ['GenerationEngine']
