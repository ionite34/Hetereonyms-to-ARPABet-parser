[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Hetereonyms-to-ARPABet-parser
Heteronym to ARPABet parser. Plugin for xVASynth.

This plugin is designed to convert detected Heteronyms from graphemes (spelling) to phonemes (pronunciation).

Hetreonyms are two or more words that are spelled identically but have different sounds and meanings.

Example of heteronyms:

* Did you want to read the book? I thought you read it already. (/rēd/ as present-tense vs. /red/ as past-tense)
* The soldier was to desert the army and venture into the desert. (/ˈdezərt/ as noun vs. /dəˈzərt/ as verb)

The conversion is handled by a deep learning seq2seq framework based on TensorFlow.

Words not matching the [preset list](g2p_h/heteronyms.en) of known heteronyms are not converted to phonemes.
This allows them to be handled by other dictionaries downstream or by models directly.

## References
* Based on my g2pH framework for grapheme to phoneme hetreonym processing https://github.com/ionite34/g2pH
* [Learning pronunciation from a foreign language in speech synthesis networks](https://arxiv.org/abs/1811.09364)
* Kyubyong Park & [Jongseok Kim](https://github.com/ozmig77)
