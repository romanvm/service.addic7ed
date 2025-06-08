#!/usr/bin/env python3

import os
import sys
import re
import xml.etree.ElementTree as ET
from glob import glob


def find_language_dirs(addon_dir):
    """Find all language resource directories"""
    pattern = os.path.join(addon_dir, 'resources', 'language', 'resource.language.*')
    return glob(pattern)


def get_language_code_from_dir(dir_path):
    """Extract language code from directory path"""
    # Extract the code from the directory name (resource.language.xx_yy)
    lang_code = os.path.basename(dir_path).split('.')[-1]
    # Convert to the format used in addon.xml (xx_YY)
    if '_' in lang_code:
        ll, cc = lang_code.split('_')
        return f"{ll}_{cc.upper()}"
    return lang_code.upper()


def read_addon_xml(addon_dir):
    """Read and parse addon.xml file"""
    addon_xml_path = os.path.join(addon_dir, 'addon.xml')
    try:
        tree = ET.parse(addon_xml_path)
        return tree
    except (ET.ParseError, FileNotFoundError) as e:
        print(f"Error reading {addon_xml_path}: {e}")
        sys.exit(1)


def extract_addon_strings(tree):
    """Extract summary and description strings from addon.xml"""
    strings = {}
    root = tree.getroot()
    metadata = root.find('.//extension[@point="xbmc.addon.metadata"]')

    if metadata is None:
        print("No metadata found in addon.xml")
        return strings

    # Process summaries
    for summary in metadata.findall('summary'):
        lang = summary.get('lang', 'en_GB')
        text = summary.text or ""
        if lang not in strings:
            strings[lang] = {}
        strings[lang]['summary'] = text

    # Process descriptions
    for description in metadata.findall('description'):
        lang = description.get('lang', 'en_GB')
        text = description.text or ""
        if lang not in strings:
            strings[lang] = {}
        strings[lang]['description'] = text

    return strings


def read_po_file(po_path):
    """Read and parse a .po file"""
    if not os.path.isfile(po_path):
        print(f"Warning: PO file not found: {po_path}")
        return {}

    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract existing translation segments for addon.xml
    segments = {}

    # Look for summary translation
    summary_match = re.search(
        r'msgctxt "addon\.xml:summary"\s*\nmsgid "(.*)"\s*\nmsgstr "(.*)"', 
        content, 
        re.DOTALL
    )
    if summary_match:
        segments['summary'] = {
            'msgid': summary_match.group(1),
            'msgstr': summary_match.group(2)
        }

    # Look for description translation
    desc_match = re.search(
        r'msgctxt "addon\.xml:description"\s*\nmsgid "(.*)"\s*\nmsgstr "(.*)"', 
        content, 
        re.DOTALL
    )
    if desc_match:
        segments['description'] = {
            'msgid': desc_match.group(1),
            'msgstr': desc_match.group(2)
        }

    return segments, content


def update_po_file(po_path, en_strings, lang_strings, is_en=False):
    """Update .po file with addon.xml strings"""
    segments, content = read_po_file(po_path)
    updated_content = content

    # Process summary
    if 'summary' in segments:
        # Replace existing summary translation
        en_summary = en_strings.get('en_GB', {}).get('summary', '')
        lang_summary = lang_strings.get('summary', '')

        # For English strings, msgstr should be empty
        msgstr = '' if is_en else lang_summary

        # Replace existing translation segment
        updated_content = re.sub(
            r'msgctxt "addon\.xml:summary"\s*\nmsgid ".*"\s*\nmsgstr ".*"',
            f'msgctxt "addon.xml:summary"\nmsgid "{en_summary}"\nmsgstr "{msgstr}"',
            updated_content,
            flags=re.DOTALL
        )
    else:
        # Add new summary translation segment
        en_summary = en_strings.get('en_GB', {}).get('summary', '')
        msgstr = '' if is_en else lang_strings.get('summary', '')
        new_segment = f'\n\nmsgctxt "addon.xml:summary"\nmsgid "{en_summary}"\nmsgstr "{msgstr}"'
        updated_content += new_segment

    # Process description
    if 'description' in segments:
        # Replace existing description translation
        en_description = en_strings.get('en_GB', {}).get('description', '')
        lang_description = lang_strings.get('description', '')

        # For English strings, msgstr should be empty
        msgstr = '' if is_en else lang_description

        # Replace existing translation segment
        updated_content = re.sub(
            r'msgctxt "addon\.xml:description"\s*\nmsgid ".*"\s*\nmsgstr ".*"',
            f'msgctxt "addon.xml:description"\nmsgid "{en_description}"\nmsgstr "{msgstr}"',
            updated_content,
            flags=re.DOTALL
        )
    else:
        # Add new description translation segment
        en_description = en_strings.get('en_GB', {}).get('description', '')
        msgstr = '' if is_en else lang_strings.get('description', '')
        new_segment = f'\n\nmsgctxt "addon.xml:description"\nmsgid "{en_description}"\nmsgstr "{msgstr}"'
        updated_content += new_segment

    # Write updated content back to the file
    with open(po_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)


