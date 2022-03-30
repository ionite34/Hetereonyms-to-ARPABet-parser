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

    logger.log(f'original_line: <{text_line}>')
    logger.log(f'dict_to_replace: {dict_to_replace}')

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
        logger.log(f'originals: {originals}')
        logger.log(f'replacements: {replacements}')
        logger.log(f'Heteronym types: {typeWord}')
        # Replace the original words in the text with the homograph phonemes
        for index, original_word in enumerate(originals):
            # If we detect the original_word in the dict_to_replace, skip this iteration
            if original_word in dict_to_replace:
                logger.log(f"[Notice]: A word was skipped due to dictionary conflict: ['{original_word}']")
                continue
            logger.log(f'index: [{index}]')
            logger.log(f'original word: <{original_word}>')
            # build the rep lacement string
            # needs to be enclosed by curly brackets, and each phoneme is space separated
            replacement_string = '{' + ' '.join(replacements[index]) + '}'
            logger.log(f'replacement string: <{replacement_string}>')
            # match the original word as a whole word only using regex (\b) and replace
            # match any case of the original word
            text_line = re.sub(r'\b' + original_word + r'\b', replacement_string, text_line, flags=re.IGNORECASE)
        # Set the data to the new text line
        data["sentence"] = text_line
        # Log the new text line
        logger.log(f'Modified line: <{text_line}>')
    else:
        logger.log(f'No replacements found')

    # Find predicted word:
    if False:
        predicted_word_list = g2p.predict_text_line("misogyny")
        originals_t, replacements_t = predicted_word_list
        logger.log(f'Predicted word special: {replacements_t[0]}')

    # End timer
    end_time = datetime.datetime.now()
    # Report to log
    delta = end_time - start_time
    elapsed = "{:.2f}".format(delta.total_seconds() * 1000)
    if initialized_g2p:
        logger.log(f'Model initialization occured during this run, expect time taken to be longer.')
    logger.log(f'Time taken: {elapsed} ms')
