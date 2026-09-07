"""
Formatting and Design Engine for Resume Tailor.
Manages global and per-section PDF styling presets, CSS variable compilation,
and persistent user formatting preferences.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import json

CONFIG_FILE_PATH = Path(__file__).resolve().parent.parent / "data" / "formatting_config.json"

DEFAULT_THEME: Dict[str, Any] = {
    "preset_name": "Executive Modern",
    # Page & Geometry
    "page_margin_top": "0.45in",
    "page_margin_bottom": "0.45in",
    "page_margin_left": "0.5in",
    "page_margin_right": "0.5in",
    "show_page_numbers": True,
    "page_number_position": "bottom-right",
    "page_number_font_size": "8pt",
    "page_number_color": "#718096",
    # Typography
    "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    "font_size_base": "9.5pt",
    "line_height_base": "1.35",
    "font_size_name": "20pt",
    "font_weight_name": "700",
    "name_uppercase": True,
    "font_size_headline": "10.5pt",
    "font_size_section_title": "10.5pt",
    "font_size_role_title": "10pt",
    "font_size_dates_location": "8.8pt",
    "font_size_skills_table": "8.8pt",
    "font_size_bullets": "9.2pt",
    # Palette
    "color_accent": "#2563eb",
    "color_headings": "#0f172a",
    "color_body": "#334155",
    "color_subtle": "#64748b",
    "color_border": "#cbd5e1",
    "color_header_bottom_border": "#2d3748",
    # Header Section
    "header_alignment": "center",
    "header_margin_bottom": "12px",
    "header_border_bottom_width": "1.5px",
    "contact_font_size": "8.5pt",
    "contact_sep": "|",
    # Professional Summary
    "summary_alignment": "justify",
    "summary_line_height": "1.4",
    "summary_margin_bottom": "11px",
    # Core Technical & Compliance Competencies Table
    "skills_label_width": "172px",
    "skills_row_padding": "2px",
    "skills_separator": "•",
    "skills_label_color": "#0f172a",
    "skills_values_alignment": "justify",
    # Experience & Bullets
    "role_margin_bottom": "9px",
    "role_title_color": "#0f172a",
    "company_name_color": "#2563eb",
    "role_skills_size": "8.3pt",
    "show_role_competencies": True,
    "bullet_indent": "16px",
    "bullet_spacing": "3px",
    "bullet_line_height": "1.35",
    "bullet_alignment": "justify",
    "bullet_symbol": "disc",
    # Section Dividers & Headings
    "section_title_uppercase": True,
    "section_title_letter_spacing": "0.8px",
    "section_title_border_width": "1px",
    "section_title_margin_bottom": "6px",
    "section_spacing": "11px",
    # Custom CSS Override
    "custom_css": "",
}

THEME_PRESETS: Dict[str, Dict[str, Any]] = {
    "Executive Modern": {
        **DEFAULT_THEME,
        "preset_name": "Executive Modern",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        "color_accent": "#2563eb",
        "color_headings": "#0f172a",
        "color_body": "#334155",
        "page_margin_top": "0.45in",
        "page_margin_bottom": "0.45in",
        "page_margin_left": "0.5in",
        "page_margin_right": "0.5in",
        "font_size_base": "9.5pt",
        "skills_label_width": "172px",
        "bullet_spacing": "3px",
    },
    "Federal & Defense Dense": {
        **DEFAULT_THEME,
        "preset_name": "Federal & Defense Dense",
        "font_family": "'Times New Roman', Times, 'Liberation Serif', Georgia, serif",
        "color_accent": "#1e293b",
        "color_headings": "#000000",
        "color_body": "#1f2937",
        "color_subtle": "#4b5563",
        "color_border": "#9ca3af",
        "color_header_bottom_border": "#111827",
        "page_margin_top": "0.4in",
        "page_margin_bottom": "0.4in",
        "page_margin_left": "0.45in",
        "page_margin_right": "0.45in",
        "font_size_base": "9.0pt",
        "line_height_base": "1.28",
        "font_size_name": "18pt",
        "font_size_headline": "10pt",
        "font_size_section_title": "10pt",
        "font_size_role_title": "9.5pt",
        "font_size_bullets": "8.8pt",
        "skills_label_width": "165px",
        "skills_row_padding": "1px",
        "bullet_spacing": "2px",
        "role_margin_bottom": "7px",
        "section_spacing": "8px",
        "company_name_color": "#111827",
    },
    "Compact 2-Page Fit": {
        **DEFAULT_THEME,
        "preset_name": "Compact 2-Page Fit",
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        "color_accent": "#1d4ed8",
        "color_headings": "#0f172a",
        "color_body": "#334155",
        "page_margin_top": "0.35in",
        "page_margin_bottom": "0.35in",
        "page_margin_left": "0.4in",
        "page_margin_right": "0.4in",
        "font_size_base": "8.9pt",
        "line_height_base": "1.26",
        "font_size_name": "18pt",
        "font_size_headline": "9.8pt",
        "font_size_section_title": "9.8pt",
        "font_size_role_title": "9.3pt",
        "font_size_bullets": "8.6pt",
        "header_margin_bottom": "8px",
        "skills_label_width": "160px",
        "skills_row_padding": "1.5px",
        "bullet_spacing": "1.5px",
        "role_margin_bottom": "6px",
        "section_spacing": "7px",
    },
    "Tech Minimalist": {
        **DEFAULT_THEME,
        "preset_name": "Tech Minimalist",
        "font_family": "'Inter', 'Segoe UI', system-ui, sans-serif",
        "color_accent": "#047857",
        "color_headings": "#111827",
        "color_body": "#374151",
        "color_subtle": "#6b7280",
        "header_alignment": "left",
        "name_uppercase": False,
        "font_size_name": "22pt",
        "font_weight_name": "800",
        "page_margin_top": "0.5in",
        "page_margin_bottom": "0.5in",
        "page_margin_left": "0.55in",
        "page_margin_right": "0.55in",
        "font_size_base": "9.3pt",
        "line_height_base": "1.38",
        "bullet_symbol": "square",
        "company_name_color": "#047857",
        "skills_label_color": "#065f46",
    }
}


def load_formatting_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load local custom formatting config, falling back to DEFAULT_THEME."""
    target_path = path or CONFIG_FILE_PATH
    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                merged = dict(DEFAULT_THEME)
                merged.update(saved)
                return merged
        except Exception as e:
            print(f"Failed loading formatting config from {target_path}: {e}")
    return dict(DEFAULT_THEME)


