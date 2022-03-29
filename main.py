# pre-imports
isDev = setupData["isDev"]

if not isDev:
    import sys
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
    # Grab dictionary words about to be replaced downstream
    dict_to_replace = data["dict_words"]

    logger.log(f'original_line: {text_line}')
    logger.log(f'dict_to_replace: {dict_to_replace}')

    # Start timer
    start_time = datetime.datetime.now()

    # Starts G2p
    g2p = G2p()

    # Check if there is a heteronym in the text using the heteronyms.en dictionary in the g2p_h subfolder
    if g2p.contains_het(text_line):
        # If there is, get the replacement list of homographs and their phonemes
        source_list = g2p.het_replace(text_line)
        originals, replacements, typeWord = source_list
        logger.log(f'originals: {originals}')
        logger.log(f'replacements: {replacements}')
        logger.log(f'Heteronym types: {typeWord}')
        # Replace the original words in the text with the homograph phonemes
        for index, original_word in enumerate(originals):
            logger.log(f'index: [{index}]')
            logger.log(f'original word: <{original_word}>')
            # build the replacement string
            # needs to be enclosed by curly brackets, and each phoneme is space separated
            replacement_string = '{' + ' '.join(replacements[index]) + '}'
            logger.log(f'replacement string: <{replacement_string}>')
            # match the original word as a whole word only using regex (\b) and replace
            text_line = re.sub(r'\b' + original_word + r'\b', replacement_string, text_line, 1)
        # Add a space to the beginning and end of the text line
        text_line = '{ } ' + text_line + ' { }'
        # Set the data to the new text line
        data["sentence"] = text_line
        # Log the new text line
        logger.log(f'Modified line: {text_line}')

    # End timer
    end_time = datetime.datetime.now()
    # Report to log
    delta = end_time - start_time
    elapsed = "{:.2f}".format(delta.total_seconds() * 1000)
    logger.log(f'Time taken: {elapsed} ms')
