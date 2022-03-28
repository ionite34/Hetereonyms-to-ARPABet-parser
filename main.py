isDev = setupData["isDev"]

if not isDev:
    import sys
    sys.path.append("./resources/app")

#import plugins.hetereonyms_to_arpabet.g2p_h as G2p
from plugins.hetereonyms_to_arpabet.g2p_h import G2p

logger = setupData["logger"]

def het_to_arpabet(data=None):
    global logger
    global G2p

    # Detect if the model type supports ARPABet, model type has to be FastPitch1.1 or above
    # Parse the "modelType" of the "data" and parse string
    modelType = data["modelType"]
    # Confirm model type contains FastPitch
    if "FastPitch" in modelType:
        # Get the version number after "FastPitch"
        modelType_version = modelType.split("FastPitch")[1]
        # Parse the version number
        modelType_version = modelType_version.split(".")[0]
        # First verison digit has to be 1 or above, second digit has to be 1 or above
        if not int(modelType_version[0]) >= 1 and int(modelType_version[1]) >= 1:
            # Or first version digit has to be 2 or above with no further requirements
            if not int(modelType_version[0]) >= 2:
                # otherwise, exit early
                return
    
    logger.log(f'original_text: {data["sequence"]}')

    # Convert to ARPABet
    g2p = G2p()
    # Get converted string
    converted_string = g2p(data["sequence"])
    logger.log(f'converted_string: {converted_string}')
    # convert the converted_string array to a string and store
    converted_string_joined = "".join(converted_string)
    logger.log(f'converted_string_joined: {converted_string_joined}')
    # set to sequence
    data["sequence"] = converted_string_joined


def het_to_arpabet_batch(data=None):
    #wip