def save_formatting_config(config: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Save formatting configuration to local JSON file."""
    target_path = path or CONFIG_FILE_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def compile_theme_css(config: Dict[str, Any]) -> str:
    """
    Compile configuration dictionary into CSS Custom Properties (:root)
    and dynamic structural CSS rules for WeasyPrint HTML template.
    """
    cfg = dict(DEFAULT_THEME)
    cfg.update(config)

    # Convert bullet symbol to list-style-type
    symbol_map = {
        "disc": "disc",
        "circle": "circle",
        "square": "square",
        "hyphen": "'- '",
        "none": "none"
    }
    list_style = symbol_map.get(cfg.get("bullet_symbol", "disc"), "disc")

    # Name text transform
    name_transform = "uppercase" if cfg.get("name_uppercase", True) else "none"
    section_title_transform = "uppercase" if cfg.get("section_title_uppercase", True) else "none"

    # Page number rule
    if cfg.get("show_page_numbers", True):
        page_num_rule = f"""
    @page {{
      @{cfg.get('page_number_position', 'bottom-right')} {{
        content: counter(page) " of " counter(pages);
        font-size: {cfg.get('page_number_font_size', '8pt')};
        color: {cfg.get('page_number_color', '#718096')};
        font-family: {cfg.get('font_family')};
      }}
    }}
        """
    else:
        page_num_rule = """
    @page {
      @bottom-right { content: none; }
      @bottom-center { content: none; }
      @bottom-left { content: none; }
    }
        """

    css_output = f"""
    {page_num_rule}

    :root {{
      --page-margin-top: {cfg.get('page_margin_top', '0.45in')};
      --page-margin-bottom: {cfg.get('page_margin_bottom', '0.45in')};
      --page-margin-left: {cfg.get('page_margin_left', '0.5in')};
      --page-margin-right: {cfg.get('page_margin_right', '0.5in')};

      --font-body: {cfg.get('font_family')};
      --font-size-base: {cfg.get('font_size_base', '9.5pt')};
      --line-height-base: {cfg.get('line_height_base', '1.35')};

      --color-accent: {cfg.get('color_accent', '#2563eb')};
      --color-headings: {cfg.get('color_headings', '#0f172a')};
      --color-body: {cfg.get('color_body', '#334155')};
      --color-subtle: {cfg.get('color_subtle', '#64748b')};
      --color-border: {cfg.get('color_border', '#cbd5e1')};
      --color-header-border: {cfg.get('color_header_bottom_border', '#2d3748')};

      --header-align: {cfg.get('header_alignment', 'center')};
      --header-margin-bottom: {cfg.get('header_margin_bottom', '12px')};
      --header-border-width: {cfg.get('header_border_bottom_width', '1.5px')};
      --contact-align: {'flex-start' if cfg.get('header_alignment') == 'left' else 'center'};
      --role-skills-display: {'block' if cfg.get('show_role_competencies', True) else 'none'};
      --font-size-name: {cfg.get('font_size_name', '20pt')};
      --font-weight-name: {cfg.get('font_weight_name', '700')};
      --name-transform: {name_transform};
      --font-size-headline: {cfg.get('font_size_headline', '10.5pt')};
      --contact-font-size: {cfg.get('contact_font_size', '8.5pt')};

      --summary-align: {cfg.get('summary_alignment', 'justify')};
      --summary-line-height: {cfg.get('summary_line_height', '1.4')};
      --summary-margin-bottom: {cfg.get('summary_margin_bottom', '11px')};

      --skills-label-width: {cfg.get('skills_label_width', '172px')};
      --skills-row-padding: {cfg.get('skills_row_padding', '2px')};
      --skills-label-color: {cfg.get('skills_label_color', '#0f172a')};
      --skills-val-align: {cfg.get('skills_values_alignment', 'justify')};
      --font-size-skills-table: {cfg.get('font_size_skills_table', '8.8pt')};

      --section-spacing: {cfg.get('section_spacing', '11px')};
      --section-title-size: {cfg.get('font_size_section_title', '10.5pt')};
      --section-title-transform: {section_title_transform};
      --section-title-spacing: {cfg.get('section_title_letter_spacing', '0.8px')};
      --section-title-border-width: {cfg.get('section_title_border_width', '1px')};
      --section-title-margin-bottom: {cfg.get('section_title_margin_bottom', '6px')};

      --role-margin-bottom: {cfg.get('role_margin_bottom', '9px')};
      --role-title-size: {cfg.get('font_size_role_title', '10pt')};
      --role-title-color: {cfg.get('role_title_color', '#0f172a')};
      --company-color: {cfg.get('company_name_color', '#2563eb')};
      --dates-loc-size: {cfg.get('font_size_dates_location', '8.8pt')};
      --role-skills-size: {cfg.get('role_skills_size', '8.3pt')};

      --bullet-indent: {cfg.get('bullet_indent', '16px')};
      --bullet-spacing: {cfg.get('bullet_spacing', '3px')};
      --bullet-line-height: {cfg.get('bullet_line_height', '1.35')};
      --bullet-align: {cfg.get('bullet_alignment', 'justify')};
      --bullet-size: {cfg.get('font_size_bullets', '9.2pt')};
      --bullet-style: {list_style};
    }}
    """

    # Append user custom CSS override if provided
    user_css = cfg.get("custom_css", "").strip()
    if user_css:
        css_output += f"\n    /* User Custom CSS Overrides */\n    {user_css}\n"

    return css_output
