import os
import re
import streamlit as st
import langdetect
import anthropic
from typing import Dict, Any

def has_chinese_characters(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def detect_language_sections(text: str) -> Dict[str, Any]:
    """Analyze different sections of the document for language detection."""
    # Split into paragraphs for granular analysis
    paragraphs = text.split('\n\n')
    sections_analysis = {
        'primary_language': 'en',
        'has_mixed_content': False,
        'sections_requiring_translation': [],
        'translation_confidence': 1.0
    }

    try:
        # Check for Chinese characters first
        has_chinese = has_chinese_characters(text)
        if has_chinese:
            sections_analysis['has_mixed_content'] = True
            sections_analysis['primary_language'] = 'zh'
            sections_analysis['translation_confidence'] = 0.9

        # Detect primary language from full text
        try:
            detected_lang = langdetect.detect(text)
            if detected_lang != 'en':
                sections_analysis['primary_language'] = detected_lang
        except:
            if has_chinese:
                sections_analysis['primary_language'] = 'zh'
            else:
                sections_analysis['primary_language'] = 'en'

        # Analyze individual paragraphs
        non_english_sections = []
        paragraph_languages = set()

        for i, para in enumerate(paragraphs):
            if len(para.strip()) > 20:  # Lower threshold to catch shorter sections
                # Check for Chinese characters first
                if has_chinese_characters(para):
                    non_english_sections.append({
                        'index': i,
                        'language': 'zh',
                        'preview': para[:100] + '...' if len(para) > 100 else para
                    })
                    paragraph_languages.add('zh')
                    continue

                try:
                    lang = langdetect.detect(para)
                    paragraph_languages.add(lang)
                    if lang != 'en':
                        non_english_sections.append({
                            'index': i,
                            'language': lang,
                            'preview': para[:100] + '...' if len(para) > 100 else para
                        })
                except:
                    continue

        sections_analysis['has_mixed_content'] = len(paragraph_languages) > 1 or has_chinese
        sections_analysis['sections_requiring_translation'] = non_english_sections
        sections_analysis['translation_confidence'] = 0.8 if has_chinese else (
            1.0 if len(paragraph_languages) == 1 else 0.9
        )

    except Exception as e:
        st.error(f"Error in language detection: {str(e)}")
        sections_analysis['translation_confidence'] = 0.5

    return sections_analysis

def translate_text(text: str, source_lang: str) -> str:
    """Translate text to English using Claude."""
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    prompt = f"""
    Translate the following text from {source_lang} to English, maintaining the original formatting and structure.
    Preserve any technical terms, numbers, and special characters.

    Text to translate:
    {text}

    Provide only the translated text in your response, without any additional commentary.
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text if response.content else text
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return text