def extract_translations_from_po(po_path):
    """Extract addon.xml translations from a .po file"""
    segments, _ = read_po_file(po_path)
    translations = {}

    if 'summary' in segments and segments['summary']['msgstr']:
        translations['summary'] = segments['summary']['msgstr']

    if 'description' in segments and segments['description']['msgstr']:
        translations['description'] = segments['description']['msgstr']

    return translations


def update_addon_xml(tree, translations_by_lang, addon_dir):
    """Update addon.xml with translations from .po files"""
    root = tree.getroot()
    metadata = root.find('.//extension[@point="xbmc.addon.metadata"]')

    if metadata is None:
        print("No metadata found in addon.xml")
        return

    # Process each language
    for lang, translations in translations_by_lang.items():
        # Skip English source language
        if lang.lower() == 'en_gb':
            continue

        # Update or create summary tag
        if 'summary' in translations:
            summary = metadata.find(f'summary[@lang="{lang}"]')
            if summary is not None:
                summary.text = translations['summary']
            else:
                summary = ET.SubElement(metadata, 'summary')
                summary.set('lang', lang)
                summary.text = translations['summary']

        # Update or create description tag
        if 'description' in translations:
            description = metadata.find(f'description[@lang="{lang}"]')
            if description is not None:
                description.text = translations['description']
            else:
                description = ET.SubElement(metadata, 'description')
                description.set('lang', lang)
                description.text = translations['description']

    # Write updated XML back to the file
    addon_xml_path = os.path.join(addon_dir, 'addon.xml')
    tree.write(addon_xml_path, encoding='UTF-8', xml_declaration=True)


def dump_translations(addon_dir):
    """Copy strings from addon.xml to .po files"""
    print(f"Dumping translations from {addon_dir}/addon.xml to .po files...")

    # Read addon.xml
    tree = read_addon_xml(addon_dir)

    # Extract strings from addon.xml
    addon_strings = extract_addon_strings(tree)

    # Find all language directories
    lang_dirs = find_language_dirs(addon_dir)

    for lang_dir in lang_dirs:
        # Get language code from directory name
        lang_code = get_language_code_from_dir(lang_dir)
        print(f"Processing language: {lang_code}")

        # Find corresponding strings.po file
        po_path = os.path.join(lang_dir, 'strings.po')

        # Check if it's English (source language)
        is_en = lang_code.lower() == 'en_gb'

        # Get addon.xml strings for this language
        lang_strings = addon_strings.get(lang_code, {})

        # Update the .po file
        update_po_file(po_path, addon_strings, lang_strings, is_en)

    print("Translation dump completed.")


def load_translations(addon_dir):
    """Copy translations from .po files to addon.xml"""
    print(f"Loading translations from .po files to {addon_dir}/addon.xml...")

    # Read addon.xml
    tree = read_addon_xml(addon_dir)

    # Find all language directories except English
    lang_dirs = find_language_dirs(addon_dir)

    # Collect translations from all .po files
    translations_by_lang = {}

    for lang_dir in lang_dirs:
        # Get language code from directory name
        lang_code = get_language_code_from_dir(lang_dir)
        print(f"Processing language: {lang_code}")

        # Skip English source language for loading
        if lang_code.lower() == 'en_gb':
            continue

        # Find corresponding strings.po file
        po_path = os.path.join(lang_dir, 'strings.po')

        # Extract translations from .po file
        translations = extract_translations_from_po(po_path)

        if translations:
            translations_by_lang[lang_code] = translations

    # Update addon.xml with translations
    update_addon_xml(tree, translations_by_lang, addon_dir)

    print("Translation load completed.")


def show_usage():
    """Show script usage information"""
    print("Usage: python sync_addon_info_translations.py <option> [addon_dir]")
    print("Options:")
    print("  -d, --dump-translations  : Copy strings from addon.xml to .po files")
    print("  -l, --load-translations  : Copy translations from .po files to addon.xml")
    print("Parameters:")
    print("  addon_dir                : Path to the addon directory (default: current directory)")
    sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        show_usage()

    option = sys.argv[1]

    # Set addon directory - default to current directory if not specified
    addon_dir = sys.argv[2] if len(sys.argv) == 3 else '.'

    if option in ('-d', '--dump-translations'):
        dump_translations(addon_dir)
    elif option in ('-l', '--load-translations'):
        load_translations(addon_dir)
    else:
        show_usage()


if __name__ == '__main__':
    main()
