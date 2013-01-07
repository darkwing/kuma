import difflib
import re
import urllib

import constance.config
from jingo import register
import jinja2
from tidylib import tidy_document
from tower import ugettext as _

from sumo.urlresolvers import reverse
from wiki import DIFF_WRAP_COLUMN

import logging
from pyquery import PyQuery as pq


def compare_url(doc, from_id, to_id):
    return (reverse('wiki.compare_revisions', args=[doc.full_path],
                    locale=doc.locale)
            + '?' +
            urllib.urlencode({'from': from_id, 'to': to_id})
           )


def show_inline_diff(content_from, content_to):
    tidy_from, errors = _massage_diff_content(content_from)
    tidy_to, errors = _massage_diff_content(content_to)
    sm = difflib.SequenceMatcher(None, tidy_from, tidy_to)


def diff_rendered_table(content_from, content_to):
    table = diff_table(content_from, content_to, '', '')
    table = pq(table)

    rows = table.find('tbody tr')
    output = ''
    if len(rows):
        output = '<table border="1">'
        for row in rows:
            output += '<tr><td><p>%s</p></td><td><p>%s</p></td></tr>' % (pq(row).find('td').eq(2).html(), pq(row).find('td').eq(5).html())
        output+= '</table>'

    return jinja2.Markup(output)


def diff_rendered(content_from, content_to):
    """ blah """
    if content_from == content_to:
        return ''

    tidy_from, errors = _massage_diff_content(content_from)
    tidy_to, errors = _massage_diff_content(content_to)

    logging.debug('tidy_from: ' + tidy_from)
    logging.debug('tidy_to: ' + tidy_to)

    tidy_from = pq(tidy_from).find('body').html()
    tidy_to = pq(tidy_to).find('body').html()

    seqm = difflib.SequenceMatcher(None, tidy_from, tidy_to)
    full_output = []
    used_elements = []

    logging.debug('======================================')

    def apply_tag(seq_string, start, end, tag, opcode):
        #  Walk backward in the sequence to find a '<' or a '>'
        #  If a '<' is found before a '>', assume it's an in-tag change
        #       and move the tag before and after it
        #  If a '>' is found first, carry on per usual
        last_angle = ''
        start_down = start

        logging.debug('-------------------------------------------------')

        was = '<%s>%s</%s>' % (tag, seq_string[start:end], tag)
        #logging.debug('<' + opcode + '> Change without processing: ' + was)

        while start_down > 0:
            #logging.debug(str(start_down) + ' / ' + seq_string[start_down])
            if seq_string[start_down] == '>':
                last_angle = '>'
                break
            elif seq_string[start_down] == '<':
                last_angle = '<'
                break
            else:
                start_down = start_down - 1

        return_val = string = ''

        logging.debug('last_angle is: [' + last_angle + ']')
        if last_angle and last_angle != '>':  # attribute change
            
            #  Detect the tag type
            tag_type = seq_string[start_down+1:end].partition(' ')[0].replace('>', '').replace('<','')

            if tag_type != '/':
                #  Replace the "end" position with the end of the "</tag_type"
                end_split = seq_string[start_down+1:len(seq_string)].split('</' + tag_type)

                logging.debug(tag_type + ' :: end split is: ')
                logging.debug(end_split)

                if len(end_split):
                    end = start_down + 1 + len(end_split[0]) + 2 + len(tag_type) + 1

                if start_down in used_elements:
                    logging.debug('already used this element, not showing duplicate changes')
                    return ''
                used_elements.append(start_down)
                string = seq_string[start_down:end]

                logging.debug('in-tag/attribute change :: ' + string)
        else:
            string = seq_string[start:end]
            #logging.debug('simple change!')

        return_val = '<%s>%s</%s>' % (tag, string, tag)# if len(string.strip()) else ''
        #logging.debug('change with processing: ' + return_val)

        return return_val

    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            #full_output.append(seqm.a[a0:a1])
            logging.debug('')
        elif opcode == 'insert':
            #full_output.append('<ins>' + seqm.b[b0:b1] + '</ins>')
            full_output.append(apply_tag(seqm.b, b0, b1, 'ins', opcode))
        elif opcode == 'delete':
            #full_output.append('<del>' + seqm.a[a0:a1] + '</del>')
            full_output.append(apply_tag(seqm.a, a0, a1, 'del', opcode))
        elif opcode == 'replace':
            #full_output.append('<del>' + seqm.a[a0:a1] + '</del>')
            #full_output.append('<ins>' + seqm.b[b0:b1] + '</ins>')
            full_output.append(apply_tag(seqm.a, a0, a1, 'del', opcode))
            full_output.append(apply_tag(seqm.b, b0, b1, 'ins', opcode))
        else:
            raise RuntimeError('unexpected opcode')

    full_output = ''.join(full_output)

    return full_output


