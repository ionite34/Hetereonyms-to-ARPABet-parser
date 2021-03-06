# pre-imports
import os
import sys
isDev = setupData["isDev"]

dir_path = os.path.dirname(os.path.realpath(__file__))
nltk_path = dir_path.replace(
    "\\", "/").split("/cpython")[0]+f'/plugins/hetereonyms_to_arpabet'
sys.path.append(nltk_path)

if isDev:
    sys.path.append("./plugins/hetereonyms_to_arpabet")
else:
    sys.path.append("./resources/app")

# imports
from plugins.hetereonyms_to_arpabet.g2p_h import G2p
import datetime
import re

logger = setupData["logger"]

def het_to_arpabet(data=None):
    global logger
    global G2p
    global datetime
    global re
    
    # Grab original text line
    text_line = data["sentence"]

    # Preprocessing

    # 1. Clear all double spaces and replace with single space
    text_line = re.sub(r'\s+', ' ', text_line)

    # Grab dictionary words about to be replaced downstream
    dict_to_replace = data["dict_words"]

    logger.log(f'original_line: <{text_line}>')
    #logger.log(f'dict_to_replace: {dict_to_replace}')

    # Start timer
    start_time = datetime.datetime.now()

    # Flag for if initialization happened during this run
    initialized_g2p = False
    # Check if G2p is started in cache, if not, create it
    if "context_cache" not in data.keys():
        data["context_cache"] = {}
        data["context_cache"]["g2p"] = G2p()
        initialized_g2p = True
    g2p = data["context_cache"]["g2p"]

    # Get replacements from g2p
    source_list = g2p.het_replace(text_line, True)
    originals, replacements, typeWord = source_list
    # Check if originals is not empty
    if len(originals)>0:
        logger.log(f'Originals: {originals}')
        logger.log(f'Replacements: {replacements}')
        logger.log(f'Heteronym types: {typeWord}')
        # Replace the original words in the text with the homograph phonemes
        for index, original_word in enumerate(originals):
            # If we detect the original_word in the dict_to_replace, skip this iteration
            if original_word in dict_to_replace:
                logger.log(f"[Caution](1/2): A word was skipped due to dictionary conflict: ['{original_word}']")
                logger.log(f"[Caution](2/2): Intended replacement: ['{original_word}']")
                continue
            logger.log(f'index: [{index}]')
            logger.log(f'original word: <{original_word}>')
            # build the rep lacement string
            # needs to be enclosed by curly brackets, and each phoneme is space separated
            replacement_string = '{' + ' '.join(replacements[index]) + '}'
            logger.log(f'replacement string: <{replacement_string}>')
            # match the original word as a whole word only using regex (\b) and replace
            # match any case of the original word
            # match only the first occurrence of the original word
            text_line = re.sub(r'\b' + original_word + r'\b', replacement_string, text_line, 1, flags=re.IGNORECASE)
        # Set the data to the new text line
        data["sentence"] = text_line
        # Log the new text line
        logger.log(f'Modified line: <{text_line}>')
    else:
        logger.log(f'No replacements found')
        
    # End timer
    end_time = datetime.datetime.now()
    # Report to log
    delta = end_time - start_time
    elapsed = "{:.2f}".format(delta.total_seconds() * 1000)
    if initialized_g2p:
        logger.log(f'Model initialization occured during this run, expect time taken to be longer.')
    logger.log(f'Time taken: {elapsed} ms')