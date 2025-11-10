#!/usr/bin/env python3

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def find_language_dirs(addon_dir):
    """Find all language resource directories"""
    resources_path = addon_dir / 'resources' / 'language'
    return list(resources_path.glob('resource.language.*'))


def get_language_code_from_dir(dir_path):
    """Extract language code from directory path"""
    # Extract the code from the directory name (resource.language.xx_yy)
    lang_code = dir_path.name.split('.')[-1]
    # Convert to the format used in addon.xml (xx_YY)
    if '_' in lang_code:
        ll, cc = lang_code.split('_')
        return f"{ll}_{cc.upper()}"
    return lang_code.lower()


def read_addon_xml(addon_dir):
    """Read and parse addon.xml file"""
    addon_xml_path = addon_dir / 'addon.xml'
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


def read_po_file(po_file):
    """Read and parse a .po file"""
    if not po_file.is_file():
        print(f"Warning: PO file not found: {po_file}")
        return {}

    content = po_file.read_text(encoding='utf-8')

    # Extract existing translation segments for addon.xml
    segments = {}

    # Look for summary translation
    summary_match = re.search(
        r'msgctxt "addon\.xml:summary"\s*?\nmsgid "([^"]*)"\s*?\nmsgstr "([^"]*)"',
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
        r'msgctxt "addon\.xml:description"\s*?\nmsgid "([^"]*)"\s*?\nmsgstr "([^"]*)"',
        content,
        re.DOTALL
    )
    if desc_match:
        segments['description'] = {
            'msgid': desc_match.group(1),
            'msgstr': desc_match.group(2)
        }

    return segments, content


def update_po_file(po_file, en_strings, lang_strings, is_en=False):
    """Update .po file with addon.xml strings"""
    segments, content = read_po_file(po_file)
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
            r'msgctxt "addon\.xml:summary"\s*?\nmsgid "[^"]*"\s*?\nmsgstr "[^"]*"',
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
            r'msgctxt "addon\.xml:description"\s*?\nmsgid "[^"]*"\s*?\nmsgstr "[^"]*"',
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
    po_file.write_text(updated_content, encoding='utf-8')


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
        raise SystemExit(1)

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
                # Find all existing summary tags and insert after the last one
                summaries = metadata.findall('summary')
                if summaries:
                    last_summary = summaries[-1]
                    children = list(metadata)
                    insert_position = children.index(last_summary) + 1

                    new_summary = ET.Element('summary')
                    new_summary.set('lang', lang)
                    new_summary.text = translations['summary']
                    new_summary.tail = '\n  '
                    metadata.insert(insert_position, new_summary)
                else:
                    raise RuntimeError('No summary tag found in addon.xml')

        # Update or create description tag
        if 'description' in translations:
            description = metadata.find(f'description[@lang="{lang}"]')
            if description is not None:
                description.text = translations['description']
            else:
                # Find all existing description tags and insert after the last one
                descriptions = metadata.findall('description')
                if descriptions:
                    last_description = descriptions[-1]
                    children = list(metadata)
                    insert_position = children.index(last_description) + 1

                    new_description = ET.Element('description')
                    new_description.set('lang', lang)
                    new_description.text = translations['description']
                    new_description.tail = '\n  '
                    metadata.insert(insert_position, new_description)
                else:
                    raise RuntimeError('No description tag found in addon.xml')

    # Get XML as string with double quotes in declaration
    xml_string = ET.tostring(root, encoding='unicode')
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_string

    # Write to file
    addon_xml_path = addon_dir / 'addon.xml'
    with open(addon_xml_path, 'w', encoding='UTF-8') as f:
        f.write(xml_content)


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
        po_file = lang_dir / 'strings.po'

        # Check if it's English (source language)
        is_en = lang_code.lower() == 'en_gb'

        # Get addon.xml strings for this language
        lang_strings = addon_strings.get(lang_code, {})

        # Update the .po file
        update_po_file(po_file, addon_strings, lang_strings, is_en)

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
        po_path = lang_dir / 'strings.po'

        # Extract translations from .po file
        translations = extract_translations_from_po(po_path)

        if translations:
            translations_by_lang[lang_code] = translations

    # Update addon.xml with translations
    update_addon_xml(tree, translations_by_lang, addon_dir)

    print("Translation load completed.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Sync addon information translations between addon.xml and strings.po files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sync_addon_info_translations.py -d <addon directory>
  python sync_addon_info_translations.py --load-translations <addon directory>
        """
    )

    # Create mutually exclusive group for the operation
    operation_group = parser.add_mutually_exclusive_group(required=True)
    operation_group.add_argument(
        '-d', '--dump-translations',
        action='store_true',
        help='Copy strings from addon.xml to .po files'
    )
    operation_group.add_argument(
        '-l', '--load-translations',
        action='store_true',
        help='Copy translations from .po files to addon.xml'
    )

    # Add addon directory argument
    parser.add_argument(
        'addon_dir',
        nargs='?',
        default='.',
        help='Path to the addon directory (default: current directory)'
    )

    args = parser.parse_args()

    addon_dir = BASE_DIR / args.addon_dir
    if args.dump_translations:
        dump_translations(addon_dir)
    elif args.load_translations:
        load_translations(addon_dir)


if __name__ == '__main__':
    main()
