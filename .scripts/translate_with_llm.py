#!/usr/bin/env python3
"""

================================================================================
BILARA PALI-TO-ENGLISH LLM TRANSLATOR
================================================================================

WHAT IS THIS?

This is an LLM translator using the best Pali translation model available, 
gemma-2-mitra-it, created by the Buddhist NLP team at https://dharmamitra.org.

The Abhidhamma has never been fully translated into English. With this script, 
you can translate the entire Abhidhamma with a single command:

    python3 translate_with_llm.py --uid abhidhamma

On a dedicated HuggingFace Inference Endpoint with an Nvidia A100 GPU, 
translating the complete Abhidhamma would take approximately 20-30 hours 
(~1,100 files, ~80,000+ segments). The script saves progress incrementally, 
so you can stop and resume anytime without losing work.

For comparison, a human expert would take approximately 20-25 years to translate the entire Abhidhamma.
Stock LLMs have not been trained on Pali, so they have around 60% accuracy on average.
gemma-2-mitra-it has 75% accuracy on Pali to English translation.

You can also translate any other part of the Pali Canon (Suttas, Vinaya, etc.) 
using the same approach.

================================================================================

USAGE:
------
# Translate entire Pali Canon (uses defaults: root/pli/ms → translation/en/llm)
python3 translate_with_llm.py --all

# Translate entire Abhidhamma Piṭaka (all 7 books)
python3 translate_with_llm.py --uid abhidhamma

# Translate single book (e.g., Dhammasaṅgaṇī)
python3 translate_with_llm.py --uid ds

# Translate specific files
python3 translate_with_llm.py --uids ds1.1,ds1.2,ds1.3

# Translate from custom directory
python3 translate_with_llm.py --source-dir root/pli/ms/sutta --uid dn --all

# Translate a single file
python3 translate_with_llm.py source.json target.json

# Faster translation (0.5s delay between calls)
python3 translate_with_llm.py --uid ds --delay 0.5

# Re-translate existing files (overwrite)
python3 translate_with_llm.py --uid ds --overwrite

HOW IT WORKS:
-------------
1. Finds source files in root/pli/ms (or custom directory)
2. Intelligently handles partial translations:
   - Skips fully translated files
   - Resumes partially translated files (even mid-file!)
   - Use --overwrite to force re-translation
3. Translates segments via LLM API
4. Saves incrementally after each segment (crash-safe!)
5. Saves to translation/en/llm with EXACT same structure and filenames
6. Creates directories/files on-demand (no empty files!)

TO CUSTOMIZE:
-------------
Edit the CONFIGURATION section below to adjust:
- Endpoint URL (for your own HuggingFace endpoint)
- Translation quality parameters (temperature, max tokens, etc.)
- Rate limiting (delay between API calls)

SETUP:
------
1. Install dependencies:
   pip install requests python-dotenv

2. Create .env file in repository root with:
   HUGGINGFACE_ACCESS_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx
   ENDPOINT_URL=https://your-endpoint-url.us-east-1.aws.endpoints.huggingface.cloud
   
   Get token from: https://huggingface.co/settings/tokens

3. Set up dedicated HuggingFace Inference Endpoint:
   - Model: buddhist-nlp/gemma-2-mitra-it
   - Hardware: AWS GPU (Nvidia A100 or similar recommended)
   - Runtime: vLLM
   - Copy your endpoint URL to ENDPOINT_URL in .env file
   
   Alternative: Use --use-api flag for public API (slower, rate-limited)


================================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================

import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================

# --- REQUIRED ---
DEFAULT_ENDPOINT = os.getenv('ENDPOINT_URL')
ACCESS_TOKEN = os.getenv('HUGGINGFACE_ACCESS_TOKEN')

# Validate required environment variables
if not ACCESS_TOKEN:
    print("ERROR: HUGGINGFACE_ACCESS_TOKEN not found in environment variables.", file=sys.stderr)
    print("Please create a .env file in the repository root with:", file=sys.stderr)
    print("  HUGGINGFACE_ACCESS_TOKEN=hf_xxxxxxxxxxxxx", file=sys.stderr)
    print("Get your token from: https://huggingface.co/settings/tokens", file=sys.stderr)
    sys.exit(1)

if not DEFAULT_ENDPOINT:
    print("ERROR: ENDPOINT_URL not found in environment variables.", file=sys.stderr)
    print("Please add to your .env file:", file=sys.stderr)
    print("  ENDPOINT_URL=https://your-endpoint.huggingface.cloud", file=sys.stderr)
    print("Or use --use-api flag to use the public API (slower, rate-limited)", file=sys.stderr)
    sys.exit(1)

# Edit these settings to customize the translation behavior

# --- Directory Configuration ---
# Set these to translate entire collections in batch mode
DEFAULT_SOURCE_DIR = "root/pli/ms"              # Source Pali texts directory
DEFAULT_TARGET_DIR = "translation/en/llm"       # Output English translations directory

# --- Endpoint Configuration ---
PUBLIC_API_URL = "https://api-inference.huggingface.co/models/buddhist-nlp/gemma-2-mitra-it"
MODEL_NAME = "buddhist-nlp/gemma-2-mitra-it"

# --- Translation Model Parameters ---
# These control the quality and style of translations
MAX_TOKENS = 150              # Maximum length of generated translation
TEMPERATURE = 0.5             # Creativity level (0.0=deterministic, 1.0=creative)
TOP_P = 0.9                   # Nucleus sampling threshold (lower=more focused)
REPETITION_PENALTY = 1.2      # Penalty for repeating tokens (higher=less repetition)

# --- Stop Sequences ---
# The model will stop generating when it encounters these
STOP_TOKENS = ["#", "\n\n", "Please translate"]

# --- Rate Limiting ---
DEFAULT_DELAY = 1.0           # Seconds to wait between API calls (avoid throttling)

# --- Model-Specific Formatting ---
# gemma-2-mitra-it requires special formatting for Pali translation
LINE_BREAK_TOKEN = " 🔽 "     # Replace \n with this in Pali text
PROMPT_TEMPLATE = "Please translate into English (capitalize the first word): {text} 🔽 Translation::"

# --- API Timeout ---
REQUEST_TIMEOUT = 30          # Seconds to wait for API response


# ============================================================================
# AUTHENTICATION
# ============================================================================

def get_api_token():
    """
    Retrieve HuggingFace API token from environment variables.
    
    Returns:
        str: The HuggingFace access token
        
    Raises:
        ValueError: If HUGGINGFACE_ACCESS_TOKEN is not found in .env file
    """
    if not ACCESS_TOKEN:
        raise ValueError(
            "HUGGINGFACE_ACCESS_TOKEN not found in .env file.\n"
            "Please create a .env file with your HuggingFace token:\n"
            "  HUGGINGFACE_ACCESS_TOKEN=hf_xxxxxxxxxxxxx\n"
            "Get your token from: https://huggingface.co/settings/tokens"
        )
    return ACCESS_TOKEN


# ============================================================================
# TRANSLATION FUNCTIONS
# ============================================================================

def translate_segment(api_token, endpoint_url, pali_text, segment_id, use_api=False):
    """
    Translate a single Pali text segment to English using LLM.
    
    This function handles the complete translation workflow:
    1. Formats the Pali text according to model requirements
    2. Constructs the API request with appropriate parameters
    3. Sends request to either dedicated endpoint or public API
    4. Parses and cleans the model's response
    5. Ensures proper capitalization
    
    Args:
        api_token (str): HuggingFace authentication token
        endpoint_url (str): URL of the dedicated HuggingFace endpoint
        pali_text (str): The Pali text to translate
        segment_id (str): Unique identifier for this segment (e.g., "ds1.1:0.1")
        use_api (bool): If True, use public Inference API; if False, use dedicated endpoint
        
    Returns:
        str: The English translation, properly capitalized and cleaned
        
    Model-Specific Formatting:
        The gemma-2-mitra-it model requires:
        - Line breaks replaced with '🔽' character
        - Template: "Please translate into English: <text> 🔽 Translation::"
        - Stop token: '#'
    """
    
    # --- Step 1: Format input text ---
    # Replace line breaks with special token as required by gemma-2-mitra-it model
    pali_text_formatted = pali_text.replace('\n', LINE_BREAK_TOKEN)
    
    # Construct prompt using model's instruction template
    # The model is fine-tuned to recognize this specific format
    prompt = PROMPT_TEMPLATE.format(text=pali_text_formatted)
    
    # --- Step 2: Prepare HTTP request ---
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # --- Step 3: Configure endpoint and payload ---
    if use_api:
        # Option A: Use public HuggingFace Inference API
        # Slower, rate-limited, but no endpoint costs
        url = PUBLIC_API_URL
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": MAX_TOKENS,      # Maximum length of translation
                "temperature": TEMPERATURE,         # Creativity (0=deterministic, 1=creative)
                "top_p": TOP_P,                     # Nucleus sampling threshold
                "repetition_penalty": REPETITION_PENALTY,  # Penalize repetition
                "do_sample": True,                  # Enable sampling
                "return_full_text": False           # Return only generated text
            }
        }
    else:
        # Option B: Use dedicated HuggingFace endpoint
        # Faster, consistent, but requires paid endpoint
        base_url = endpoint_url.rstrip('/')
        url = f"{base_url}/v1/completions"  # OpenAI-compatible API
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "stop": STOP_TOKENS  # Stop generation at these tokens
        }
    
    # --- Step 4: Send request and handle response ---
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        result = response.json()
        
        # Parse response based on API format
        if use_api:
            # HuggingFace Inference API returns different format
            if isinstance(result, list) and len(result) > 0:
                translation = result[0].get('generated_text', '')
            elif isinstance(result, dict):
                translation = result.get('generated_text', '')
            else:
                translation = str(result)
        else:
            # OpenAI-compatible completions format
            if 'choices' in result and len(result['choices']) > 0:
                translation = result['choices'][0].get('text', '')
            else:
                translation = str(result)
        
        # --- Step 5: Clean up the translation ---
        translation = translation.strip()
        
        # Remove common prefixes that model might include
        if translation.startswith("Translation::"):
            translation = translation[13:].strip()
        if translation.startswith("English:"):
            translation = translation[8:].strip()
        
        # Stop at model's stop token or common delimiters
        cleanup_stops = STOP_TOKENS + ["🔽 🔽"]  # Add line break token duplicates
        for stop in cleanup_stops:
            if stop in translation:
                translation = translation.split(stop)[0].strip()
        
        # Remove any remaining line break tokens (single instances)
        translation = translation.replace("🔽", "").strip()
        
        # Ensure first letter is capitalized for consistency with bilara-data style
        if translation and len(translation) > 0:
            translation = translation[0].upper() + translation[1:]
        
        return translation
        
    except Exception as e:
        # Log error but don't crash - allows script to continue with other segments
        print(f"Error translating segment {segment_id}: {e}", file=sys.stderr)
        return ""


def translate_file(source_path, target_path, endpoint_url, delay=1.0, use_api=False):
    """
    Translate an entire JSON file of Pali segments to English.
    
    This function orchestrates the translation of a complete bilara-data file:
    - Reads source Pali JSON file
    - Translates each segment using the LLM
    - Saves incrementally after each translation (resume on interruption)
    - Intelligently handles partial translations (resumes mid-file)
    - Skips segments that are already translated
    - Applies rate limiting between API calls
    
    Args:
        source_path (Path): Path to source Pali JSON file
        target_path (Path): Path to output English JSON file
        endpoint_url (str): URL of HuggingFace endpoint
        delay (float): Seconds to wait between API calls (default: 1.0)
        use_api (bool): If True, use public API instead of dedicated endpoint
        
    Returns:
        dict: Complete translations dictionary {segment_id: translation}
        
    File Structure:
        Input:  {"ds1.1:0.1": "Dhammasaṅgaṇī", "ds1.1:0.2": "Tikamātikā", ...}
        Output: {"ds1.1:0.1": "Compendium of Dharma", "ds1.1:0.2": "Matrix of Triads", ...}
    """
    
    print(f"Reading source: {source_path}")
    
    # --- Step 1: Load source Pali text ---
    with open(source_path, 'r', encoding='utf-8') as f:
        pali_data = json.load(f)
    
    # --- Step 2: Load existing translations (if resuming) ---
    if target_path.exists():
        with open(target_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
    else:
        translations = {}
    
    # --- Step 3: Identify segments that need translation ---
    segments_to_translate = []
    for segment_id, pali_text in pali_data.items():
        # Skip if already translated and not empty
        if segment_id in translations and translations[segment_id] and translations[segment_id].strip():
            continue
        segments_to_translate.append((segment_id, pali_text))
    
    # --- Step 4: Check if there's work to do ---
    total = len(pali_data)
    remaining = len(segments_to_translate)
    completed = total - remaining
    
    if remaining == 0:
        print(f"✓ All {total} segments already translated!")
        return translations
    
    if completed > 0:
        print(f"Found partial translation: {completed}/{total} segments already done")
        print(f"Resuming translation of remaining {remaining} segments...")
    else:
        print(f"Translating {total} segments...")
    
    # --- Step 5: Get API authentication ---
    api_token = get_api_token()
    
    if use_api:
        print(f"Using HuggingFace Inference API")
    else:
        print(f"Using endpoint: {endpoint_url}")
    
    # --- Step 6: Translate remaining segments ---
    for i, (segment_id, pali_text) in enumerate(segments_to_translate, 1):
        # Display progress
        print(f"[{i}/{remaining}] Translating {segment_id}: {pali_text[:50]}...")
        
        # Translate the segment
        translation = translate_segment(api_token, endpoint_url, pali_text, segment_id, use_api)
        translations[segment_id] = translation
        
        # Save after each translation (prevents data loss on interruption)
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)
        
        # Display result preview
        print(f"           → {translation[:80]}...")
        
        # Rate limiting: wait between API calls to avoid throttling
        if i < remaining:
            time.sleep(delay)
    
    print(f"\n✓ Translation complete! Saved to: {target_path}")
    return translations


# ============================================================================
# BATCH PROCESSING
# ============================================================================

def translate_batch(source_dir, target_dir, uid, uids, endpoint_url, delay=1.0, use_api=False, overwrite=False):
    """
    Translate multiple files based on UID pattern.
    
    Mirrors exact directory structure and filenames from source to target.
    Creates target files and directories on-demand as translations complete.
    By default, skips files that already have translations.
    
    Args:
        source_dir (Path): Source directory (e.g., root/pli/ms)
        target_dir (Path): Target directory (e.g., translation/en/llm)
        uid (str): Single UID to translate (e.g., 'ds' for all Dhammasaṅgaṇī, or None for all)
        uids (list): List of specific UIDs to translate (e.g., ['ds1.1', 'ds1.2'])
        endpoint_url (str): HuggingFace endpoint URL
        delay (float): Delay between API calls
        use_api (bool): Use public API instead of endpoint
        overwrite (bool): If True, re-translate even if target file exists (default: False)
    """
    
    # --- Find source files based on UID pattern ---
    source_files = []
    
    if uid:
        # Find all files under the UID subdirectory
        matches = list(source_dir.glob(f'**/{uid}'))
        if matches:
            if len(matches) != 1:
                print(f"Warning: Multiple matches for UID '{uid}', using first match", file=sys.stderr)
            source_files.extend(matches[0].glob('**/*.json'))
    elif uids:
        # Find specific files matching the UID list
        for file in source_dir.glob('**/*.json'):
            file_uid = file.stem.split('_')[0]
            if file_uid in uids:
                source_files.append(file)
    else:
        # No UID specified - translate ALL files in source directory
        source_files.extend(source_dir.glob('**/*.json'))
    
    if not source_files:
        print(f"Error: No source files found for UID pattern", file=sys.stderr)
        sys.exit(1)
    
    # --- Translate each file ---
    total_files = len(source_files)
    print(f"\n{'='*80}")
    print(f"BATCH TRANSLATION: {total_files} files")
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    print(f"{'='*80}\n")
    
    for i, source_file in enumerate(sorted(source_files), 1):
        # Mirror exact directory structure and filename
        relative_path = source_file.relative_to(source_dir)
        target_file = target_dir / relative_path
        
        # Check if file is fully translated (unless overwrite flag is set)
        if not overwrite and target_file.exists():
            # Load both source and target to check completion
            with open(source_file, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
            with open(target_file, 'r', encoding='utf-8') as f:
                target_data = json.load(f)
            
            # Check if all segments are translated
            all_translated = True
            for segment_id in source_data.keys():
                if segment_id not in target_data or not target_data[segment_id] or not target_data[segment_id].strip():
                    all_translated = False
                    break
            
            if all_translated:
                print(f"[{i}/{total_files}] ✅ Skipping {relative_path} (fully translated, use --overwrite to re-translate)")
                continue
            else:
                # Partial translation detected - will resume
                partial_count = sum(1 for sid in source_data.keys() 
                                  if sid in target_data and target_data[sid] and target_data[sid].strip())
                print(f"\n{'─'*80}")
                print(f"[{i}/{total_files}] 🔄 {relative_path}")
                print(f"           Resuming partial translation ({partial_count}/{len(source_data)} segments done)")
                print(f"{'─'*80}")
        else:
            print(f"\n{'─'*80}")
            print(f"[{i}/{total_files}] 📄 {relative_path}")
            if overwrite and target_file.exists():
                print(f"           🔄 Overwriting existing translation")
            print(f"{'─'*80}")
        
        # Create target directory if needed
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Translate the file (handles partial translations intelligently)
        try:
            translate_file(source_file, target_file, endpoint_url, delay, use_api)
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Translation interrupted by user")
            print(f"Progress saved. Run again to resume from file {i}/{total_files}")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error translating {source_file.name}: {e}", file=sys.stderr)
            continue
    
    print(f"\n{'='*80}")
    print(f"✅ BATCH COMPLETE: Translated {total_files} files")
    print(f"{'='*80}\n")


# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    # --- Parse command-line arguments ---
    parser = argparse.ArgumentParser(
        description='Translate Pali texts to English using Buddhist NLP LLM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Translate entire Pali Canon (root/pli/ms → translation/en/llm)
  %(prog)s --all
  
  # Translate entire Abhidhamma Piṭaka (all 7 books)
  %(prog)s --uid abhidhamma
  
  # Translate single book (e.g., Dhammasaṅgaṇī)
  %(prog)s --uid ds
  
  # Re-translate existing files (overwrite)
  %(prog)s --uid ds --overwrite
  
  # Translate specific files
  %(prog)s --uids ds1.1,ds1.2,dn1
  
  # Translate a single file
  %(prog)s source.json target.json

Smart Resume: Automatically handles partial translations
  - Fully translated files: Skipped (✅)
  - Partially translated files: Resumes mid-file (🔄)
  - Use --overwrite to force re-translation from scratch

Output structure mirrors input exactly:
  root/pli/ms/abhidhamma/ds/ds1/ds1.1_root-pli-ms.json
  → translation/en/llm/abhidhamma/ds/ds1/ds1.1_root-pli-ms.json

For more information, see the script header documentation.
        """
    )
    
    # Single file mode arguments
    parser.add_argument('source', nargs='?',
                       help='Path to source Pali JSON file (single file mode)')
    parser.add_argument('target', nargs='?',
                       help='Path to output English JSON file (single file mode)')
    
    # Batch mode arguments
    parser.add_argument('--source-dir', type=str, default=DEFAULT_SOURCE_DIR,
                       help=f'Source directory for batch mode (default: {DEFAULT_SOURCE_DIR})')
    parser.add_argument('--target-dir', type=str, default=DEFAULT_TARGET_DIR,
                       help=f'Target directory for batch mode (default: {DEFAULT_TARGET_DIR})')
    
    uid_group = parser.add_mutually_exclusive_group()
    uid_group.add_argument('--uid', type=str,
                          help='UID of division to translate (e.g., ds for all Dhammasaṅgaṇī, or omit for entire Pali Canon)')
    uid_group.add_argument('--uids', type=str,
                          help='Comma-separated UIDs to translate (e.g., ds1.1,ds1.2,ds1.3)')
    
    parser.add_argument('--all', action='store_true',
                       help='Translate ALL files in source directory (entire Pali Canon)')
    
    # Common arguments
    parser.add_argument('--endpoint', 
                       default=DEFAULT_ENDPOINT,
                       help=f'HuggingFace endpoint URL (default: {MODEL_NAME} endpoint)')
    parser.add_argument('--use-api', 
                       action='store_true',
                       help='Use public HuggingFace Inference API instead of dedicated endpoint')
    parser.add_argument('--delay', 
                       type=float, 
                       default=DEFAULT_DELAY, 
                       help=f'Delay in seconds between API calls (default: {DEFAULT_DELAY})')
    parser.add_argument('--overwrite', 
                       action='store_true',
                       help='Re-translate files even if they already exist (default: skip existing)')
    
    args = parser.parse_args()
    
    # --- Determine mode: single file or batch ---
    batch_mode = bool(args.uid or args.uids or args.all)
    single_mode = bool(args.source and args.target)
    
    if batch_mode and single_mode:
        print("Error: Cannot use both single file and batch mode arguments", file=sys.stderr)
        sys.exit(1)
    
    if not batch_mode and not single_mode:
        print("Error: Must provide either SOURCE/TARGET files or --uid/--uids/--all for batch mode", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    # --- Run in appropriate mode ---
    if batch_mode:
        source_dir = Path(args.source_dir)
        target_dir = Path(args.target_dir)
        
        if not source_dir.exists():
            print(f"Error: Source directory not found: {source_dir}", file=sys.stderr)
            sys.exit(1)
        
        # Determine UID pattern
        uid = args.uid if not args.all else None
        uids_list = args.uids.split(',') if args.uids else None
        
        translate_batch(source_dir, target_dir, uid, uids_list, 
                       args.endpoint, args.delay, args.use_api, args.overwrite)
    else:
        # Single file mode
        source_path = Path(args.source)
        target_path = Path(args.target)
        
        if not source_path.exists():
            print(f"Error: Source file not found: {source_path}", file=sys.stderr)
            sys.exit(1)
        
        # Create target directory if it doesn't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run translation
        translate_file(source_path, target_path, args.endpoint, delay=args.delay, use_api=args.use_api)
