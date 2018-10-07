from difflib import unified_diff
from funcy import walk, drop

BOLD_SERIF =  '𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳'
BOLD_SANS = '𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇'
strike = lambda x: x + '\u0338'

def embolden(text):
    from_text = 'abcdefghijklmnopqrstuvwxyz'
    to_text = BOLD_SANS
    return text.translate(''.maketrans(from_text, to_text))




def correct_text(from_text, to_text):
    differences = unified_diff(from_text.split(), to_text.split())
    differences = drop(3, differences)
    res = []
    for diff in differences:
        type_, text = diff[0], diff[1:]
        if type_ is '-':
            res += [walk(strike, text)]
        elif type_ is '+':
            res += [embolden(text)]
        else:
            res += [text]
    return ' '.join(res)


if __name__ == "__main__":
    print(correct_text('bad text', 'correct text'))