# http://stackoverflow.com/q/774316/571420
def show_diff(seqm):
    """Unify operations between two compared strings
seqm is a difflib.SequenceMatcher instance whose a & b are strings"""
    lines = constance.config.FEED_DIFF_CONTEXT_LINES
    full_output = []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            full_output.append(seqm.a[a0:a1])
        elif opcode == 'insert':
            full_output.append('<ins>' + seqm.b[b0:b1] + '</ins>')
        elif opcode == 'delete':
            full_output.append('<del>' + seqm.a[a0:a1] + '</del>')
        elif opcode == 'replace':
            full_output.append('&nbsp;<del>' + seqm.a[a0:a1] + '</del>&nbsp;')
            full_output.append('&nbsp;<ins>' + seqm.b[b0:b1] + '</ins>&nbsp;')
        else:
            raise RuntimeError('unexpected opcode')
    output = []
    whitespace_change = False
    for piece in full_output:
        if '<ins>' in piece or '<del>' in piece:
            # a change
            if re.match('<(ins|del)>\W+</(ins|del)>', piece):
                # the change is whitespace,
                # ignore it and remove preceding context
                output = output[:-lines]
                whitespace_change = True
                continue
            else:
                output.append(piece)
        else:
            context_lines = piece.splitlines()
            if output == []:
                # first context only shows preceding lines for next change
                context = ['<p>...</p>'] + context_lines[-lines:]
            elif whitespace_change:
                # context shows preceding lines for next change
                context = ['<p>...</p>'] + context_lines[-lines:]
                whitespace_change = False
            else:
                # context shows subsequent lines
                # and preceding lines for next change
                context = (context_lines[:lines]
                           + ['<p>...</p>']
                           + context_lines[-lines:])
            output = output + context
    # remove extra context from the very end, unless its the only context
    if len(output) > lines + 1:  # context lines and the change line
        output = output[:-lines]
    return ''.join(output)


def _massage_diff_content(content):
    tidy_options = {'output-xhtml': 0, 'force-output': 1}
    content = tidy_document(content, options=tidy_options)
    return content


@register.function
def diff_table(content_from, content_to, prev_id, curr_id):
    """Creates an HTML diff of the passed in content_from and content_to."""
    tidy_from, errors = _massage_diff_content(content_from)
    tidy_to, errors = _massage_diff_content(content_to)
    html_diff = difflib.HtmlDiff(wrapcolumn=False)
    from_lines = tidy_from.splitlines()
    to_lines = tidy_to.splitlines()
    try:
        diff = html_diff.make_table(from_lines, to_lines,
                                    _("Revision %s") % prev_id,
                                    _("Revision %s") % curr_id,
                                    context=True,
                                    numlines=constance.config.DIFF_CONTEXT_LINES
                                   )
    except RuntimeError:
        # some diffs hit a max recursion error
        message = _(u'There was an error generating the content.')
        diff = '<div class="warning"><p>%s</p></div>' % message
    return jinja2.Markup(diff)


@register.function
def diff_inline(content_from, content_to):
    tidy_from, errors = _massage_diff_content(content_from)
    tidy_to, errors = _massage_diff_content(content_to)
    sm = difflib.SequenceMatcher(None, tidy_from, tidy_to)
    diff = show_diff(sm)
    return jinja2.Markup(diff)


@register.function
def tag_diff_table(prev_tags, curr_tags, prev_id, curr_id):
    html_diff = difflib.HtmlDiff(wrapcolumn=DIFF_WRAP_COLUMN)
    prev_tag_lines = [prev_tags]
    curr_tag_lines = [curr_tags]

    diff = html_diff.make_table(prev_tag_lines, curr_tag_lines,
                                _("Revision %s") % prev_id,
                                _("Revision %s") % curr_id
                               )

    # Simple formatting update: 784877
    diff = diff.replace('",', '"<br />').replace('<td', '<td valign="top"')
    return jinja2.Markup(diff)


@register.function
def colorize_diff(diff):
    diff = diff.replace('<span class="diff_add"', '<span class="diff_add" '
                'style="background-color: #afa; text-decoration: none;"')
    diff = diff.replace('<span class="diff_sub"', '<span class="diff_sub" '
                'style="background-color: #faa; text-decoration: none;"')
    diff = diff.replace('<span class="diff_chg"', '<span class="diff_chg" '
                'style="background-color: #fe0; text-decoration: none;"')
    return diff
