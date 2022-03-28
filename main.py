# pre-imports
isDev = setupData["isDev"]

if not isDev:
    import sys
    sys.path.append("./resources/app")

# imports
from plugins.hetereonyms_to_arpabet.g2p_h import G2p
import time

logger = setupData["logger"]

def het_to_arpabet(data=None):
    global logger
    global G2p
    
    # Grab original text line
    text_line = data["sentence"]
    # Grab dictionary words about to be replaced downstream
    dict_to_replace = data["dict_words"]

    logger.log(f'original_line: {text_line}')
    logger.log(f'dict_to_replace: {dict_to_replace}')

    # Start timer
    start_time = time.time()
    # Convert to ARPABet
    g2p = G2p()
    # Get converted string
    converted_line = g2p(text_line)
    logger.log(f'converted_line: {converted_line}')
    # convert the converted_string list to a string and store
    converted_string_joined = ''.join(converted_line)
    logger.log(f'converted_string_joined: {converted_string_joined}')
    # modify the sentence
    data["sentence"] = converted_string_joined
