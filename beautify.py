#!/usr/bin/env python3
import re
import sys
import os
from collections import namedtuple
import argparse
from funcy import walk, drop, lpartition_by
from difflib import unified_diff
import jinja2

path_current_script = os.path.dirname(os.path.realpath(__file__))
templateLoader = jinja2.FileSystemLoader(searchpath=path_current_script)
templateEnv = jinja2.Environment(loader=templateLoader)


Correction = namedtuple('Correction', ['before', 'after', 'explantion'])

BOLD_SERIF = r'𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳'
BOLD_SANS = r'𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇'
ITALIC_SERIF = r'𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧'
ITALIC_SANS = r'𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻'
# strike = lambda x: x + '\u0338'

HTML_TEMPLATE = templateEnv.get_template('inlined_diff_html_template.j2')

def strike(text):
    res = ''
    do_not_strike = '., '
    for c in text:
        res += c
        if c not in do_not_strike:
            res += '\u0338'
    return res


def embolden(text):
    from_text = 'abcdefghijklmnopqrstuvwxyz'
    to_text = BOLD_SANS
    # return text.translate(''.maketrans(from_text, to_text))
    return '*' + text + '*'


def emphasize_msg(text):
    from_text = 'abcdefghijklmnopqrstuvwxyz'
    to_text = ITALIC_SERIF
    # return text.translate(''.maketrans(from_text, to_text))
    return '_' + text + '_'


def emphasize_HTML(text):
    return '<em>%s</em>' % text


def convert_diff_file_into_tuples(diff_file):
    res = []
    diffs = re.split('\n\n+', diff_file.read())
    for diff in diffs:
        lines = diff.split('\n')
        if len(lines) < 2:
            continue
        before = re.sub('^- *', '', lines[0])
        after = re.sub('^[+] *', '', lines[1])
        after = re.split(' *\(OR\) *', after)
        explantion = None
        if len(lines) > 2:
            explantion = lines[-1]
        res += [Correction(before, after, explantion)]
    return res


def correct_text_msg(from_text, to_text, insert_between=''):
    differences = unified_diff(from_text.split(), to_text.split())
    differences = drop(3, differences)
    differences = group_differences(differences)
    res = []
    for diff in differences:
        type_, text = diff[0], diff[1:]
        if type_ is '-':
            res += [walk(strike, text)]
            res += insert_between
        elif type_ is '+':
            res += [embolden(text)]
        else:
            res += [text]
    return ' '.join(res)


def correct_text_HTML(from_text, to_text, insert_between=''):
    differences = unified_diff(from_text.split(), to_text.split())
    differences = drop(3, differences)
    differences = group_differences(differences)
    res = []
    for diff in differences:
        type_, text = diff[0], diff[1:]
        if type_ is '-':
            res += ['<del>' + text + '</del>']
            res += insert_between
        elif type_ is '+':
            res += ['<ins>' + text + '</ins>']
        else:
            res += [text]
    return ' '.join(res)


def group_differences(differences, insert_between=' '):
    type_diff = lambda x: x[0]  # first letter -: del +: ins ...
    for grouped_diff in lpartition_by(type_diff, differences):
        res = grouped_diff[0]
        for rest in grouped_diff[1:]:
            res += insert_between + re.sub('^[-+]', '', rest)
        yield res


def beautify_correction_msg(correction):
    before, after, explanation = correction
    res = ''
    for after_text in after:
        if len(after) == 1:
            # insert_between = '->' #FIXME
            insert_between = ''  # FIXME
        else:
            insert_between = ''
        res += correct_text_msg(before, after_text, insert_between) + '\n'
    if explanation:
        res += emphasize_msg(explanation) + '\n'
    return res


def beautify_correction_HTML(correction):
    before, after, explanation = correction
    res = ''
    for after_text in after:
        if len(after) == 1:
            # insert_between = '->' #FIXME
            insert_between = ''  # FIXME
        else:
            insert_between = ''
        res += correct_text_HTML(before, after_text, insert_between) + '<br>'
    if explanation:
        res += emphasize_HTML(explanation) + '<br>'
    return res + '<br>'


def beautify_for_message(diff_file):
    corrections = convert_diff_file_into_tuples(diff_file)
    return '\n'.join(beautify_correction_msg(corr) for corr in corrections)


def beautify_for_HTML(diff_file):
    corrections = convert_diff_file_into_tuples(diff_file)
    res = '\n'.join(beautify_correction_HTML(corr) for corr in corrections)
    return HTML_TEMPLATE.render(body=res)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Beautify text corrections from a bare diff format')
    parser.add_argument('--to', default='message', type=str.lower,
                        choices=['html', 'message'], help='type of output format')
    parser.add_argument('diff_file', nargs='?', default='-', type=argparse.FileType('r'),
                        help='File containing corrections in diff format; Use `-` for stdin')
    parser.add_argument('outputfile', nargs='?', default='-', type=argparse.FileType(
        'w'), help='Output file: .html or .msg; Use `-` for stdout ')
    args = parser.parse_args()
    diff_file = args.diff_file
    outputfile = args.outputfile
    to = args.to
    if to == 'message':
        beautified = beautify_for_message(diff_file)
    else:
        beautified = beautify_for_HTML(diff_file)
    outputfile.write(beautified)
    outputfile.close()
    diff_file.close()

    # TODO: have this following functionality: ./beautify.py incorrect text -> correct text
